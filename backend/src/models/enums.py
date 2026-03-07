"""
Enumeration types for the Mind-Based Data Model System.

This module defines the enumeration types used by the base Mind model
and derived Mind types. These enums ensure type safety and validation
for status, priority, severity, and probability attributes.

**Validates: Requirements 1.6**
"""

from enum import Enum


class StatusEnum(str, Enum):
    """
    Status enumeration for all Mind nodes.

    Defines the lifecycle states that any Mind node can be in.
    Used by the base Mind model and inherited by all derived types.

    **Validates: Requirements 1.6**
    """

    DRAFT = "draft"
    FROZEN = "frozen"
    ACCEPTED = "accepted"
    READY = "ready"
    DONE = "done"
    ARCHIVED = "archived"
    OBSOLET = "obsolet"


class PriorityEnum(str, Enum):
    """
    Priority enumeration for Task and UserNeed types.

    Defines priority levels for work items and user needs.
    Used by Task and UserNeed derived Mind types.

    **Validates: Requirements 9.2**
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SeverityEnum(str, Enum):
    """
    Severity enumeration for Risk type.

    Defines severity levels for risk assessment.
    Used by Risk derived Mind type.

    **Validates: Requirements 9.4**
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProbabilityEnum(str, Enum):
    """
    Probability enumeration for Risk type.

    Defines probability levels for risk likelihood assessment.
    Used by Risk derived Mind type.

    **Validates: Requirements 9.4**
    """

    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    CERTAIN = "certain"
