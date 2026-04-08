"""
API routes for Relationship operations.

This module defines REST API endpoints for managing relationships between Mind nodes.
"""

from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import Response
from pydantic import BaseModel

from ..schemas.mind_generic import RelationshipResponse
from ..services.mind_service import MindService

# Create router
router = APIRouter()

# Initialize service
mind_service = MindService()


class CreateRelationshipRequest(BaseModel):
    """Request body for creating a relationship."""
    from_uuid: UUID
    to_uuid: UUID
    relationship_type: str
    properties: dict | None = None


@router.get("", response_model=list[RelationshipResponse])
async def list_relationships() -> list[RelationshipResponse]:
    """Get all relationships across all minds."""
    return await mind_service.list_all_relationships()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RelationshipResponse)
async def create_relationship(body: CreateRelationshipRequest) -> RelationshipResponse:
    """Create a new relationship between two minds."""
    result = await mind_service.create_relationship(
        source_uuid=body.from_uuid,
        target_uuid=body.to_uuid,
        relationship_type=body.relationship_type.lower(),
        properties=body.properties,
    )
    return result


class UpdateRelationshipRequest(BaseModel):
    """Request body for updating a relationship's properties."""
    properties: dict


@router.put("/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(
    relationship_id: str,
    body: UpdateRelationshipRequest,
) -> RelationshipResponse:
    """Update a relationship's properties."""
    return await mind_service.update_relationship_properties(
        relationship_id=relationship_id,
        properties=body.properties,
    )


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(relationship_id: str) -> Response:
    """Delete a relationship."""
    # This would need to be implemented in the service
    raise NotImplementedError("Relationship deletion not yet implemented")
