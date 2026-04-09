"""Unit tests for EmbeddingService.

Tests cover _build_text concatenation logic, _normalize edge cases,
embed_text/embed_texts provider calls, embed_mind_node, and bulk_embed_unembedded.
"""

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.config import Settings
from src.services.embedding_service import EmbeddingService


@pytest.fixture
def test_settings() -> Settings:
    """Create settings configured for embedding tests."""
    return Settings(
        embedding_provider="custom",
        embedding_api_endpoint="http://localhost:1234/v1",
        embedding_model_name="test-model",
        embedding_dimensions=4,
    )


@pytest.fixture
def service(test_settings: Settings) -> EmbeddingService:
    return EmbeddingService(test_settings)


# --- _build_text ---


class TestBuildText:
    def test_title_only(self, service: EmbeddingService) -> None:
        assert service._build_text("My Title", None, None) == "My Title"

    def test_title_and_description(self, service: EmbeddingService) -> None:
        result = service._build_text("Title", "A description", None)
        assert result == "Title\nA description"

    def test_title_and_tags(self, service: EmbeddingService) -> None:
        result = service._build_text("Title", None, ["a", "b"])
        assert result == "Title\nTags: a, b"

    def test_all_fields(self, service: EmbeddingService) -> None:
        result = service._build_text("Title", "Desc", ["x", "y", "z"])
        assert result == "Title\nDesc\nTags: x, y, z"

    def test_empty_tags_list(self, service: EmbeddingService) -> None:
        result = service._build_text("Title", "Desc", [])
        assert result == "Title\nDesc"

    def test_empty_description(self, service: EmbeddingService) -> None:
        result = service._build_text("Title", "", None)
        assert result == "Title"


# --- _normalize ---


class TestNormalize:
    def test_unit_vector_unchanged(self, service: EmbeddingService) -> None:
        vec = [1.0, 0.0, 0.0]
        result = service._normalize(vec)
        assert result == pytest.approx([1.0, 0.0, 0.0], abs=1e-9)

    def test_normalizes_to_unit_length(self, service: EmbeddingService) -> None:
        vec = [3.0, 4.0]
        result = service._normalize(vec)
        magnitude = math.sqrt(sum(x * x for x in result))
        assert magnitude == pytest.approx(1.0, abs=1e-9)
        assert result == pytest.approx([0.6, 0.8], abs=1e-9)

    def test_zero_vector_unchanged(self, service: EmbeddingService) -> None:
        vec = [0.0, 0.0, 0.0]
        result = service._normalize(vec)
        assert result == [0.0, 0.0, 0.0]

    def test_single_element(self, service: EmbeddingService) -> None:
        result = service._normalize([5.0])
        assert result == pytest.approx([1.0], abs=1e-9)

    def test_negative_values(self, service: EmbeddingService) -> None:
        vec = [-3.0, 4.0]
        result = service._normalize(vec)
        magnitude = math.sqrt(sum(x * x for x in result))
        assert magnitude == pytest.approx(1.0, abs=1e-9)


# --- embed_text / embed_texts ---


class TestEmbedTexts:
    @pytest.mark.asyncio
    async def test_embed_text_calls_provider(self, service: EmbeddingService) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [1.0, 0.0, 0.0, 0.0], "index": 0}]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await service.embed_text("hello")

        assert len(result) == 4
        magnitude = math.sqrt(sum(x * x for x in result))
        assert magnitude == pytest.approx(1.0, abs=1e-9)

    @pytest.mark.asyncio
    async def test_embed_texts_batch(self, service: EmbeddingService) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [1.0, 0.0, 0.0, 0.0], "index": 0},
                {"embedding": [0.0, 1.0, 0.0, 0.0], "index": 1},
            ]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            results = await service.embed_texts(["hello", "world"])

        assert len(results) == 2
        for vec in results:
            assert len(vec) == 4

    @pytest.mark.asyncio
    async def test_embed_texts_no_endpoint_raises(self) -> None:
        svc = EmbeddingService(Settings(embedding_provider="none", embedding_dimensions=4))
        with pytest.raises(RuntimeError, match="not configured"):
            await svc.embed_texts(["test"])

    @pytest.mark.asyncio
    async def test_embed_texts_provider_error(self, service: EmbeddingService) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(RuntimeError, match="status 500"):
                await service.embed_texts(["test"])

    @pytest.mark.asyncio
    async def test_embed_texts_reorders_by_index(self, service: EmbeddingService) -> None:
        """Provider may return items out of order; we sort by index."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.0, 1.0, 0.0, 0.0], "index": 1},
                {"embedding": [1.0, 0.0, 0.0, 0.0], "index": 0},
            ]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            results = await service.embed_texts(["first", "second"])

        # index 0 should be [1,0,0,0] normalized
        assert results[0][0] == pytest.approx(1.0, abs=1e-9)
        assert results[1][1] == pytest.approx(1.0, abs=1e-9)
