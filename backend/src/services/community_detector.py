"""Community detection service for identifying clusters and generating summaries.

This module implements the CommunityDetector class that runs Label Propagation
community detection on the Mind graph using NetworkX, stores community assignments
on Mind nodes, and generates AI-powered natural language summaries per community.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.7**
"""

import asyncio
import logging

import httpx
import networkx as nx
from neontology import GraphConnection
from networkx.algorithms.community.label_propagation import label_propagation_communities

from ..config.config import Settings

logger = logging.getLogger(__name__)


class CommunityDetector:
    """Detects communities in the Mind graph and generates AI summaries.

    Uses NetworkX Label Propagation for community detection and an
    OpenAI-compatible AI provider for summary generation. An asyncio lock
    prevents concurrent detection runs.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.7**
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize CommunityDetector with application settings.

        Args:
            settings: Application settings containing AI provider and Neo4j config.
        """
        self.settings = settings
        self._lock = asyncio.Lock()

    async def detect_and_summarize(self) -> dict:
        """Run the full community detection and summarization pipeline.

        Acquires an in-memory lock to prevent concurrent runs. If the lock is
        already held, returns immediately with an ``already_in_progress`` status.

        Pipeline steps:
        1. Project the Mind graph into NetworkX.
        2. Run Label Propagation community detection.
        3. Store community assignments on Mind nodes.
        4. Generate AI summaries for communities with >= 2 nodes.

        Returns:
            Stats dict with keys: ``status``, ``community_count``,
            ``nodes_processed``, ``summaries_generated``.
        """
        if self._lock.locked():
            return {
                "status": "already_in_progress",
                "community_count": 0,
                "nodes_processed": 0,
                "summaries_generated": 0,
            }

        async with self._lock:
            logger.info("Starting community detection pipeline")

            # Step 1: Project graph
            graph = await self._project_graph()
            if graph.number_of_nodes() < 2:
                logger.info(
                    "Graph has fewer than 2 nodes (%d), skipping detection",
                    graph.number_of_nodes(),
                )
                return {
                    "status": "completed",
                    "community_count": 0,
                    "nodes_processed": graph.number_of_nodes(),
                    "summaries_generated": 0,
                }

            # Step 2: Detect communities
            assignments = self._detect_communities(graph)
            community_count = len(set(assignments.values()))
            logger.info(
                "Detected %d communities across %d nodes",
                community_count,
                len(assignments),
            )

            # Step 3: Store assignments
            await self._store_assignments(assignments)

            # Step 4: Generate summaries
            summaries_generated = await self._generate_summaries(assignments)

            logger.info(
                "Community detection complete: %d communities, %d summaries",
                community_count,
                summaries_generated,
            )

            return {
                "status": "completed",
                "community_count": community_count,
                "nodes_processed": len(assignments),
                "summaries_generated": summaries_generated,
            }

    async def _project_graph(self) -> nx.Graph:
        """Load Mind nodes and relationships from Neo4j into a NetworkX graph.

        Queries all nodes with uuid and title, then all directed relationships
        between them. Builds an undirected NetworkX graph with node attributes
        (title, description, mind_type).

        Returns:
            An undirected NetworkX graph representing the Mind graph.
        """
        gc = GraphConnection()
        graph = nx.Graph()

        # Fetch all nodes with uuid and title
        node_cypher = (
            "MATCH (m) WHERE m.uuid IS NOT NULL AND m.title IS NOT NULL "
            "RETURN m.uuid AS uuid, m.title AS title, "
            "m.description AS description, labels(m)[0] AS mind_type"
        )

        try:
            node_results = gc.engine.evaluate_query(node_cypher, {})
        except Exception as e:
            logger.error("Failed to fetch nodes for graph projection: %s", e)
            return graph

        if node_results and node_results.records_raw:
            for record in node_results.records_raw:
                graph.add_node(
                    record["uuid"],
                    title=record["title"],
                    description=record.get("description"),
                    mind_type=record.get("mind_type", "Mind"),
                )

        # Fetch all relationships between nodes
        rel_cypher = (
            "MATCH (a)-[r]->(b) WHERE a.uuid IS NOT NULL AND b.uuid IS NOT NULL "
            "RETURN a.uuid AS source, b.uuid AS target, type(r) AS rel_type"
        )

        try:
            rel_results = gc.engine.evaluate_query(rel_cypher, {})
        except Exception as e:
            logger.error("Failed to fetch relationships for graph projection: %s", e)
            return graph

        if rel_results and rel_results.records_raw:
            for record in rel_results.records_raw:
                source = record["source"]
                target = record["target"]
                # Only add edges between nodes that exist in the graph
                if graph.has_node(source) and graph.has_node(target):
                    graph.add_edge(source, target, rel_type=record["rel_type"])

        logger.info(
            "Projected graph: %d nodes, %d edges",
            graph.number_of_nodes(),
            graph.number_of_edges(),
        )
        return graph

    def _detect_communities(self, graph: nx.Graph) -> dict[str, int]:
        """Run Label Propagation community detection on the NetworkX graph.

        Args:
            graph: Undirected NetworkX graph of Mind nodes.

        Returns:
            Dictionary mapping node UUID to community ID (integer).
        """
        communities = label_propagation_communities(graph)

        assignments: dict[str, int] = {}
        for community_id, node_set in enumerate(communities):
            for node_uuid in node_set:
                assignments[node_uuid] = community_id

        return assignments

    async def _store_assignments(self, assignments: dict[str, int]) -> None:
        """Write community_id property to each Mind node in Neo4j.

        Uses UNWIND for batch efficiency to update all nodes in a single query.

        Args:
            assignments: Dictionary mapping node UUID to community ID.
        """
        if not assignments:
            return

        gc = GraphConnection()

        # Build list of {uuid, community_id} for UNWIND
        items = [
            {"uuid": uuid, "community_id": cid}
            for uuid, cid in assignments.items()
        ]

        store_cypher = (
            "UNWIND $items AS item "
            "MATCH (m) WHERE m.uuid = item.uuid "
            "SET m.community_id = item.community_id"
        )

        try:
            gc.engine.evaluate_query(store_cypher, {"items": items})
            logger.info("Stored community assignments for %d nodes", len(items))
        except Exception as e:
            logger.error("Failed to store community assignments: %s", e)

    async def _generate_summaries(self, assignments: dict[str, int]) -> int:
        """Generate AI summaries for each community with >= 2 nodes.

        For each qualifying community, fetches node titles and descriptions,
        calls the AI provider to generate a summary, and stores the result
        as a CommunitySummary node in Neo4j.

        Args:
            assignments: Dictionary mapping node UUID to community ID.

        Returns:
            Number of summaries successfully generated.
        """
        # Group nodes by community
        communities: dict[int, list[str]] = {}
        for uuid, cid in assignments.items():
            communities.setdefault(cid, []).append(uuid)

        gc = GraphConnection()
        summaries_generated = 0

        for community_id, node_uuids in communities.items():
            # Skip communities with fewer than 2 nodes (Requirement 4.7)
            if len(node_uuids) < 2:
                logger.debug(
                    "Skipping community %d with %d node(s)",
                    community_id,
                    len(node_uuids),
                )
                continue

            # Fetch node details for this community
            fetch_cypher = (
                "MATCH (m) WHERE m.uuid IN $uuids "
                "RETURN m.title AS title, m.description AS description"
            )

            try:
                results = gc.engine.evaluate_query(
                    fetch_cypher, {"uuids": node_uuids}
                )
            except Exception as e:
                logger.error(
                    "Failed to fetch nodes for community %d: %s", community_id, e
                )
                continue

            if not results or not results.records_raw:
                continue

            # Build node list for the prompt
            node_lines: list[str] = []
            for record in results.records_raw:
                title = record.get("title", "Untitled")
                description = record.get("description", "")
                if description:
                    node_lines.append(f"- {title}: {description}")
                else:
                    node_lines.append(f"- {title}")

            node_list = "\n".join(node_lines)
            prompt = (
                "Summarize the following group of related project nodes in "
                "2-3 sentences. Focus on what they have in common and their "
                f"collective purpose.\n\nNodes:\n{node_list}"
            )

            # Call AI provider for summary
            try:
                summary = await self._call_ai_for_summary(prompt)
            except Exception as e:
                logger.error(
                    "Failed to generate summary for community %d: %s",
                    community_id,
                    e,
                )
                continue

            if not summary:
                continue

            # Store summary as CommunitySummary node
            store_cypher = (
                "MERGE (cs:CommunitySummary {community_id: $community_id}) "
                "SET cs.summary = $summary, "
                "cs.node_count = $node_count, "
                "cs.updated_at = datetime()"
            )

            try:
                gc.engine.evaluate_query(
                    store_cypher,
                    {
                        "community_id": community_id,
                        "summary": summary,
                        "node_count": len(node_uuids),
                    },
                )
                summaries_generated += 1
                logger.debug(
                    "Stored summary for community %d (%d nodes)",
                    community_id,
                    len(node_uuids),
                )
            except Exception as e:
                logger.error(
                    "Failed to store summary for community %d: %s",
                    community_id,
                    e,
                )

        return summaries_generated

    async def _call_ai_for_summary(self, prompt: str) -> str:
        """Call the AI provider to generate a community summary.

        Uses the same AI provider configuration as AIChatService (OpenAI-compatible
        endpoint). Makes a non-streaming request for simplicity.

        Args:
            prompt: The summary generation prompt.

        Returns:
            Generated summary text, or empty string on failure.
        """
        endpoint = self.settings.ai_api_endpoint
        if not endpoint:
            logger.warning("AI API endpoint not configured, skipping summary generation")
            return ""

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.settings.ai_api_key:
            headers["Authorization"] = f"Bearer {self.settings.ai_api_key}"

        payload = {
            "model": self.settings.ai_model_name or "",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{endpoint}/chat/completions",
                    json=payload,
                    headers=headers,
                )

            if response.status_code != 200:
                logger.error(
                    "AI provider returned status %d for summary: %s",
                    response.status_code,
                    response.text[:200],
                )
                return ""

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return ""

            return choices[0].get("message", {}).get("content", "").strip()

        except httpx.HTTPError as exc:
            logger.error("AI provider request failed for summary: %s", exc)
            return ""
