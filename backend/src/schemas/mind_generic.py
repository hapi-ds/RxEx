"""
Generic Mind schemas for API routes.

These schemas are NOT auto-generated and should be maintained manually.
They provide generic interfaces for working with any Mind type via the API.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ..models.enums import StatusEnum


class MindCreate(BaseModel):
    """Generic schema for creating any Mind type."""
    mind_type: str
    title: str
    creator: str
    description: str | None = None
    status: StatusEnum | None = StatusEnum.DRAFT
    tags: list[str] | None = None
    type_specific_attributes: dict | None = None


class MindUpdate(BaseModel):
    """Generic schema for updating any Mind type. All fields optional."""
    title: str | None = None
    description: str | None = None
    status: StatusEnum | None = None
    tags: list[str] | None = None
    type_specific_attributes: dict | None = None


class MindResponse(BaseModel):
    """Generic schema for Mind responses."""
    uuid: UUID
    mind_type: str
    title: str
    description: str | None
    creator: str
    status: StatusEnum
    version: int
    created_at: datetime
    updated_at: datetime
    tags: list[str] | None = None
    type_specific_attributes: dict


class MindBulkUpdate(BaseModel):
    """Schema for bulk update operations."""
    uuids: list[UUID]
    updates: MindUpdate


class MindQueryFilters(BaseModel):
    """Schema for querying Minds with filters."""
    mind_type: str | None = None
    creator: str | None = None
    status: StatusEnum | None = None
    tags: list[str] | None = None
    limit: int = 50
    offset: int = 0


class QueryResult(BaseModel):
    """Schema for query results with pagination."""
    items: list[MindResponse]
    total: int
    limit: int
    offset: int


class RelationshipResponse(BaseModel):
    """Schema for relationship responses."""
    source_uuid: UUID
    target_uuid: UUID
    relationship_type: str
    created_at: datetime


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    request_id: str
    error_type: str
    message: str
    details: dict = {}
