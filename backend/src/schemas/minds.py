"""
Request schemas for the Mind-Based Data Model System.

This module defines Pydantic schemas for API request validation. These schemas
define the structure of incoming requests for creating, updating, and querying
Mind nodes. The schemas validate input data before it reaches the service layer.

**Validates: Requirements 3.1, 5.1, 11.1-11.7**
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.enums import StatusEnum


class MindCreate(BaseModel):
    """
    Schema for creating a new Mind node.

    This schema validates Mind creation requests, ensuring all required base
    attributes are provided along with type-specific attributes in a flexible
    dictionary format that will be validated based on the mind_type.

    Attributes:
        mind_type: The type of Mind node to create (e.g., "project", "task", "risk")
        title: Human-readable name for the Mind node
        description: Optional detailed description
        creator: User identifier who is creating the node
        type_specific_attributes: Dictionary of attributes specific to the mind_type

    **Validates: Requirements 3.1**
    """

    mind_type: str = Field(
        ...,
        min_length=1,
        description="Type of Mind node (project, task, company, department, resource, email, knowledge, requirement, acceptance_criteria, risk, failure, account, schedulehistory, scheduledtask)",
        examples=["project"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable name for the Mind node",
        examples=["Q1 2024 Product Launch"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional detailed description of the Mind node",
        examples=["Launch new product features for Q1 2024 including authentication and dashboard"],
    )
    creator: str = Field(
        ...,
        min_length=1,
        description="User identifier who is creating the node",
        examples=["user@example.com"],
    )
    type_specific_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of attributes specific to the mind_type (validated based on type)",
        examples=[{"start_date": "2024-01-01", "end_date": "2024-03-31", "budget": 50000.0}],
    )

    @field_validator("mind_type")
    @classmethod
    def validate_mind_type(cls, v: str) -> str:
        """Validate that mind_type is one of the supported types."""
        valid_types = {
            "project",
            "task",
            "company",
            "department",
            "resource",  # Replaces "employee" - use resource_type=PERSON in type_specific_attributes
            "email",
            "knowledge",
            "requirement",  # Consolidated: user_story, user_need, design_input, design_output, process_requirement, work_instruction_requirement
            "acceptance_criteria",
            "risk",
            "failure",
            "account",
            "schedulehistory",
            "scheduledtask",
        }
        if v not in valid_types:
            raise ValueError(f"mind_type must be one of: {', '.join(sorted(valid_types))}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mind_type": "project",
                    "title": "Q1 2024 Product Launch",
                    "description": "Launch new product features for Q1 2024",
                    "creator": "user@example.com",
                    "type_specific_attributes": {
                        "start_date": "2024-01-01",
                        "end_date": "2024-03-31",
                        "budget": 50000.0,
                    },
                },
                {
                    "mind_type": "task",
                    "title": "Implement authentication",
                    "description": "Add JWT-based authentication to the API",
                    "creator": "dev@example.com",
                    "type_specific_attributes": {
                        "priority": "high",
                        "assignee": "dev@example.com",
                        "due_date": "2024-01-20",
                        "estimated_hours": 8.0,
                    },
                },
            ]
        }
    }


class MindUpdate(BaseModel):
    """
    Schema for updating an existing Mind node.

    This schema validates Mind update requests. All fields are optional since
    updates may modify only a subset of attributes. When an update is applied,
    a new version of the Mind node is created with the updated attributes.

    Attributes:
        title: Optional updated title
        description: Optional updated description
        status: Optional updated status
        type_specific_attributes: Optional dictionary of updated type-specific attributes

    **Validates: Requirements 5.1**
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Optional updated title",
        examples=["Q1 2024 Product Launch - Updated"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional updated description",
        examples=["Updated scope to include mobile app features"],
    )
    status: Optional[StatusEnum] = Field(
        default=None,
        description="Optional updated status (draft, frozen, accepted, ready, done, archived, obsolet)",
        examples=["active"],
    )
    type_specific_attributes: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary of updated type-specific attributes",
        examples=[{"budget": 75000.0}],
    )

    @field_validator("title", "description")
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that if provided, string fields are not empty."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Field cannot be empty string")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"title": "Q1 2024 Product Launch - Phase 2", "status": "active"},
                {
                    "description": "Updated project scope",
                    "type_specific_attributes": {"budget": 75000.0, "end_date": "2024-04-15"},
                },
            ]
        }
    }


class MindQueryFilters(BaseModel):
    """
    Schema for querying and filtering Mind nodes.

    This schema validates query requests with support for filtering by type,
    status, creator, date ranges, and sorting options. Multiple filters are
    combined with AND logic. Results are paginated.

    Attributes:
        mind_type: Optional filter by Mind type
        status: Optional filter by status
        creator: Optional filter by creator
        updated_after: Optional filter for nodes updated after this datetime
        updated_before: Optional filter for nodes updated before this datetime
        sort_by: Field to sort by (updated_at, version, title)
        sort_order: Sort direction (asc or desc)
        page: Page number (1-based)
        page_size: Number of items per page (max 100)

    **Validates: Requirements 11.1-11.7**
    """

    mind_type: Optional[str] = Field(
        default=None, description="Optional filter by Mind type", examples=["project"]
    )
    status: Optional[StatusEnum] = Field(
        default=None, description="Optional filter by status", examples=["active"]
    )
    creator: Optional[str] = Field(
        default=None,
        description="Optional filter by creator identifier",
        examples=["user@example.com"],
    )
    updated_after: Optional[datetime] = Field(
        default=None,
        description="Optional filter for nodes updated after this datetime",
        examples=["2024-01-01T00:00:00Z"],
    )
    updated_before: Optional[datetime] = Field(
        default=None,
        description="Optional filter for nodes updated before this datetime",
        examples=["2024-12-31T23:59:59Z"],
    )
    sort_by: str = Field(
        default="updated_at",
        description="Field to sort by (updated_at, version, title)",
        examples=["updated_at"],
    )
    sort_order: str = Field(
        default="desc", description="Sort direction (asc or desc)", examples=["desc"]
    )
    page: int = Field(default=1, ge=1, description="Page number (1-based)", examples=[1])
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page (max 100)", examples=[20]
    )

    @field_validator("mind_type")
    @classmethod
    def validate_mind_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that mind_type is one of the supported types if provided."""
        if v is None:
            return v
        valid_types = {
            "project",
            "task",
            "company",
            "department",
            "resource",  # Replaces "employee"
            "email",
            "knowledge",
            "requirement",  # Consolidated type
            "acceptance_criteria",
            "risk",
            "failure",
            "account",
            "schedulehistory",
            "scheduledtask",
        }
        if v not in valid_types:
            raise ValueError(f"mind_type must be one of: {', '.join(sorted(valid_types))}")
        return v

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate that sort_by is one of the supported fields."""
        valid_fields = {"updated_at", "version", "title"}
        if v not in valid_fields:
            raise ValueError(f"sort_by must be one of: {', '.join(sorted(valid_fields))}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate that sort_order is either asc or desc."""
        if v not in {"asc", "desc"}:
            raise ValueError("sort_order must be either 'asc' or 'desc'")
        return v

    @field_validator("updated_before")
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate that updated_before is after updated_after if both are provided."""
        if (
            v is not None
            and "updated_after" in info.data
            and info.data["updated_after"] is not None
        ):
            if v <= info.data["updated_after"]:
                raise ValueError("updated_before must be after updated_after")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mind_type": "project",
                    "status": "active",
                    "sort_by": "updated_at",
                    "sort_order": "desc",
                    "page": 1,
                    "page_size": 20,
                },
                {
                    "creator": "user@example.com",
                    "updated_after": "2024-01-01T00:00:00Z",
                    "updated_before": "2024-12-31T23:59:59Z",
                    "sort_by": "title",
                    "sort_order": "asc",
                    "page": 1,
                    "page_size": 50,
                },
            ]
        }
    }


class MindBulkUpdate(BaseModel):
    """
    Schema for bulk update operations on Mind nodes.

    This schema validates bulk update requests where multiple Mind nodes can be
    updated in a single operation. Each update specifies the UUID of the node
    to update and the fields to modify.

    Attributes:
        uuid: UUID of the Mind node to update
        title: Optional updated title
        description: Optional updated description
        status: Optional updated status
        type_specific_attributes: Optional dictionary of updated type-specific attributes

    **Validates: Requirements 11.1-11.7**
    """

    uuid: UUID = Field(
        ...,
        description="UUID of the Mind node to update",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Optional updated title",
        examples=["Updated Title"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional updated description",
        examples=["Updated description"],
    )
    status: Optional[StatusEnum] = Field(
        default=None, description="Optional updated status", examples=["active"]
    )
    type_specific_attributes: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary of updated type-specific attributes",
        examples=[{"priority": "high"}],
    )

    @field_validator("title", "description")
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that if provided, string fields are not empty."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Field cannot be empty string")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"uuid": "550e8400-e29b-41d4-a716-446655440000", "status": "active"},
                {
                    "uuid": "660e8400-e29b-41d4-a716-446655440001",
                    "title": "Updated Task Title",
                    "type_specific_attributes": {"priority": "critical", "due_date": "2024-02-01"},
                },
            ]
        }
    }


# ============================================================================
# Response Schemas
# ============================================================================


class MindResponse(BaseModel):
    """
    Schema for Mind node responses.

    This schema defines the structure of Mind node data returned from the API.
    It includes all base Mind attributes plus type-specific attributes in a
    flexible dictionary format. This schema is used for single node responses
    from create, retrieve, and update operations.

    Attributes:
        uuid: Unique identifier for the Mind node (immutable across versions)
        mind_type: Type of Mind node (e.g., "project", "task", "risk")
        title: Human-readable name for the Mind node
        version: Version number (auto-incremented on updates)
        updated_at: Timestamp of last modification
        creator: User identifier who created the node
        status: Current status of the node
        description: Optional detailed description
        type_specific_attributes: Dictionary of attributes specific to the mind_type

    **Validates: Requirements 3.7, 4.2**
    """

    uuid: UUID = Field(
        ...,
        description="Unique identifier for the Mind node (immutable across versions)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    mind_type: str = Field(..., description="Type of Mind node", examples=["project"])
    title: str = Field(
        ...,
        description="Human-readable name for the Mind node",
        examples=["Q1 2024 Product Launch"],
    )
    version: int = Field(
        ..., ge=1, description="Version number (auto-incremented on updates)", examples=[1]
    )
    updated_at: datetime = Field(
        ..., description="Timestamp of last modification", examples=["2024-01-15T10:30:00Z"]
    )
    creator: str = Field(
        ..., description="User identifier who created the node", examples=["user@example.com"]
    )
    status: StatusEnum = Field(..., description="Current status of the node", examples=["active"])
    description: Optional[str] = Field(
        default=None,
        description="Optional detailed description",
        examples=["Launch new product features for Q1 2024"],
    )
    type_specific_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of attributes specific to the mind_type",
        examples=[{"start_date": "2024-01-01", "end_date": "2024-03-31", "budget": 50000.0}],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "uuid": "550e8400-e29b-41d4-a716-446655440000",
                    "mind_type": "project",
                    "title": "Q1 2024 Product Launch",
                    "version": 1,
                    "updated_at": "2024-01-15T10:30:00Z",
                    "creator": "user@example.com",
                    "status": "active",
                    "description": "Launch new product features for Q1 2024",
                    "type_specific_attributes": {
                        "start_date": "2024-01-01",
                        "end_date": "2024-03-31",
                        "budget": 50000.0,
                    },
                },
                {
                    "uuid": "660e8400-e29b-41d4-a716-446655440001",
                    "mind_type": "task",
                    "title": "Implement authentication",
                    "version": 2,
                    "updated_at": "2024-01-16T14:20:00Z",
                    "creator": "dev@example.com",
                    "status": "active",
                    "description": "Add JWT-based authentication to the API",
                    "type_specific_attributes": {
                        "priority": "high",
                        "assignee": "dev@example.com",
                        "due_date": "2024-01-20",
                        "estimated_hours": 8.0,
                    },
                },
            ]
        }
    }


class QueryResult(BaseModel):
    """
    Schema for paginated query results.

    This schema defines the structure of paginated query responses. It includes
    the list of Mind nodes matching the query criteria along with pagination
    metadata to enable clients to navigate through large result sets.

    Attributes:
        items: List of Mind nodes matching the query criteria
        total: Total number of items matching the query (across all pages)
        page: Current page number (1-based)
        page_size: Number of items per page
        total_pages: Total number of pages available

    **Validates: Requirements 4.2, 11.7**
    """

    items: list[MindResponse] = Field(
        ..., description="List of Mind nodes matching the query criteria", examples=[[]]
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of items matching the query (across all pages)",
        examples=[42],
    )
    page: int = Field(..., ge=1, description="Current page number (1-based)", examples=[1])
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page", examples=[20])
    total_pages: int = Field(..., ge=0, description="Total number of pages available", examples=[3])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "uuid": "550e8400-e29b-41d4-a716-446655440000",
                            "mind_type": "project",
                            "title": "Q1 2024 Product Launch",
                            "version": 1,
                            "updated_at": "2024-01-15T10:30:00Z",
                            "creator": "user@example.com",
                            "status": "active",
                            "description": "Launch new product features",
                            "type_specific_attributes": {
                                "start_date": "2024-01-01",
                                "end_date": "2024-03-31",
                            },
                        }
                    ],
                    "total": 42,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 3,
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """
    Schema for error responses.

    This schema defines the consistent structure for all error responses from
    the API. It includes a unique request ID for tracing, error type for
    categorization, human-readable message, optional details dictionary, and
    timestamp of when the error occurred.

    Attributes:
        request_id: Unique identifier for the request (for tracing and debugging)
        error_type: Category of error (ValidationError, NotFoundError, DatabaseError, etc.)
        message: Human-readable error message
        details: Optional dictionary with additional error context
        timestamp: Timestamp when the error occurred

    **Validates: Requirements 12.1**
    """

    request_id: str = Field(
        ...,
        description="Unique identifier for the request (for tracing and debugging)",
        examples=["req_abc123"],
    )
    error_type: str = Field(
        ...,
        description="Category of error (ValidationError, NotFoundError, DatabaseError, RateLimitError, InternalError)",
        examples=["ValidationError"],
    )
    message: str = Field(
        ..., description="Human-readable error message", examples=["Invalid input data"]
    )
    details: dict[str, Any] = Field(
        ...,
        description="Dictionary with additional error context",
        examples=[{"field": "start_date", "error": "start_date must be before end_date"}],
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the error occurred", examples=["2024-01-15T10:30:00Z"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "req_abc123",
                    "error_type": "ValidationError",
                    "message": "Invalid input data",
                    "details": {
                        "field": "start_date",
                        "error": "start_date must be before end_date",
                    },
                    "timestamp": "2024-01-15T10:30:00Z",
                },
                {
                    "request_id": "req_abc124",
                    "error_type": "NotFoundError",
                    "message": "Mind node not found",
                    "details": {"uuid": "550e8400-e29b-41d4-a716-446655440000"},
                    "timestamp": "2024-01-15T10:31:00Z",
                },
                {
                    "request_id": "req_abc125",
                    "error_type": "DatabaseError",
                    "message": "Database connection failed",
                    "details": {"retry_after": 30},
                    "timestamp": "2024-01-15T10:32:00Z",
                },
            ]
        }
    }


class RelationshipResponse(BaseModel):
    """
    Schema for relationship operation responses.

    This schema defines the structure of relationship data returned from the API.
    It includes the relationship type, source and target UUIDs, and optional
    metadata about the relationship. Used for relationship creation and query
    operations.

    Attributes:
        relationship_type: Type of relationship (contains, depends_on, assigned_to, relates_to, implements, mitigates)
        source_uuid: UUID of the source Mind node
        target_uuid: UUID of the target Mind node
        created_at: Timestamp when the relationship was created
        properties: Optional dictionary of relationship properties

    **Validates: Requirements 8.4, 8.5**
    """

    relationship_type: str = Field(
        ...,
        description="Type of relationship (contains, depends_on, assigned_to, relates_to, implements, mitigates)",
        examples=["contains"],
    )
    source_uuid: UUID = Field(
        ...,
        description="UUID of the source Mind node",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    target_uuid: UUID = Field(
        ...,
        description="UUID of the target Mind node",
        examples=["660e8400-e29b-41d4-a716-446655440001"],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the relationship was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    properties: dict[str, Any] = Field(
        ...,
        description="Dictionary of relationship properties",
        examples=[{"weight": 1.0, "notes": "Primary dependency"}],
    )

    @field_validator("relationship_type")
    @classmethod
    def validate_relationship_type(cls, v: str) -> str:
        """Validate that relationship_type is one of the supported types."""
        valid_types = {
            "contains",
            "depends_on",
            "assigned_to",
            "relates_to",
            "implements",
            "mitigates",
        }
        if v not in valid_types:
            raise ValueError(f"relationship_type must be one of: {', '.join(sorted(valid_types))}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "relationship_type": "contains",
                    "source_uuid": "550e8400-e29b-41d4-a716-446655440000",
                    "target_uuid": "660e8400-e29b-41d4-a716-446655440001",
                    "created_at": "2024-01-15T10:30:00Z",
                    "properties": None,
                },
                {
                    "relationship_type": "depends_on",
                    "source_uuid": "770e8400-e29b-41d4-a716-446655440002",
                    "target_uuid": "660e8400-e29b-41d4-a716-446655440001",
                    "created_at": "2024-01-15T11:00:00Z",
                    "properties": {
                        "weight": 1.0,
                        "notes": "Must complete authentication before dashboard",
                    },
                },
                {
                    "relationship_type": "assigned_to",
                    "source_uuid": "660e8400-e29b-41d4-a716-446655440001",
                    "target_uuid": "880e8400-e29b-41d4-a716-446655440003",
                    "created_at": "2024-01-15T12:00:00Z",
                    "properties": None,
                },
            ]
        }
    }
