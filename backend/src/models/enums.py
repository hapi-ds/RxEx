"""
Enumeration types for the Mind-Based Data Model System with TaskJuggler integration.

**Validates: Requirements 1.6**
"""

from enum import Enum


class StatusEnum(str, Enum):
    """Status enumeration for all Mind nodes."""
    DRAFT = "draft"
    FROZEN = "frozen"
    ACCEPTED = "accepted"
    READY = "ready"
    ACTIVE = "active"
    DONE = "done"
    ARCHIVED = "archived"
    OBSOLET = "obsolet"
    DELETED = "deleted"


class PriorityEnum(str, Enum):
    """Priority enumeration for Task and Requirement types."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SeverityEnum(str, Enum):
    """Severity enumeration for Risk type."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProbabilityEnum(str, Enum):
    """Probability enumeration for Risk type."""
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    CERTAIN = "certain"


class ResourceType(Enum):
    """Resource type enumeration - PERSON, GROUP, or EQUIPMENT."""
    PERSON = "PERSON"
    GROUP = "GROUP"
    EQUIPMENT = "EQUIPMENT"


class AccountType(Enum):
    """Account type enumeration for COST or REVENUE tracking."""
    COST = "COST"
    REVENUE = "REVENUE"


class TaskType(Enum):
    """Task type enumeration - all consolidated task variants."""
    TASK = "TASK"  # Regular work item
    PHASE = "PHASE"  # Project phase/stage
    MILESTONE = "MILESTONE"  # Significant checkpoint
    WORKPACKAGE = "WORKPACKAGE"  # Collection of activities


class RequirementType(Enum):
    """Requirement type enumeration for all requirement variants."""
    USER_STORY = "USER_STORY"
    USER_NEED = "USER_NEED"
    DESIGN_INPUT = "DESIGN_INPUT"
    DESIGN_OUTPUT = "DESIGN_OUTPUT"
    PROCESS_REQUIREMENT = "PROCESS_REQUIREMENT"
    WORK_INSTRUCTION_REQUIREMENT = "WORK_INSTRUCTION_REQUIREMENT"
