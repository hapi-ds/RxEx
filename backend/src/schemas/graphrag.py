"""Pydantic schemas for GraphRAG knowledge base API request and response models.

This module defines the validation schemas used by the GraphRAG API endpoints
for semantic search, knowledge base status, bulk operations, and retrieval
result structures used internally by the GraphRAG retriever and context builder.

**Validates: Requirements 2.5, 8.1, 8.2, 8.3, 8.4**
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """Request payload for standalone semantic search.

    Attributes:
        query: The search query text to embed and match against Mind nodes.
        top_k: Maximum number of results to return.
        threshold: Minimum cosine similarity score for inclusion.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Search query text to embed and match against Mind nodes",
        examples=["What are the main risk areas in the project?"],
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return",
        examples=[10],
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score for inclusion",
        examples=[0.7],
    )


class SemanticSearchResult(BaseModel):
    """A single result from semantic search.

    Attributes:
        uuid: Unique identifier of the matched Mind node.
        title: Human-readable title of the Mind node.
        description: Optional detailed description.
        mind_type: The specific Mind type label (e.g., "Task", "Project").
        tags: Optional list of tags for categorization.
        score: Cosine similarity score between query and node embedding.
    """

    uuid: str = Field(
        ...,
        description="Unique identifier of the matched Mind node",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    title: str = Field(
        ...,
        description="Human-readable title of the Mind node",
        examples=["Design Phase"],
    )
    description: str | None = Field(
        default=None,
        description="Optional detailed description",
        examples=["Design phase for the NAMD project"],
    )
    mind_type: str = Field(
        ...,
        description="The specific Mind type label",
        examples=["Task"],
    )
    tags: list[str] | None = Field(
        default=None,
        description="Optional list of tags for categorization",
        examples=[["design", "namd"]],
    )
    score: float = Field(
        ...,
        description="Cosine similarity score between query and node embedding",
        examples=[0.92],
    )


class SemanticSearchResponse(BaseModel):
    """Response from the standalone semantic search endpoint.

    Attributes:
        results: List of matching Mind nodes with similarity scores.
        query_embedding_time_ms: Time spent generating the query embedding.
        search_time_ms: Time spent performing the vector similarity search.
    """

    results: list[SemanticSearchResult] = Field(
        ...,
        description="List of matching Mind nodes with similarity scores",
    )
    query_embedding_time_ms: float = Field(
        ...,
        description="Time spent generating the query embedding in milliseconds",
        examples=[45.2],
    )
    search_time_ms: float = Field(
        ...,
        description="Time spent performing the vector similarity search in milliseconds",
        examples=[12.8],
    )


class KnowledgeBaseStatus(BaseModel):
    """Current status of the GraphRAG knowledge base.

    Attributes:
        total_nodes: Total number of Mind nodes in the graph.
        embedded_nodes: Number of Mind nodes with embeddings.
        community_count: Number of detected communities.
        last_embedding_sync: Timestamp of the last embedding sync operation.
        last_community_detection: Timestamp of the last community detection run.
        graphrag_enabled: Whether GraphRAG is enabled in the configuration.
    """

    total_nodes: int = Field(
        ...,
        description="Total number of Mind nodes in the graph",
        examples=[150],
    )
    embedded_nodes: int = Field(
        ...,
        description="Number of Mind nodes with embeddings",
        examples=[142],
    )
    community_count: int = Field(
        ...,
        description="Number of detected communities",
        examples=[8],
    )
    last_embedding_sync: datetime | None = Field(
        default=None,
        description="Timestamp of the last embedding sync operation (ISO 8601 UTC)",
        examples=["2024-01-15T10:30:00Z"],
    )
    last_community_detection: datetime | None = Field(
        default=None,
        description="Timestamp of the last community detection run (ISO 8601 UTC)",
        examples=["2024-01-15T12:00:00Z"],
    )
    graphrag_enabled: bool = Field(
        ...,
        description="Whether GraphRAG is enabled in the configuration",
        examples=[True],
    )


class OperationResponse(BaseModel):
    """Response for bulk embedding or community detection operations.

    Attributes:
        status: Operation status indicator.
        message: Human-readable description of the operation result.
        details: Optional additional details about the operation.
    """

    status: str = Field(
        ...,
        description='Operation status: "started", "completed", or "already_in_progress"',
        examples=["started"],
    )
    message: str = Field(
        ...,
        description="Human-readable description of the operation result",
        examples=["Bulk embedding generation started for 42 nodes"],
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional additional details about the operation",
        examples=[{"nodes_processed": 42}],
    )


class SeedNode(BaseModel):
    """A semantically matched Mind node used as a seed for graph traversal.

    Attributes:
        uuid: Unique identifier of the Mind node.
        title: Human-readable title.
        description: Optional detailed description.
        mind_type: The specific Mind type label.
        tags: Optional list of tags.
        score: Cosine similarity score from semantic search.
    """

    uuid: str = Field(
        ...,
        description="Unique identifier of the Mind node",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    title: str = Field(
        ...,
        description="Human-readable title of the Mind node",
        examples=["Design Phase"],
    )
    description: str | None = Field(
        default=None,
        description="Optional detailed description",
    )
    mind_type: str = Field(
        ...,
        description="The specific Mind type label",
        examples=["Task"],
    )
    tags: list[str] | None = Field(
        default=None,
        description="Optional list of tags",
    )
    score: float = Field(
        ...,
        description="Cosine similarity score from semantic search",
        examples=[0.92],
    )


class SubgraphNode(BaseModel):
    """A node discovered during graph traversal from seed nodes.

    Attributes:
        uuid: Unique identifier of the Mind node.
        title: Human-readable title.
        mind_type: The specific Mind type label.
        status: Optional current lifecycle state.
    """

    uuid: str = Field(
        ...,
        description="Unique identifier of the Mind node",
        examples=["660e8400-e29b-41d4-a716-446655440001"],
    )
    title: str = Field(
        ...,
        description="Human-readable title of the Mind node",
        examples=["Implementation Sprint"],
    )
    mind_type: str = Field(
        ...,
        description="The specific Mind type label",
        examples=["Task"],
    )
    status: str | None = Field(
        default=None,
        description="Optional current lifecycle state",
        examples=["active"],
    )


class SubgraphEdge(BaseModel):
    """A relationship discovered during graph traversal.

    Attributes:
        relationship_type: Neo4j relationship type label.
        direction: Whether the edge is outgoing or incoming from the traversal perspective.
        source_uuid: UUID of the source node.
        target_uuid: UUID of the target node.
        connected_node_summary: Optional summary of the connected node (title, type, status).
    """

    relationship_type: str = Field(
        ...,
        description="Neo4j relationship type label",
        examples=["CONTAINS"],
    )
    direction: str = Field(
        ...,
        description='Edge direction: "outgoing" or "incoming"',
        examples=["outgoing"],
    )
    source_uuid: str = Field(
        ...,
        description="UUID of the source node",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    target_uuid: str = Field(
        ...,
        description="UUID of the target node",
        examples=["660e8400-e29b-41d4-a716-446655440001"],
    )
    connected_node_summary: str | None = Field(
        default=None,
        description="Optional summary of the connected node (title, type, status)",
        examples=["Implementation Sprint (Task, active)"],
    )


class CommunitySummary(BaseModel):
    """A community summary from community detection.

    Attributes:
        community_id: Unique community identifier.
        summary: Natural language summary of the community.
        node_count: Number of nodes in this community.
        relevance_score: Relevance score relative to the query (0.0 if unranked).
    """

    community_id: int = Field(
        ...,
        description="Unique community identifier",
        examples=[1],
    )
    summary: str = Field(
        ...,
        description="Natural language summary of the community",
        examples=["This community focuses on design and planning tasks for the NAMD project."],
    )
    node_count: int = Field(
        ...,
        description="Number of nodes in this community",
        examples=[12],
    )
    relevance_score: float = Field(
        default=0.0,
        description="Relevance score relative to the query (0.0 if unranked)",
        examples=[0.85],
    )


class RetrievalResult(BaseModel):
    """Complete retrieval output from the GraphRAG retriever.

    Combines semantic search hits, graph traversal results, and community
    summaries into a single structured result.

    Attributes:
        seed_nodes: Semantic search hits with similarity scores.
        subgraph_nodes: Nodes discovered during graph traversal.
        subgraph_edges: Relationships discovered during graph traversal.
        community_summaries: Ranked community summaries.
        retrieval_mode: The resolved retrieval mode used.
    """

    seed_nodes: list[SeedNode] = Field(
        ...,
        description="Semantic search hits with similarity scores",
    )
    subgraph_nodes: list[SubgraphNode] = Field(
        ...,
        description="Nodes discovered during graph traversal",
    )
    subgraph_edges: list[SubgraphEdge] = Field(
        ...,
        description="Relationships discovered during graph traversal",
    )
    community_summaries: list[CommunitySummary] = Field(
        ...,
        description="Ranked community summaries",
    )
    retrieval_mode: str = Field(
        ...,
        description='The resolved retrieval mode used: "local", "global", or "hybrid"',
        examples=["hybrid"],
    )
