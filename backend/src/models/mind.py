"""
Base Mind model for the Mind-Based Data Model System.

This module defines the foundational BaseMind node type that serves as the
parent class for all 18 specialized Mind types. It uses neontology for Neo4j
ORM integration and Pydantic for attribute validation.

**Validates: Requirements 1.1, 1.2, 1.4, 1.5**
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from neontology import BaseNode, BaseRelationship
from pydantic import Field, field_serializer

from .enums import StatusEnum


class BaseMind(BaseNode):
    """
    Base Mind node containing core attributes inherited by all derived types.

    This class defines the foundational structure for all Mind nodes in the
    system. It includes universal attributes (UUID, title, version, timestamps,
    creator, status, description, tags) that are inherited by all 18 specialized
    Mind types.

    Attributes:
        uuid: Unique identifier that remains constant across all versions
        title: Human-readable name for the Mind node
        version: Auto-incrementing version number (starts at 1)
        created_at: Timestamp when the node was first created
        updated_at: Timestamp of last modification
        creator: User identifier who created the node
        status: Current lifecycle state (draft, active, archived, deleted)
        description: Optional detailed description
        tags: Optional list of tags for categorization

    **Validates: Requirements 1.1, 1.2, 1.4, 1.5**
    """

    __primarylabel__: str = "Mind"
    __primaryproperty__: str = "uuid"

    uuid: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier that remains constant across all versions",
    )
    title: str = Field(
        ..., min_length=1, max_length=200, description="Human-readable name for the Mind node"
    )
    version: int = Field(default=1, ge=1, description="Auto-incrementing version number")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of initial creation",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last modification",
    )

    creator: str = Field(..., min_length=1, description="User identifier who created the node")
    status: StatusEnum = Field(default=StatusEnum.DRAFT, description="Current lifecycle state")
    description: str | None = Field(
        default=None, max_length=1000, description="Optional detailed description"
    )
    tags: list[str] | None = Field(
        default=None, description="Optional list of tags for categorization"
    )

    # GraphRAG properties (written by embedding and community detection services)
    embedding: list[float] | None = Field(
        default=None, description="Vector embedding for semantic search"
    )
    community_id: int | None = Field(
        default=None, description="Community assignment from detection algorithm"
    )

    @field_serializer('uuid')
    def serialize_uuid(self, uuid: UUID, _info) -> str:
        """Serialize UUID to string for Neo4j compatibility."""
        return str(uuid)


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


class Scheduled(BaseRelationship):
    """
    Relationship linking INPUT nodes to their SCHEDULED versions.

    This relationship connects input specification nodes (Task, Project) with
    their calculated schedule state nodes (ScheduledTask, ScheduleHistory).
    It includes version and timestamp information for proper scheduling history.

    **Validates: Requirements 5.4**
    """

    __relationshiptype__: str = "SCHEDULED"

    source: BaseMind
    target: BaseMind
    version: int = Field(..., ge=1, description="Schedule version number")
    scheduled_at: datetime = Field(..., description="Timestamp when this schedule was computed")


class Contains(BaseRelationship):
    """
    Relationship for hierarchical containment within project structure.

    Used to link parent nodes (Project, Phase) to their child elements
    (Task, Milestone, Resource).

    **Validates: Requirements 8.1**
    """

    __relationshiptype__: str = "CONTAINS"

    source: BaseMind
    target: BaseMind
    level: int = Field(..., ge=0, description="Hierarchy level in WBS")


class Predates(BaseRelationship):
    """
    Relationship linking predecessor tasks to their successor tasks.

    This relationship defines task dependencies using TaskJuggler's dependency
    types. It enables the Critical Path Method scheduler to calculate proper
    scheduling based on task interdependencies.

    **Validates: Requirements 8.2**
    """

    __relationshiptype__: str = "PREDATES"

    source: BaseMind
    target: BaseMind
    dependency_type: str = Field(
        ..., description="Dependency type (FINISH_START, START_START, FINISH_FINISH, START_FINISH)"
    )
    gap_duration: Optional[float] = Field(
        default=None, ge=0.0, description="Time gap between tasks in days"
    )


class AssignedTo(BaseRelationship):
    """
    Relationship linking resources to tasks they work on.

    This relationship connects Resource nodes to Task nodes with effort
    allocation information for resource scheduling and cost calculation.

    **Validates: Requirements 8.2**
    """

    __relationshiptype__: str = "ASSIGNED_TO"

    source: BaseMind
    target: BaseMind
    effort_allocation: float = Field(
        ..., ge=0.0, le=1.0, description="Effort allocation as percentage (0.0-1.0)"
    )


class To(BaseRelationship):
    """
    Relationship linking journal_entries or bookings to tasks or projects.

    This relationship connects Journal_entry or booking nodes to Task nodes.
    (Booking FOR resource x TO task y)

    """

    __relationshiptype__: str = "TO"

    source: BaseMind
    target: BaseMind


class For(BaseRelationship):
    """
    Relationship linking bookings to resources.

    This relationship connects Resource nodes to booking nodes.
    (Booking FOR resource x TO task y)

    """

    __relationshiptype__: str = "FOR"

    source: BaseMind
    target: BaseMind


class Refines(BaseRelationship):
    """
    Relationship linking Requirements to Requirements.

    This relationship connects Requirement nodes to other Requirement nodes.

    """

    __relationshiptype__: str = "REFINES"

    source: BaseMind
    target: BaseMind


class HasScheduled(BaseRelationship):
    """Relationship linking a Project to its ScheduleHistory nodes."""

    __relationshiptype__: str = "HAS_SCHEDULED"

    source: BaseMind  # Project
    target: BaseMind  # ScheduleHistory


class CanOccur(BaseRelationship):
    """
    Relationship linking a Risk node to a Requirement node.

    This relationship indicates that a risk can occur for a given requirement,
    carrying two probability percentages (p1, p2) for conditional risk modeling
    (e.g., P1 = probability of exposure, P2 = probability of harm given exposure).

    **Validates: Requirements 3.1, 3.2, 3.3, 3.5**
    """

    __relationshiptype__: str = "CAN_OCCUR"

    source: BaseMind  # Risk
    target: BaseMind  # Requirement
    p1: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    p2: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class LeadTo(BaseRelationship):
    """
    Relationship linking a Failure node to a Risk or another Failure node.

    This relationship models failure chains and failure trees, where failures
    lead to risks or cascade into other failures. Supports infinite chaining
    of Failure → Failure connections for arbitrarily deep failure chains.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6, 4.8**
    """

    __relationshiptype__: str = "LEAD_TO"

    source: BaseMind  # Failure
    target: BaseMind  # Risk or Failure
    occurrence_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    detectability_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class Mitigates(BaseRelationship):
    """
    Relationship linking a Mitigation node to a Risk or Failure node.

    This relationship indicates that a mitigation measure reduces the likelihood
    or impact of a given risk or failure mode.
    """

    __relationshiptype__: str = "MITIGATES"

    source: BaseMind  # Mitigation
    target: BaseMind  # Risk or Failure

