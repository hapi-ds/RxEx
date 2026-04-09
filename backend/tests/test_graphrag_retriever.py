"""Unit tests for GraphRAGRetriever.

Tests classify_query logic and basic retriever construction. Semantic search
and retrieval tests that require Neo4j are covered by integration tests.
"""

import pytest

from src.config.config import Settings
from src.services.graphrag_retriever import GraphRAGRetriever


@pytest.fixture
def settings() -> Settings:
    """Create minimal settings for testing."""
    return Settings(
        embedding_provider="none",
        graphrag_enabled=True,
        graphrag_top_k=10,
        graphrag_similarity_threshold=0.7,
        graphrag_traversal_depth=2,
        graphrag_max_subgraph_nodes=50,
        graphrag_default_mode="auto",
    )


@pytest.fixture
def retriever(settings: Settings) -> GraphRAGRetriever:
    """Create a retriever with a mock embedding service (None for classify_query tests)."""
    # embedding_service is not needed for classify_query tests
    return GraphRAGRetriever(settings=settings, embedding_service=None)  # type: ignore[arg-type]


class TestClassifyQuery:
    """Tests for keyword-based query classification."""

    def test_global_with_overview(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Give me an overview of the project") == "global"

    def test_global_with_summary(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Provide a summary of risks") == "global"

    def test_global_with_all(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Show all tasks") == "global"

    def test_global_with_main(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("What are the main risk areas?") == "global"

    def test_global_with_overall(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("What is the overall status?") == "global"

    def test_global_with_general(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Give a general assessment") == "global"

    def test_global_with_entire(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Review the entire project") == "global"

    def test_global_with_whole(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Analyze the whole system") == "global"

    def test_global_with_across(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Issues across all teams") == "global"

    def test_local_specific_entity(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("What is the status of Task-42?") == "local"

    def test_local_no_keywords(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Tell me about the design phase") == "local"

    def test_global_case_insensitive(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Give me an OVERVIEW") == "global"

    def test_local_empty_query(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("") == "local"

    def test_global_keyword_in_mixed_case(self, retriever: GraphRAGRetriever) -> None:
        assert retriever.classify_query("Summary of Sprint 3") == "global"


class TestRetrieverInit:
    """Tests for retriever initialization."""

    def test_stores_settings(self, settings: Settings) -> None:
        retriever = GraphRAGRetriever(settings=settings, embedding_service=None)  # type: ignore[arg-type]
        assert retriever.settings is settings

    def test_stores_embedding_service(self, settings: Settings) -> None:
        mock_service = object()
        retriever = GraphRAGRetriever(settings=settings, embedding_service=mock_service)  # type: ignore[arg-type]
        assert retriever.embedding_service is mock_service

import math
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


class TestCosineSimilarity:
    """Tests for the _cosine_similarity static method."""

    def test_identical_vectors(self) -> None:
        vec = [1.0, 0.0, 0.0]
        assert GraphRAGRetriever._cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert GraphRAGRetriever._cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self) -> None:
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert GraphRAGRetriever._cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector_a(self) -> None:
        assert GraphRAGRetriever._cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    def test_zero_vector_b(self) -> None:
        assert GraphRAGRetriever._cosine_similarity([1.0, 1.0], [0.0, 0.0]) == 0.0

    def test_known_similarity(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        dot = 1 * 4 + 2 * 5 + 3 * 6  # 32
        norm_a = math.sqrt(1 + 4 + 9)  # sqrt(14)
        norm_b = math.sqrt(16 + 25 + 36)  # sqrt(77)
        expected = dot / (norm_a * norm_b)
        assert GraphRAGRetriever._cosine_similarity(a, b) == pytest.approx(expected)


class TestGetCommunitySummaries:
    """Tests for _get_community_summaries method."""

    @pytest.fixture
    def mock_embedding_service(self) -> AsyncMock:
        service = AsyncMock()
        # Return a simple normalized vector for any text
        service.embed_text = AsyncMock(return_value=[0.5, 0.5, 0.5, 0.5])
        return service

    @pytest.fixture
    def retriever_with_embed(
        self, settings: Settings, mock_embedding_service: AsyncMock
    ) -> GraphRAGRetriever:
        return GraphRAGRetriever(
            settings=settings, embedding_service=mock_embedding_service
        )

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_summaries(
        self, retriever_with_embed: GraphRAGRetriever
    ) -> None:
        mock_result = MagicMock()
        mock_result.records_raw = []

        with patch("src.services.graphrag_retriever.GraphConnection") as mock_gc_cls:
            mock_gc_cls.return_value.engine.evaluate_query.return_value = mock_result
            result = await retriever_with_embed._get_community_summaries(
                [0.1, 0.2, 0.3, 0.4], limit=5
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_query_failure(
        self, retriever_with_embed: GraphRAGRetriever
    ) -> None:
        with patch("src.services.graphrag_retriever.GraphConnection") as mock_gc_cls:
            mock_gc_cls.return_value.engine.evaluate_query.side_effect = RuntimeError(
                "connection failed"
            )
            result = await retriever_with_embed._get_community_summaries(
                [0.1, 0.2, 0.3, 0.4], limit=5
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_ranks_by_relevance_descending(
        self, retriever_with_embed: GraphRAGRetriever, mock_embedding_service: AsyncMock
    ) -> None:
        # Return different embeddings so cosine similarity varies
        mock_embedding_service.embed_text = AsyncMock(
            side_effect=[
                [0.1, 0.0, 0.0, 0.0],  # low similarity to query
                [0.9, 0.9, 0.9, 0.9],  # high similarity to query
            ]
        )

        mock_result = MagicMock()
        mock_result.records_raw = [
            {"community_id": 1, "summary": "Low relevance community", "node_count": 3},
            {"community_id": 2, "summary": "High relevance community", "node_count": 5},
        ]

        query_embedding = [1.0, 1.0, 1.0, 1.0]

        with patch("src.services.graphrag_retriever.GraphConnection") as mock_gc_cls:
            mock_gc_cls.return_value.engine.evaluate_query.return_value = mock_result
            result = await retriever_with_embed._get_community_summaries(
                query_embedding, limit=10
            )

        assert len(result) == 2
        # Higher relevance should come first
        assert result[0].community_id == 2
        assert result[1].community_id == 1
        assert result[0].relevance_score > result[1].relevance_score

    @pytest.mark.asyncio
    async def test_respects_limit(
        self, retriever_with_embed: GraphRAGRetriever
    ) -> None:
        mock_result = MagicMock()
        mock_result.records_raw = [
            {"community_id": i, "summary": f"Community {i}", "node_count": i + 1}
            for i in range(5)
        ]

        with patch("src.services.graphrag_retriever.GraphConnection") as mock_gc_cls:
            mock_gc_cls.return_value.engine.evaluate_query.return_value = mock_result
            result = await retriever_with_embed._get_community_summaries(
                [0.5, 0.5, 0.5, 0.5], limit=2
            )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_skips_empty_summaries(
        self, retriever_with_embed: GraphRAGRetriever
    ) -> None:
        mock_result = MagicMock()
        mock_result.records_raw = [
            {"community_id": 1, "summary": "", "node_count": 3},
            {"community_id": 2, "summary": None, "node_count": 2},
            {"community_id": 3, "summary": "Valid summary", "node_count": 5},
        ]

        with patch("src.services.graphrag_retriever.GraphConnection") as mock_gc_cls:
            mock_gc_cls.return_value.engine.evaluate_query.return_value = mock_result
            result = await retriever_with_embed._get_community_summaries(
                [0.5, 0.5, 0.5, 0.5], limit=10
            )

        assert len(result) == 1
        assert result[0].community_id == 3

    @pytest.mark.asyncio
    async def test_handles_embedding_failure_gracefully(
        self, retriever_with_embed: GraphRAGRetriever, mock_embedding_service: AsyncMock
    ) -> None:
        # First embed call fails, second succeeds
        mock_embedding_service.embed_text = AsyncMock(
            side_effect=[
                RuntimeError("embed failed"),
                [0.5, 0.5, 0.5, 0.5],
            ]
        )

        mock_result = MagicMock()
        mock_result.records_raw = [
            {"community_id": 1, "summary": "Failing community", "node_count": 3},
            {"community_id": 2, "summary": "Working community", "node_count": 5},
        ]

        with patch("src.services.graphrag_retriever.GraphConnection") as mock_gc_cls:
            mock_gc_cls.return_value.engine.evaluate_query.return_value = mock_result
            result = await retriever_with_embed._get_community_summaries(
                [0.5, 0.5, 0.5, 0.5], limit=10
            )

        # Both should be returned; the failed one gets score 0.0
        assert len(result) == 2
        failed_community = next(r for r in result if r.community_id == 1)
        assert failed_community.relevance_score == 0.0
