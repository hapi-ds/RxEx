"""
Base Mind model for the Mind-Based Data Model System.

This module defines the foundational BaseMind node type that serves as the
parent class for all 18 specialized Mind types. It uses neontology for Neo4j
ORM integration and Pydantic for attribute validation.

**Validates: Requirements 1.1, 1.2, 1.4, 1.5**
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from neontology import BaseNode, BaseRelationship
from pydantic import Field

from .enums import StatusEnum


class BaseMind(BaseNode):
    """
    Base Mind node containing core attributes inherited by all derived types.

    This class defines the foundational structure for all Mind nodes in the
    system. It includes universal attributes (UUID, title, version, timestamps,
    creator, status, description) that are inherited by all 18 specialized
    Mind types.

    Attributes:
        uuid: Unique identifier that remains constant across all versions
        title: Human-readable name for the Mind node
        version: Auto-incrementing version number (starts at 1)
        updated_at: Timestamp of last modification
        creator: User identifier who created the node
        status: Current lifecycle state (draft, active, archived, deleted)
        description: Optional detailed description

    **Validates: Requirements 1.1, 1.2, 1.4, 1.5**
    """

    __primarylabel__: str = "Mind"
    __primaryproperty__: str = "uuid"

    uuid: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier that remains constant across all versions"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable name for the Mind node"
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Auto-incrementing version number"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last modification"
    )
    creator: str = Field(
        ...,
        min_length=1,
        description="User identifier who created the node"
    )
    status: StatusEnum = Field(
        default=StatusEnum.DRAFT,
        description="Current lifecycle state"
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional detailed description"
    )


class Previous(BaseRelationship):
    """
    Relationship linking a Mind node to its previous version.

    This relationship enables version history tracking by creating a chain
    from newer versions to older versions. Each update creates a new Mind
    node that links to its predecessor via this relationship.

    **Validates: Requirements 5.4**
    """

    __relationshiptype__: str = "PREVIOUS"

    source: BaseMind
    target: BaseMind
