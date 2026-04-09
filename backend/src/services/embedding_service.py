"""Embedding service for generating and storing vector embeddings on Mind nodes.

This module implements the EmbeddingService class that generates vector embeddings
from Mind node text content using a configurable embedding provider (OpenAI-compatible),
stores them as node properties in Neo4j, and manages the vector index.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1**
"""

import logging
import math

import httpx
from neontology import GraphConnection

from ..config.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating vector embeddings and storing them on Mind nodes.

    Supports OpenAI-compatible embedding providers (OpenAI, LM-Studio, custom)
    via httpx. Embeddings are L2-normalized before storage. A Neo4j vector index
    is created on first use if it does not already exist.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1**
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize EmbeddingService with application settings.

        Args:
            settings: Application settings containing embedding provider config.
        """
        self.settings = settings
        self._index_ensured = False

    def _build_text(
        self, title: str, description: str | None, tags: list[str] | None
    ) -> str:
        """Concatenate node fields into a single string for embedding.

        Args:
            title: Node title (required).
            description: Optional node description.
            tags: Optional list of tags.

        Returns:
            Combined text string suitable for embedding.
        """
        parts = [title]
        if description:
            parts.append(description)
        if tags:
            parts.append("Tags: " + ", ".join(tags))
        return "\n".join(parts)

    def _normalize(self, vector: list[float]) -> list[float]:
        """L2-normalize a vector to unit length.

        Args:
            vector: Input float vector.

        Returns:
            Unit-length vector. Returns zero vector unchanged if magnitude is zero.
        """
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude == 0.0:
            return vector
        return [x / magnitude for x in vector]

    async def _ensure_vector_index(self) -> None:
        """Create the Neo4j vector index if it does not already exist.

        Uses CREATE VECTOR INDEX ... IF NOT EXISTS so it is safe to call
        multiple times. Only runs once per service lifetime (cached via flag).

        **Validates: Requirement 2.1**
        """
        if self._index_ensured:
            return

        gc = GraphConnection()
        dimensions = self.settings.embedding_dimensions

        # Neo4j 5.15+ vector index creation
        cypher = (
            "CREATE VECTOR INDEX mind_embedding_index IF NOT EXISTS "
            "FOR (m:Mind) ON (m.embedding) "
            "OPTIONS {indexConfig: {"
            "`vector.dimensions`: $dimensions, "
            "`vector.similarity_function`: 'cosine'"
            "}}"
        )

        try:
            gc.engine.evaluate_query(cypher, {"dimensions": dimensions})
            self._index_ensured = True
            logger.info(
                "Ensured vector index mind_embedding_index (dimensions=%d)",
                dimensions,
            )
        except Exception as e:
            logger.warning("Failed to create vector index: %s", e)

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text string.

        Calls the configured embedding provider API (OpenAI-compatible format)
        and returns the L2-normalized result vector.

        Args:
            text: Input text to embed.

        Returns:
            Normalized embedding vector of length ``embedding_dimensions``.

        Raises:
            RuntimeError: If the embedding provider is not configured or returns
                an invalid response.

        **Validates: Requirements 1.1, 1.4, 1.6**
        """
        results = await self.embed_texts([text])
        return results[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple texts via the embedding provider.

        Args:
            texts: List of input texts.

        Returns:
            List of normalized embedding vectors, one per input text.

        Raises:
            RuntimeError: If the provider is not configured or the response is
                invalid.

        **Validates: Requirements 1.1, 1.4, 1.6**
        """
        endpoint = self.settings.embedding_api_endpoint
        if not endpoint:
            raise RuntimeError("Embedding API endpoint is not configured")

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.settings.embedding_api_key:
            headers["Authorization"] = f"Bearer {self.settings.embedding_api_key}"

        payload: dict = {"input": texts, "model": self.settings.embedding_model_name or ""}

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{endpoint}/embeddings",
                    json=payload,
                    headers=headers,
                )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Embedding provider returned status {response.status_code}: "
                    f"{response.text[:200]}"
                )

            data = response.json()
            # OpenAI-compatible response: {"data": [{"embedding": [...], "index": 0}, ...]}
            items = sorted(data["data"], key=lambda d: d["index"])
            vectors = [self._normalize(item["embedding"]) for item in items]
            return vectors

        except httpx.HTTPError as exc:
            raise RuntimeError(f"Embedding provider request failed: {exc}") from exc

    async def embed_mind_node(self, node_uuid: str) -> None:
        """Fetch a Mind node by UUID, embed its text content, and store the embedding.

        Builds text from the node's title, description, and tags, generates an
        embedding, and writes it back as the ``embedding`` property on the node.

        Args:
            node_uuid: UUID of the Mind node to embed.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.5, 1.6**
        """
        await self._ensure_vector_index()

        gc = GraphConnection()

        # Fetch node properties
        fetch_cypher = (
            "MATCH (m) "
            "WHERE m.uuid = $uuid AND m.title IS NOT NULL "
            "RETURN m.title AS title, m.description AS description, m.tags AS tags"
        )

        try:
            results = gc.engine.evaluate_query(fetch_cypher, {"uuid": node_uuid})
        except Exception as e:
            logger.error("Failed to fetch node %s for embedding: %s", node_uuid, e)
            return

        if not results or not results.records_raw:
            logger.warning("Node %s not found for embedding", node_uuid)
            return

        record = results.records_raw[0]
        title = record["title"]
        description = record.get("description")
        tags = record.get("tags")

        if not title:
            logger.warning("Node %s has empty title, skipping embedding", node_uuid)
            return

        text = self._build_text(title, description, tags)

        try:
            embedding = await self.embed_text(text)
        except RuntimeError as e:
            logger.error("Failed to embed node %s: %s", node_uuid, e)
            return

        # Store embedding on the node
        store_cypher = (
            "MATCH (m) WHERE m.uuid = $uuid "
            "SET m.embedding = $embedding"
        )

        try:
            gc.engine.evaluate_query(
                store_cypher, {"uuid": node_uuid, "embedding": embedding}
            )
            logger.debug("Stored embedding for node %s", node_uuid)
        except Exception as e:
            logger.error("Failed to store embedding for node %s: %s", node_uuid, e)

    async def bulk_embed_unembedded(self, batch_size: int = 50) -> int:
        """Find all Mind nodes without embeddings and embed them in batches.

        Args:
            batch_size: Number of nodes to embed per batch.

        Returns:
            Total number of nodes that were successfully embedded.

        **Validates: Requirement 1.7**
        """
        await self._ensure_vector_index()

        gc = GraphConnection()

        # Query nodes that have a title but no embedding property
        query_cypher = (
            "MATCH (m) "
            "WHERE m.uuid IS NOT NULL AND m.title IS NOT NULL "
            "AND m.embedding IS NULL "
            "RETURN m.uuid AS uuid, m.title AS title, "
            "m.description AS description, m.tags AS tags"
        )

        try:
            results = gc.engine.evaluate_query(query_cypher, {})
        except Exception as e:
            logger.error("Failed to query un-embedded nodes: %s", e)
            return 0

        if not results or not results.records_raw:
            logger.info("No un-embedded nodes found")
            return 0

        records = list(results.records_raw)
        total = len(records)
        logger.info("Found %d un-embedded nodes, processing in batches of %d", total, batch_size)

        embedded_count = 0

        for i in range(0, total, batch_size):
            batch = records[i : i + batch_size]
            texts: list[str] = []
            uuids: list[str] = []

            for record in batch:
                title = record["title"]
                if not title:
                    continue
                description = record.get("description")
                tags = record.get("tags")
                texts.append(self._build_text(title, description, tags))
                uuids.append(record["uuid"])

            if not texts:
                continue

            try:
                embeddings = await self.embed_texts(texts)
            except RuntimeError as e:
                logger.error("Batch embedding failed at offset %d: %s", i, e)
                continue

            # Store embeddings for each node in the batch
            store_cypher = (
                "MATCH (m) WHERE m.uuid = $uuid "
                "SET m.embedding = $embedding"
            )

            for uuid, embedding in zip(uuids, embeddings):
                try:
                    gc.engine.evaluate_query(
                        store_cypher, {"uuid": uuid, "embedding": embedding}
                    )
                    embedded_count += 1
                except Exception as e:
                    logger.error("Failed to store embedding for node %s: %s", uuid, e)

            logger.info(
                "Embedded batch %d-%d (%d/%d)",
                i,
                min(i + batch_size, total),
                embedded_count,
                total,
            )

        logger.info("Bulk embedding complete: %d/%d nodes embedded", embedded_count, total)
        return embedded_count
