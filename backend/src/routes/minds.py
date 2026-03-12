"""
API routes for the Mind-Based Data Model System.

This module defines all REST API endpoints for Mind node operations including
CRUD operations, version history, relationships, bulk operations, and queries.
It also implements global error handlers for consistent error responses.

**Validates: Requirements 3.1, 3.7, 4.1-4.5, 5.1-5.8, 6.1-6.6, 7.1-7.6,
8.1-8.6, 10.1-10.5, 11.1-11.7, 12.1-12.6**
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import JSONResponse, Response

from ..exceptions import (
    MindDatabaseError,
    MindError,
    MindNotFoundError,
    MindValidationError,
    RateLimitError,
)
from ..models.enums import StatusEnum
from ..schemas.mind_generic import (
    ErrorResponse,
    MindBulkUpdate,
    MindCreate,
    MindQueryFilters,
    MindResponse,
    MindUpdate,
    QueryResult,
    RelationshipResponse,
)
from ..services.mind_service import MindService

# Create router with prefix
router = APIRouter(prefix="/api/v1/minds")

# Initialize service
mind_service = MindService()


def generate_request_id() -> str:
    """Generate a unique request ID for error tracking."""
    return f"req_{uuid.uuid4().hex[:12]}"


def create_error_response(
    request_id: str, error_type: str, message: str, details: Optional[dict] = None
) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        request_id=request_id,
        error_type=error_type,
        message=message,
        details=details or {},
        timestamp=datetime.now(timezone.utc),
    )


# Exception Handlers
async def mind_not_found_handler(request: Request, exc: MindNotFoundError) -> JSONResponse:
    """Handle MindNotFoundError exceptions (HTTP 404)."""
    request_id = generate_request_id()
    error_response = create_error_response(
        request_id=request_id,
        error_type="NotFoundError",
        message=str(exc),
        details={"uuid": exc.uuid},
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content=error_response.model_dump(mode="json")
    )


async def mind_validation_handler(request: Request, exc: MindValidationError) -> JSONResponse:
    """Handle MindValidationError exceptions (HTTP 400)."""
    request_id = generate_request_id()
    error_response = create_error_response(
        request_id=request_id,
        error_type="ValidationError",
        message=str(exc),
        details={"error": str(exc)},
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=error_response.model_dump(mode="json")
    )


async def mind_database_handler(request: Request, exc: MindDatabaseError) -> JSONResponse:
    """Handle MindDatabaseError exceptions (HTTP 503)."""
    request_id = generate_request_id()
    error_response = create_error_response(
        request_id=request_id,
        error_type="DatabaseError",
        message="Database operation failed",
        details={"retry_after": 30, "error": str(exc)},
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(mode="json"),
        headers={"Retry-After": "30"},
    )


async def mind_error_handler(request: Request, exc: MindError) -> JSONResponse:
    """Handle generic MindError exceptions (HTTP 500)."""
    request_id = generate_request_id()
    error_response = create_error_response(
        request_id=request_id,
        error_type="InternalError",
        message="An unexpected error occurred",
        details={"error": str(exc)},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions (HTTP 400)."""
    request_id = generate_request_id()
    error_response = create_error_response(
        request_id=request_id,
        error_type="ValidationError",
        message="Invalid input data",
        details={"error": str(exc)},
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=error_response.model_dump(mode="json")
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions (HTTP 500)."""
    request_id = generate_request_id()
    error_response = create_error_response(
        request_id=request_id,
        error_type="InternalError",
        message="An unexpected error occurred",
        details={},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )


async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    """Handle RateLimitError exceptions (HTTP 429)."""
    request_id = generate_request_id()
    error_response = create_error_response(
        request_id=request_id,
        error_type="RateLimitError",
        message="Rate limit exceeded",
        details={"retry_after": 60, "limit": 100, "window": "1 minute"},
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.model_dump(mode="json"),
        headers={"Retry-After": "60"},
    )


# API Endpoints - IMPORTANT: Specific paths (/bulk) must come BEFORE parameterized paths (/{uuid})


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MindResponse)
async def create_mind(mind_data: MindCreate) -> MindResponse:
    """Create a new Mind node. Validates: Requirements 3.1, 3.7"""
    return await mind_service.create_mind(mind_data)


@router.get("", response_model=QueryResult)
async def query_minds(
    mind_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    creator: Optional[str] = Query(None),
    updated_after: Optional[datetime] = Query(None),
    updated_before: Optional[datetime] = Query(None),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> QueryResult:
    """Query and filter Mind nodes. Validates: Requirements 4.4, 4.5, 11.1-11.7"""
    status: Optional[StatusEnum] = StatusEnum(status_filter) if status_filter else None
    filters = MindQueryFilters(
        mind_type=mind_type,
        status=status,
        creator=creator,
        updated_after=updated_after,
        updated_before=updated_before,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return await mind_service.query_minds(filters)


@router.post("/bulk", status_code=status.HTTP_201_CREATED, response_model=list[MindResponse])
async def bulk_create_minds(minds_data: list[MindCreate]) -> list[MindResponse]:
    """Bulk create Mind nodes (max 100). Validates: Requirements 10.1, 10.3, 10.4, 10.5"""
    if len(minds_data) > 100:
        raise ValueError("Bulk create limited to 100 items per request")
    return await mind_service.bulk_create(minds_data)


@router.put("/bulk", response_model=list[MindResponse])
async def bulk_update_minds(updates_data: list[MindBulkUpdate]) -> list[MindResponse]:
    """Bulk update Mind nodes (max 100). Validates: Requirements 10.2, 10.3, 10.4, 10.5"""
    if len(updates_data) > 100:
        raise ValueError("Bulk update limited to 100 items per request")
    return await mind_service.bulk_update(updates_data)


@router.get("/{uuid}", response_model=MindResponse)
async def get_mind(uuid: UUID) -> MindResponse:
    """Retrieve a Mind node by UUID. Validates: Requirements 4.1, 4.2, 4.3"""
    return await mind_service.get_mind(uuid)


@router.put("/{uuid}", response_model=MindResponse)
async def update_mind(uuid: UUID, mind_data: MindUpdate) -> MindResponse:
    """Update a Mind node (creates new version). Validates: Requirements 5.1-5.8"""
    return await mind_service.update_mind(uuid, mind_data)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mind(uuid: UUID, hard: bool = Query(False)) -> Response:
    """Delete a Mind node (soft or hard). Validates: Requirements 7.1-7.6"""
    await mind_service.delete_mind(uuid, hard_delete=hard)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{uuid}/history", response_model=list[MindResponse])
async def get_version_history(
    uuid: UUID, page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=100)
) -> list[MindResponse]:
    """Get version history for a Mind node. Validates: Requirements 6.1-6.6"""
    return await mind_service.get_version_history(uuid, page=page, page_size=page_size)


@router.post(
    "/{uuid}/relationships",
    status_code=status.HTTP_201_CREATED,
    response_model=RelationshipResponse,
)
async def create_relationship(
    uuid: UUID, target_uuid: UUID = Query(...), relationship_type: str = Query(...)
) -> RelationshipResponse:
    """Create a relationship between Mind nodes. Validates: Requirements 8.1-8.6"""
    return await mind_service.create_relationship(uuid, target_uuid, relationship_type)


@router.get("/{uuid}/relationships", response_model=list[RelationshipResponse])
async def get_relationships(
    uuid: UUID,
    relationship_type: Optional[str] = Query(None),
    direction: Optional[str] = Query("both"),
) -> list[RelationshipResponse]:
    """Get relationships for a Mind node. Validates: Requirements 8.5"""
    return await mind_service.get_relationships(uuid, relationship_type, direction)
