"""
Knowledge Store service for AI chat context generation.

This module implements the KnowledgeStore class that retrieves project context
from Neo4j for AI prompt generation. It handles schema information (relationship
types, node types) and risk data, with simple in-memory caching for schema data.
When GraphRAG is enabled, it integrates semantic search, graph traversal, and
community summaries into the context prompt.

**Validates: Requirements 2.1, 2.2, 2.3, 2.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.4**
"""

import logging
import time
from typing import Any, Optional

from neontology import GraphConnection

from ..config.config import Settings, settings
from ..schemas.graphrag import RetrievalResult
from ..services.embedding_service import EmbeddingService
from ..services.graphrag_retriever import GraphRAGRetriever

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """
    Service class for retrieving and formatting project context from Neo4j.

    This class implements context generation for AI chat by querying Neo4j for
    schema information (relationship types, node types) and risk data. It uses
    simple in-memory caching with timestamp-based TTL for schema data.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.6**
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Initialize KnowledgeStore with configurable cache TTL.

        Args:
            cache_ttl_seconds: Cache time-to-live in seconds (default 300 = 5 minutes)

        **Validates: Requirement 2.6**
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    def _get_cached(self, key: str) -> Optional[Any]:
        """
        Retrieve cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self.cache_ttl_seconds:
                return value
            # Cache expired, remove it
            del self._cache[key]
        return None

    def _set_cached(self, key: str, value: Any) -> None:
        """
        Store value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (time.time(), value)

    def invalidate_cache(self, key: str | None = None) -> None:
        """
        Invalidate cached data.

        Args:
            key: Specific cache key to invalidate, or None to clear all
        """
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    async def get_relationship_types(self) -> list[str]:
        """
        Retrieve all valid relationship types from Neo4j schema.

        This method queries Neo4j for all relationship types currently in use.
        Results are cached for cache_ttl_seconds to minimize database queries.

        Returns:
            List of relationship type names (e.g., ["CONTAINS", "DEPENDS_ON"])

        **Validates: Requirement 2.1**
        """
        # Check cache first
        cached = self._get_cached("relationship_types")
        if cached is not None:
            return cached

        logger.debug("Querying Neo4j for relationship types (cache miss)")
        gc = GraphConnection()

        cypher = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"

        try:
            results = gc.engine.evaluate_query(cypher, {})

            relationship_types = []
            if results and results.records_raw:
                for record in results.records_raw:
                    rel_type = record["relationshipType"]
                    relationship_types.append(rel_type)

            # Cache the results
            self._set_cached("relationship_types", relationship_types)

            return relationship_types

        except Exception as e:
            logger.warning(
                "get_relationship_types: failed to query relationship types: %s",
                e,
            )
            return []

    async def get_mind_node_types(self) -> list[str]:
        """
        Retrieve all Mind node types from Neo4j schema.

        This method queries Neo4j for all node labels currently in use.
        Results are cached for cache_ttl_seconds to minimize database queries.

        Returns:
            List of node type names (e.g., ["Project", "Task", "Risk"])

        **Validates: Requirement 2.2**
        """
        # Check cache first
        cached = self._get_cached("mind_node_types")
        if cached is not None:
            return cached

        logger.debug("Querying Neo4j for mind node types (cache miss)")
        gc = GraphConnection()

        cypher = "CALL db.labels() YIELD label RETURN label"

        try:
            results = gc.engine.evaluate_query(cypher, {})

            node_types = []
            if results and results.records_raw:
                for record in results.records_raw:
                    label = record["label"]
                    node_types.append(label)

            # Cache the results
            self._set_cached("mind_node_types", node_types)

            return node_types

        except Exception as e:
            logger.warning(
                "get_mind_node_types: failed to query node labels: %s",
                e,
            )
            return []

    async def get_risk_analyses(self) -> list[dict[str, Any]]:
        """
        Query and retrieve risk analyses from the graph database.

        This method queries Neo4j for all Risk nodes and returns their properties.
        Risk data is NOT cached since it changes more frequently than schema data.

        Returns:
            List of risk dictionaries with properties (title, severity, probability, etc.)

        **Validates: Requirement 2.3**
        """
        gc = GraphConnection()

        # Query for all Risk nodes, get latest version of each UUID
        cypher = """
        MATCH (r:Risk)
        WHERE NOT EXISTS((r)<-[:PREVIOUS]-())
        RETURN r.uuid as uuid, r.title as title, r.description as description,
               r.severity as severity, r.probability as probability,
               r.mitigation_plan as mitigation_plan, r.status as status
        ORDER BY r.title
        """

        try:
            results = gc.engine.evaluate_query(cypher, {})

            risks = []
            if results and results.records_raw:
                for record in results.records_raw:
                    risk = {
                        "uuid": str(record["uuid"]) if record["uuid"] else None,
                        "title": record["title"],
                        "description": record["description"],
                        "severity": record["severity"],
                        "probability": record["probability"],
                        "mitigation_plan": record["mitigation_plan"],
                        "status": record["status"],
                    }
                    risks.append(risk)

            return risks

        except Exception as e:
            logger.warning(
                "get_risk_analyses: failed to query risk nodes: %s",
                e,
            )
            return []

    def format_relationships(self, relationships: list[str]) -> str:
        """
        Format relationship types as structured text for prompt inclusion.

        Args:
            relationships: List of relationship type names

        Returns:
            Formatted string describing available relationship types

        **Validates: Requirement 2.4**
        """
        if not relationships:
            return "Available relationship types: None"

        return f"Available relationship types: {', '.join(relationships)}"

    async def get_mind_nodes(self) -> list[dict[str, str]]:
        """
        Retrieve existing Mind nodes (uuid, title, mind_type) from Neo4j.

        Results are cached for cache_ttl_seconds. Returns a compact list
        so the AI can reference nodes by UUID when creating relationships.

        Returns:
            List of dicts with keys: uuid, title, mind_type
        """
        cached = self._get_cached("mind_nodes")
        if cached is not None:
            return cached

        gc = GraphConnection()
        # Nodes don't have a mind_type property — the type is the Neo4j label.
        # Filter to nodes that have uuid + title (all Mind-derived nodes).
        # Exclude system labels like User, Poste, etc. by requiring version property.
        # Get only the latest version per uuid.
        cypher = (
            "MATCH (m) "
            "WHERE m.uuid IS NOT NULL AND m.title IS NOT NULL AND m.version IS NOT NULL "
            "WITH m.uuid AS uuid, m ORDER BY m.version DESC "
            "WITH uuid, collect(m)[0] AS latest "
            "RETURN uuid, latest.title AS title, labels(latest)[0] AS mind_type "
            "ORDER BY title LIMIT 200"
        )

        try:
            results = gc.engine.evaluate_query(cypher, {})
            nodes: list[dict[str, str]] = []
            if results and results.records_raw:
                for record in results.records_raw:
                    nodes.append(
                        {
                            "uuid": record["uuid"],
                            "title": record["title"],
                            "mind_type": record.get("mind_type", "unknown"),
                        }
                    )
            self._set_cached("mind_nodes", nodes)
            return nodes
        except Exception as e:
            logger.warning(
                "get_mind_nodes: failed to query mind nodes: %s",
                e,
            )
            return []

    def format_mind_nodes(self, nodes: list[dict[str, str]]) -> str:
        """
        Format existing Mind nodes as structured text for prompt inclusion.

        Args:
            nodes: List of node dicts with uuid, title, mind_type

        Returns:
            Formatted string listing existing nodes with UUIDs
        """
        if not nodes:
            return "Existing Mind nodes: None"

        lines = ["Existing Mind nodes:"]
        for node in nodes:
            lines.append(f'  - [{node["mind_type"]}] "{node["title"]}" (uuid: {node["uuid"]})')
        return "\n".join(lines)

    def format_risks(self, risks: list[dict[str, Any]]) -> str:
        """
        Format risk information as structured text for prompt inclusion.

        Args:
            risks: List of risk dictionaries with properties

        Returns:
            Formatted string describing risk analyses

        **Validates: Requirement 2.5**
        """
        if not risks:
            return "Risk Analyses: None"

        formatted_lines = ["Risk Analyses:"]
        for risk in risks:
            title = risk.get("title", "Untitled Risk")
            severity = risk.get("severity", "Unknown")
            probability = risk.get("probability", "Unknown")
            description = risk.get("description", "")
            mitigation = risk.get("mitigation_plan", "")

            formatted_lines.append(f"\n- {title}")
            formatted_lines.append(f"  Severity: {severity}, Probability: {probability}")
            if description:
                formatted_lines.append(f"  Description: {description}")
            if mitigation:
                formatted_lines.append(f"  Mitigation: {mitigation}")

        return "\n".join(formatted_lines)

    async def get_enabled_skills(self) -> list[dict[str, str]]:
        """Query all enabled Skill nodes from Neo4j.

        Skills are NOT cached — queried fresh each request so that
        toggling a skill takes effect on the next chat message.

        Returns:
            List of dicts with keys: name, content

        **Validates: Requirements 17.1, 17.2, 17.3, 17.4**
        """
        gc = GraphConnection()
        cypher = (
            "MATCH (s:Skill) WHERE s.enabled = true "
            "RETURN s.name AS name, s.content AS content "
            "ORDER BY s.name"
        )
        try:
            results = gc.engine.evaluate_query(cypher, {})
            skills: list[dict[str, str]] = []
            if results and results.records_raw:
                for record in results.records_raw:
                    skills.append(
                        {
                            "name": record["name"],
                            "content": record["content"],
                        }
                    )
            return skills
        except Exception as e:
            logger.warning(
                "get_enabled_skills: failed to query enabled skills: %s",
                e,
            )
            return []

    def format_skills(self, skills: list[dict[str, str]]) -> str:
        """Format enabled skills as structured text for prompt inclusion.

        Args:
            skills: List of skill dicts with name and content keys.

        Returns:
            Formatted string with '## AI Skills' heading and each skill's
            name as a sub-heading followed by its content. Returns empty
            string if no skills are provided.

        **Validates: Requirements 17.1, 17.2, 17.3, 17.4**
        """
        if not skills:
            return ""
        lines = ["## AI Skills", ""]
        for skill in skills:
            lines.append(f"### {skill['name']}")
            lines.append(skill["content"])
            lines.append("")
        return "\n".join(lines)

    def _estimate_token_count(self, text: str) -> int:
        """
        Estimate token count using word-based approximation (1 token ≈ 0.75 words).

        This is a simple approximation. More accurate tokenization would require
        provider-specific tokenizers (tiktoken for OpenAI, etc.).

        Args:
            text: Text to estimate token count for

        Returns:
            Estimated token count

        **Validates: Requirement 2.7**
        """
        # Split on whitespace to count words
        word_count = len(text.split())
        # 1 token ≈ 0.75 words, so word_count / 0.75 = token_count
        # Equivalent to word_count * (1 / 0.75) = word_count * 1.333...
        token_count = int(word_count / 0.75)
        return token_count

    def _format_retrieval_results(self, results: RetrievalResult) -> str:
        """Format GraphRAG retrieval results as structured text for prompt inclusion.

        Formats seed nodes, subgraph edges, and community summaries into
        readable sections with source attribution (node UUIDs and titles).

        Args:
            results: The retrieval result from GraphRAGRetriever.

        Returns:
            Formatted string containing all retrieval sections.

        **Validates: Requirements 5.1, 5.2, 5.6**
        """
        sections: list[str] = []

        # Format seed nodes (ordered by descending score from retriever)
        if results.seed_nodes:
            lines = ["## Relevant Nodes"]
            for node in results.seed_nodes:
                desc = f": {node.description}" if node.description else ""
                lines.append(
                    f"- [{node.uuid}] {node.title} "
                    f"({node.mind_type}, score: {node.score:.2f}){desc}"
                )
            sections.append("\n".join(lines))

        # Format subgraph edges
        if results.subgraph_edges:
            lines = ["## Related Nodes"]
            for edge in results.subgraph_edges:
                lines.append(
                    f"- {edge.source_uuid} --[{edge.relationship_type}]--> {edge.target_uuid}"
                )
            sections.append("\n".join(lines))

        # Format community summaries (ordered by descending relevance from retriever)
        if results.community_summaries:
            lines = ["## Community Insights"]
            for cs in results.community_summaries:
                lines.append(
                    f"Community {cs.community_id} ({cs.node_count} nodes): {cs.summary}"
                )
            sections.append("\n".join(lines))

        return "\n\n".join(sections)

    def _allocate_token_budget(self, mode: str, total_budget: int) -> tuple[int, int]:
        """Allocate token budget between local and global context.

        For hybrid mode, splits the budget 70% local / 30% global by default.
        For local mode, all budget goes to local. For global, all to global.

        Args:
            mode: Resolved retrieval mode (``"local"``, ``"global"``, or ``"hybrid"``).
            total_budget: Total tokens available for GraphRAG context.

        Returns:
            Tuple of (local_budget, global_budget).

        **Validates: Requirement 5.5**
        """
        if mode == "hybrid":
            return (int(total_budget * 0.7), int(total_budget * 0.3))
        if mode == "global":
            return (0, total_budget)
        # "local" or any other value
        return (total_budget, 0)

    async def generate_context_prompt(
        self, query: str | None = None, retrieval_mode: str = "auto"
    ) -> str:
        """Generate a Context_Prompt containing relevant project information.

        When ``graphrag_enabled`` is True and a ``query`` is provided, the prompt
        includes GraphRAG retrieval results (semantic search hits, graph traversal
        context, community summaries) alongside the existing schema information.
        When disabled or no query is given, behaviour is identical to the original
        implementation.

        Args:
            query: Optional user query for GraphRAG retrieval.
            retrieval_mode: Retrieval strategy — ``"auto"``, ``"local"``,
                ``"global"``, or ``"hybrid"``.

        Returns:
            Formatted context prompt string within token limit.

        **Validates: Requirements 2.7, 2.8, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.4**
        """
        # Retrieve all context data
        relationship_types = await self.get_relationship_types()
        node_types = await self.get_mind_node_types()
        risks = await self.get_risk_analyses()
        mind_nodes = await self.get_mind_nodes()
        skills = await self.get_enabled_skills()

        # Format each section
        relationships_text = self.format_relationships(relationship_types)
        node_types_text = (
            f"Available Mind node types: {', '.join(node_types)}"
            if node_types
            else "Available Mind node types: None"
        )
        risks_text = self.format_risks(risks)
        mind_nodes_text = self.format_mind_nodes(mind_nodes)
        skills_text = self.format_skills(skills)

        # --- GraphRAG retrieval (only when enabled + query provided) ---
        graphrag_text = ""
        if settings.graphrag_enabled and query:
            try:
                embedding_service = EmbeddingService(settings)
                retriever = GraphRAGRetriever(settings, embedding_service)
                retrieval_result = await retriever.retrieve(query, retrieval_mode)
                graphrag_text = self._format_retrieval_results(retrieval_result)
            except Exception as e:
                logger.warning("GraphRAG retrieval failed, falling back to base context: %s", e)

        # Combine into structured prompt
        sections = [
            "# Project Context",
            "",
            "You are an AI assistant for a Mind-based project management system.",
            "You have access to specialized AI skills that provide expert guidance and capabilities. When appropriate, leverage these skills by applying their methodology, templates, or expert knowledge to the user's request.",
            "When the user asks you to create a node, always use the exact mind_type from the available types listed below.",
            "Do NOT substitute one type for another (e.g., do not use 'resource' when the user asks for 'department').",
            "When creating relationships, look up the UUIDs from the 'Existing Nodes' section below. NEVER ask the user for UUIDs.",
            "If the user says 'connect all departments to the company', find all department nodes and the company node from the list below and create relationships using their UUIDs.",
            "If the user asks to create nodes AND connect them, create the nodes first. The user will confirm each node creation, and then you can create relationships using the new UUIDs.",
            "",
            "## Tool Execution Feedback",
            "Tool execution results are prefixed with `[Tool Result]` in the conversation.",
            "When you receive a `[Tool Result]` message, extract any UUIDs it contains and use them for subsequent operations (e.g., creating relationships between newly created nodes).",
            "After receiving a successful tool result, proceed to the next step immediately. Do not attempt to verify or test the result.",
            "Never ask the user for UUIDs. Always use UUIDs from `[Tool Result]` messages or from the Existing Nodes list below.",
            "",
            "## Graph Schema",
            relationships_text,
            node_types_text,
            "",
            "## Existing Nodes",
            mind_nodes_text,
            "",
            "## " + risks_text,
        ]

        # Append AI Skills section if any skills are enabled
        if skills_text:
            sections.append("")
            sections.append("## AI Skills")
            sections.append("")
            sections.append(skills_text)

        # Append GraphRAG section if results are non-empty
        if graphrag_text:
            sections.append("")
            sections.append("## Knowledge Base Context")
            sections.append("")
            sections.append(graphrag_text)

        full_prompt = "\n".join(sections)

        # Check token count and truncate if necessary
        token_count = self._estimate_token_count(full_prompt)
        max_tokens = settings.ai_max_context_tokens

        if token_count <= max_tokens:
            return full_prompt

        # If over limit, truncate lower-priority content.
        # Priority: schema > GraphRAG > skills > risks
        # Build base prompt without variable sections first.
        schema_sections = [
            "# Project Context",
            "",
            "## Graph Schema",
            relationships_text,
            node_types_text,
            "",
        ]
        if skills_text:
            schema_sections.append(skills_text)
            schema_sections.append("")

        schema_sections.append("## Risk Analyses")
        schema_text = "\n".join(schema_sections)
        schema_tokens = self._estimate_token_count(schema_text)

        # Calculate remaining tokens for risks + GraphRAG
        remaining_tokens = max_tokens - schema_tokens

        if remaining_tokens <= 0:
            # Schema alone exceeds limit, return just schema
            return schema_text + "\n(Risk data omitted due to token limit)"

        # If we have GraphRAG text, allocate budget between risks and GraphRAG
        if graphrag_text:
            graphrag_tokens = self._estimate_token_count(graphrag_text)
            # Give GraphRAG up to half the remaining budget, risks get the rest
            graphrag_budget = min(graphrag_tokens, remaining_tokens // 2)
            risk_budget = remaining_tokens - graphrag_budget

            # Truncate GraphRAG if needed
            if graphrag_tokens > graphrag_budget:
                truncation_suffix = "\n... (GraphRAG context truncated)"
                suffix_tokens = self._estimate_token_count(truncation_suffix)
                max_graphrag_words = int((graphrag_budget - suffix_tokens) * 0.75)
                graphrag_words = graphrag_text.split()
                if len(graphrag_words) > max_graphrag_words and max_graphrag_words > 0:
                    graphrag_text = " ".join(graphrag_words[:max_graphrag_words]) + truncation_suffix
                elif max_graphrag_words <= 0:
                    graphrag_text = ""
        else:
            risk_budget = remaining_tokens

        # Truncate risks to fit remaining tokens
        truncation_suffix = "... (truncated)"
        suffix_tokens = self._estimate_token_count(truncation_suffix)
        max_risk_words = int((risk_budget - suffix_tokens) * 0.75)
        risk_words = risks_text.split()

        if len(risk_words) <= max_risk_words:
            truncated_risks = risks_text
        else:
            truncated_risks = " ".join(risk_words[:max_risk_words]) + " " + truncation_suffix

        result = schema_text + "\n" + truncated_risks

        if graphrag_text:
            result += "\n\n## Knowledge Base Context\n\n" + graphrag_text

        return result
