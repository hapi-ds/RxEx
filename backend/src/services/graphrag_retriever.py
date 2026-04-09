"""GraphRAG retriever service for semantic search and graph-aware context retrieval.

This module implements the GraphRAGRetriever class that combines vector similarity
search with graph traversal and community summaries to retrieve contextually
relevant subgraphs for AI prompts.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6, 6.2, 6.3**
"""

import logging
import math

from neontology import GraphConnection

from ..config.config import Settings
from ..schemas.graphrag import (
    CommunitySummary,
    RetrievalResult,
    SeedNode,
    SubgraphEdge,
    SubgraphNode,
)
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# Keywords that indicate a global/aggregation query
_GLOBAL_KEYWORDS: set[str] = {
    "overview",
    "summary",
    "all",
    "main",
    "overall",
    "general",
    "entire",
    "whole",
    "across",
}


class GraphRAGRetriever:
    """Retriever that combines vector similarity search with graph traversal.

    Supports three retrieval modes:
    - **local**: Semantic search + neighbor traversal for specific questions.
    - **global**: Community summaries for high-level/aggregation questions.
    - **hybrid**: Both local and global results combined.

    The ``auto`` mode classifies the query to pick local or global automatically.

    **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6, 6.2, 6.3**
    """

    def __init__(self, settings: Settings, embedding_service: EmbeddingService) -> None:
        """Initialize the retriever with application settings and embedding service.

        Args:
            settings: Application settings containing GraphRAG configuration.
            embedding_service: Service for generating query embeddings.
        """
        self.settings = settings
        self.embedding_service = embedding_service

    async def retrieve(self, query: str, mode: str = "auto") -> RetrievalResult:
        """Main retrieval entry point.

        Resolves the retrieval mode (if ``auto``, classifies the query), then
        delegates to the appropriate search strategy.

        Args:
            query: User query text.
            mode: Retrieval mode — ``"auto"``, ``"local"``, ``"global"``, or ``"hybrid"``.

        Returns:
            A ``RetrievalResult`` containing seed nodes, subgraph, community
            summaries, and the resolved mode.

        **Validates: Requirements 2.2, 2.3, 6.2, 6.3**
        """
        # Resolve mode
        resolved_mode = mode
        if resolved_mode == "auto":
            resolved_mode = self.classify_query(query)

        seed_nodes: list[SeedNode] = []
        subgraph_nodes: list[SubgraphNode] = []
        subgraph_edges: list[SubgraphEdge] = []
        community_summaries: list[CommunitySummary] = []

        # Local or hybrid: semantic search + traverse neighbors
        if resolved_mode in ("local", "hybrid"):
            query_embedding = await self.embedding_service.embed_text(query)
            seed_nodes = await self._semantic_search(
                query_embedding,
                top_k=self.settings.graphrag_top_k,
                threshold=self.settings.graphrag_similarity_threshold,
            )
            seed_uuids = [node.uuid for node in seed_nodes]
            if seed_uuids:
                subgraph_nodes, subgraph_edges = await self._traverse_neighbors(
                    seed_uuids,
                    depth=self.settings.graphrag_traversal_depth,
                    max_nodes=self.settings.graphrag_max_subgraph_nodes,
                )

        # Global or hybrid: community summaries
        if resolved_mode in ("global", "hybrid"):
            query_embedding_for_global = (
                query_embedding
                if resolved_mode == "hybrid"
                else await self.embedding_service.embed_text(query)
            )
            community_summaries = await self._get_community_summaries(
                query_embedding_for_global,
                limit=self.settings.graphrag_top_k,
            )

        return RetrievalResult(
            seed_nodes=seed_nodes,
            subgraph_nodes=subgraph_nodes,
            subgraph_edges=subgraph_edges,
            community_summaries=community_summaries,
            retrieval_mode=resolved_mode,
        )

    async def _semantic_search(
        self,
        query_embedding: list[float],
        top_k: int,
        threshold: float,
    ) -> list[SeedNode]:
        """Perform vector similarity search against the Neo4j vector index.

        Uses the ``mind_embedding_index`` to find the most semantically similar
        Mind nodes to the query embedding.

        Args:
            query_embedding: The embedding vector for the user query.
            top_k: Maximum number of results to return.
            threshold: Minimum cosine similarity score for inclusion.

        Returns:
            List of ``SeedNode`` objects sorted by descending similarity score.

        **Validates: Requirements 2.3, 2.4, 2.5**
        """
        gc = GraphConnection()

        cypher = (
            "CALL db.index.vector.queryNodes('mind_embedding_index', $top_k, $query_embedding) "
            "YIELD node, score "
            "WHERE score >= $threshold "
            "RETURN node.uuid AS uuid, node.title AS title, "
            "node.description AS description, labels(node)[0] AS mind_type, "
            "node.tags AS tags, score "
            "ORDER BY score DESC"
        )

        try:
            results = gc.engine.evaluate_query(
                cypher,
                {
                    "top_k": top_k,
                    "query_embedding": query_embedding,
                    "threshold": threshold,
                },
            )
        except Exception as e:
            logger.error("Semantic search failed: %s", e)
            return []

        if not results or not results.records_raw:
            return []

        seed_nodes: list[SeedNode] = []
        for record in results.records_raw:
            seed_nodes.append(
                SeedNode(
                    uuid=record["uuid"],
                    title=record["title"],
                    description=record.get("description"),
                    mind_type=record.get("mind_type", "Mind"),
                    tags=record.get("tags"),
                    score=record["score"],
                )
            )

        return seed_nodes

    async def _traverse_neighbors(
        self,
        seed_uuids: list[str],
        depth: int,
        max_nodes: int,
    ) -> tuple[list[SubgraphNode], list[SubgraphEdge]]:
        """Traverse graph neighbors from seed nodes via BFS.

        Uses variable-length path matching in Cypher to find neighbor nodes
        up to ``depth`` hops from the seed nodes. Deduplicates across multiple
        seed paths and respects the ``max_nodes`` limit. A second query fetches
        all relationships between the collected node set.

        Args:
            seed_uuids: UUIDs of seed nodes to traverse from.
            depth: Maximum traversal depth (hops).
            max_nodes: Maximum number of nodes in the subgraph.

        Returns:
            Tuple of (subgraph_nodes, subgraph_edges).

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
        """
        if not seed_uuids:
            return ([], [])

        gc = GraphConnection()

        # Cap neighbor count so seed + neighbors <= max_nodes
        neighbor_limit = max(0, max_nodes - len(seed_uuids))
        if neighbor_limit == 0:
            return ([], [])

        # --- Step 1: BFS to find unique neighbor nodes ---
        neighbor_cypher = (
            "MATCH path = (seed)-[*1..$depth]-(neighbor) "
            "WHERE seed.uuid IN $seed_uuids "
            "  AND neighbor.uuid IS NOT NULL "
            "  AND NOT neighbor.uuid IN $seed_uuids "
            "WITH DISTINCT neighbor, min(length(path)) AS min_depth "
            "ORDER BY min_depth "
            "LIMIT $neighbor_limit "
            "RETURN neighbor.uuid AS uuid, neighbor.title AS title, "
            "  labels(neighbor)[0] AS mind_type, neighbor.status AS status"
        )

        try:
            node_results = gc.engine.evaluate_query(
                neighbor_cypher,
                {
                    "depth": depth,
                    "seed_uuids": seed_uuids,
                    "neighbor_limit": neighbor_limit,
                },
            )
        except Exception as e:
            logger.error("Graph traversal (neighbor query) failed: %s", e)
            return ([], [])

        subgraph_nodes: list[SubgraphNode] = []
        neighbor_uuids: list[str] = []

        if node_results and node_results.records_raw:
            for record in node_results.records_raw:
                node_uuid = record["uuid"]
                neighbor_uuids.append(node_uuid)
                subgraph_nodes.append(
                    SubgraphNode(
                        uuid=node_uuid,
                        title=record.get("title", ""),
                        mind_type=record.get("mind_type", "Mind"),
                        status=record.get("status"),
                    )
                )

        if not neighbor_uuids:
            return ([], [])

        # --- Step 2: Fetch edges between all collected nodes ---
        all_uuids = seed_uuids + neighbor_uuids

        edge_cypher = (
            "MATCH (a)-[r]->(b) "
            "WHERE a.uuid IN $all_uuids AND b.uuid IN $all_uuids "
            "RETURN a.uuid AS source_uuid, b.uuid AS target_uuid, "
            "  type(r) AS relationship_type, "
            "  b.title AS target_title, labels(b)[0] AS target_type, "
            "  b.status AS target_status"
        )

        try:
            edge_results = gc.engine.evaluate_query(
                edge_cypher,
                {"all_uuids": all_uuids},
            )
        except Exception as e:
            logger.error("Graph traversal (edge query) failed: %s", e)
            return (subgraph_nodes, [])

        subgraph_edges: list[SubgraphEdge] = []
        seed_uuid_set = set(seed_uuids)

        if edge_results and edge_results.records_raw:
            for record in edge_results.records_raw:
                source_uuid = record["source_uuid"]
                target_uuid = record["target_uuid"]

                # Determine direction relative to the seed/traversal perspective:
                # "outgoing" if the source is a seed node, "incoming" otherwise
                if source_uuid in seed_uuid_set:
                    direction = "outgoing"
                else:
                    direction = "incoming"

                # Build connected node summary as "title (mind_type, status)"
                target_title = record.get("target_title", "")
                target_type = record.get("target_type", "Mind")
                target_status = record.get("target_status")
                if target_status:
                    connected_summary = f"{target_title} ({target_type}, {target_status})"
                else:
                    connected_summary = f"{target_title} ({target_type})"

                subgraph_edges.append(
                    SubgraphEdge(
                        relationship_type=record["relationship_type"],
                        direction=direction,
                        source_uuid=source_uuid,
                        target_uuid=target_uuid,
                        connected_node_summary=connected_summary,
                    )
                )

        return (subgraph_nodes, subgraph_edges)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Cosine similarity in [-1, 1], or 0.0 if either vector has zero magnitude.
        """
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def _get_community_summaries(
        self,
        query_embedding: list[float],
        limit: int,
    ) -> list[CommunitySummary]:
        """Fetch and rank community summaries by relevance to the query.

        Queries Neo4j for all CommunitySummary nodes, embeds each summary text,
        computes cosine similarity against the query embedding, and returns the
        top ``limit`` results sorted by descending relevance.

        Args:
            query_embedding: The embedding vector for the user query.
            limit: Maximum number of community summaries to return.

        Returns:
            List of ``CommunitySummary`` objects ranked by relevance score.

        **Validates: Requirements 4.6**
        """
        gc = GraphConnection()

        cypher = (
            "MATCH (cs:CommunitySummary) "
            "RETURN cs.community_id AS community_id, cs.summary AS summary, "
            "       cs.node_count AS node_count"
        )

        try:
            results = gc.engine.evaluate_query(cypher, {})
        except Exception as e:
            logger.error("Failed to fetch community summaries: %s", e)
            return []

        if not results or not results.records_raw:
            return []

        # Embed each summary and compute relevance against the query embedding
        summaries_with_scores: list[tuple[float, dict]] = []
        for record in results.records_raw:
            summary_text = record.get("summary")
            if not summary_text:
                continue

            try:
                summary_embedding = await self.embedding_service.embed_text(summary_text)
                score = self._cosine_similarity(query_embedding, summary_embedding)
            except Exception as e:
                logger.warning(
                    "Failed to embed summary for community %s: %s",
                    record.get("community_id"),
                    e,
                )
                score = 0.0

            summaries_with_scores.append((score, record))

        # Sort by relevance descending and take top `limit`
        summaries_with_scores.sort(key=lambda item: item[0], reverse=True)

        community_summaries: list[CommunitySummary] = []
        for score, record in summaries_with_scores[:limit]:
            community_summaries.append(
                CommunitySummary(
                    community_id=record["community_id"],
                    summary=record["summary"],
                    node_count=record.get("node_count", 0),
                    relevance_score=score,
                )
            )

        return community_summaries

    def classify_query(self, query: str) -> str:
        """Classify a query as local or global based on keyword analysis.

        Checks for the presence of aggregation keywords (e.g., "overview",
        "summary", "all", "main"). If any are found, the query is classified
        as ``"global"``; otherwise ``"local"``.

        Args:
            query: The user query text.

        Returns:
            ``"global"`` if aggregation keywords are present, ``"local"`` otherwise.

        **Validates: Requirements 6.2**
        """
        query_lower = query.lower()
        words = set(query_lower.split())
        if words & _GLOBAL_KEYWORDS:
            return "global"
        return "local"
