"""API routes for GraphRAG knowledge base management.

This module defines REST API endpoints for managing the GraphRAG knowledge base
including bulk embedding generation, community detection, status queries, and
standalone semantic search. All endpoints require JWT authentication.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6**
"""

import asyncio
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from neontology import GraphConnection

from ..auth.deps import get_current_user
from ..config.config import settings
from ..models.user import UserNode
from ..schemas.graphrag import (
    KnowledgeBaseStatus,
    OperationResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from ..services.community_detector import CommunityDetector
from ..services.embedding_service import EmbeddingService
from ..services.graphrag_retriever import GraphRAGRetriever

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level locks for long-running operations
_embedding_lock = asyncio.Lock()
_community_lock = asyncio.Lock()


@router.post("/embeddings/generate", response_model=OperationResponse)
async def generate_embeddings(
    current_user: UserNode = Depends(get_current_user),
) -> OperationResponse:
    """Trigger bulk embedding generation for all un-embedded Mind nodes.

    Acquires a module-level lock to prevent concurrent embedding runs.
    Returns HTTP 409 if an embedding operation is already in progress.

    Args:
        current_user: Authenticated user from JWT token.

    Returns:
        OperationResponse with status and count of embedded nodes.

    **Validates: Requirements 8.1, 8.5, 8.6**
    """
    if _embedding_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Embedding generation is already in progress",
        )

    async with _embedding_lock:
        logger.info(
            "Bulk embedding generation triggered by %s",
            current_user.email,
        )
        embedding_service = EmbeddingService(settings)
        count = await embedding_service.bulk_embed_unembedded()

    return OperationResponse(
        status="completed",
        message=f"Bulk embedding generation completed for {count} nodes",
        details={"nodes_embedded": count},
    )


@router.post("/communities/detect", response_model=OperationResponse)
async def detect_communities(
    current_user: UserNode = Depends(get_current_user),
) -> OperationResponse:
    """Trigger community detection and summary generation.

    Acquires a module-level lock to prevent concurrent community detection runs.
    Returns HTTP 409 if a community detection operation is already in progress.

    Args:
        current_user: Authenticated user from JWT token.

    Returns:
        OperationResponse with status and community detection stats.

    **Validates: Requirements 8.2, 8.5, 8.6**
    """
    if _community_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Community detection is already in progress",
        )

    async with _community_lock:
        logger.info(
            "Community detection triggered by %s",
            current_user.email,
        )
        detector = CommunityDetector(settings)
        result = await detector.detect_and_summarize()

        if result.get("status") == "already_in_progress":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Community detection is already in progress",
            )

    return OperationResponse(
        status="completed",
        message=(
            f"Community detection completed: {result.get('community_count', 0)} communities, "
            f"{result.get('summaries_generated', 0)} summaries generated"
        ),
        details=result,
    )


@router.get("/status", response_model=KnowledgeBaseStatus)
async def get_status(
    current_user: UserNode = Depends(get_current_user),
) -> KnowledgeBaseStatus:
    """Return the current knowledge base status.

    Queries Neo4j for total Mind nodes, embedded node count, and community count.

    Args:
        current_user: Authenticated user from JWT token.

    Returns:
        KnowledgeBaseStatus with node counts and timestamps.

    **Validates: Requirements 8.3, 8.5**
    """
    gc = GraphConnection()

    # Total nodes with uuid and title
    total_cypher = (
        "MATCH (m) WHERE m.uuid IS NOT NULL AND m.title IS NOT NULL "
        "RETURN count(m) AS total"
    )
    # Embedded nodes
    embedded_cypher = (
        "MATCH (m) WHERE m.uuid IS NOT NULL AND m.embedding IS NOT NULL "
        "RETURN count(m) AS embedded"
    )
    # Community count
    community_cypher = (
        "MATCH (cs:CommunitySummary) RETURN count(cs) AS communities"
    )

    try:
        total_result = gc.engine.evaluate_query(total_cypher, {})
        total_nodes = (
            total_result.records_raw[0]["total"]
            if total_result and total_result.records_raw
            else 0
        )

        embedded_result = gc.engine.evaluate_query(embedded_cypher, {})
        embedded_nodes = (
            embedded_result.records_raw[0]["embedded"]
            if embedded_result and embedded_result.records_raw
            else 0
        )

        community_result = gc.engine.evaluate_query(community_cypher, {})
        community_count = (
            community_result.records_raw[0]["communities"]
            if community_result and community_result.records_raw
            else 0
        )
    except Exception as e:
        logger.error("Failed to query knowledge base status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query knowledge base status",
        ) from e

    return KnowledgeBaseStatus(
        total_nodes=total_nodes,
        embedded_nodes=embedded_nodes,
        community_count=community_count,
        last_embedding_sync=None,
        last_community_detection=None,
        graphrag_enabled=settings.graphrag_enabled,
    )


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: UserNode = Depends(get_current_user),
) -> SemanticSearchResponse:
    """Perform a standalone semantic search against the knowledge base.

    Embeds the query text, runs a vector similarity search against the Neo4j
    vector index, and returns matching nodes with scores and timing info.

    Args:
        request: SemanticSearchRequest with query, top_k, and threshold.
        current_user: Authenticated user from JWT token.

    Returns:
        SemanticSearchResponse with results and timing information.

    **Validates: Requirements 8.4, 8.5**
    """
    embedding_service = EmbeddingService(settings)
    retriever = GraphRAGRetriever(settings, embedding_service)

    # Embed the query
    embed_start = time.perf_counter()
    try:
        query_embedding = await embedding_service.embed_text(request.query)
    except RuntimeError as e:
        logger.error("Failed to embed search query: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {e}",
        ) from e
    embed_time_ms = (time.perf_counter() - embed_start) * 1000

    # Run semantic search
    search_start = time.perf_counter()
    seed_nodes = await retriever._semantic_search(
        query_embedding,
        top_k=request.top_k,
        threshold=request.threshold,
    )
    search_time_ms = (time.perf_counter() - search_start) * 1000

    results = [
        SemanticSearchResult(
            uuid=node.uuid,
            title=node.title,
            description=node.description,
            mind_type=node.mind_type,
            tags=node.tags,
            score=node.score,
        )
        for node in seed_nodes
    ]

    return SemanticSearchResponse(
        results=results,
        query_embedding_time_ms=round(embed_time_ms, 2),
        search_time_ms=round(search_time_ms, 2),
    )
