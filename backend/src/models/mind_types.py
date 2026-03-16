"""
Derived Mind types for the Mind-Based Data Model System.

This module defines specialized Mind node types that extend BaseMind with
type-specific attributes. Each derived type inherits all base attributes
(uuid, title, version, updated_at, creator, status, description) and adds
its own specialized fields.

**Validates: Requirements 2.1, 2.2, 2.3, 9.1, 9.2, 9.3, 9.4**
"""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator, field_serializer

from .enums import (
    PriorityEnum,
    ProbabilityEnum,
    SeverityEnum,
    ResourceType,
    AccountType,
    TaskType,
    StatusEnum,
    RequirementType,
)
from .mind import BaseMind


class Project(BaseMind):
    """
    Project Mind type representing a time-bound initiative with budget.

    Extends BaseMind with project-specific attributes including start/end dates
    and optional budget tracking.

    Attributes:
        start_date: Project start date
        end_date: Project end date (must be after start_date)
        budget: Optional budget amount in currency units

    **Validates: Requirements 2.1, 2.2, 2.3, 9.1**
    """

    __primarylabel__: str = "Project"

    start_date: date = Field(
        ...,
        description="Project start date"
    )
    end_date: date = Field(
        ...,
        description="Project end date"
    )
    budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional budget amount in currency units"
    )

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        """Validate that end_date is after start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


# PHASE is now handled by Task with task_type=PHASE

class Task(BaseMind):
    """
    Task Mind type representing a work item with priority and effort.

    Extends BaseMind with task-specific attributes including priority level,
    optional due date, and effort estimation. Resource assignment is handled
    exclusively via ASSIGNED_TO relationships (not as a field attribute).
    Resources assigned to parent nodes (Project, Phase, WorkPackage) are
    implicitly inherited by child tasks through the CONTAINS hierarchy.

    Attributes:
        priority: Task priority level (low, medium, high, critical)
        due_date: Optional due date for task completion
        effort: Optional work effort in hours
        duration: Optional work duration in days
        length: Optional calendar length in days

    **Validates: Requirements 2.1, 2.2, 2.3, 9.2**
    """

    __primarylabel__: str = "Task"

    priority: PriorityEnum = Field(
        ...,
        description="Task priority level"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Optional due date for task completion"
    )
    effort: Optional[float] = Field(
        default=None, ge=0.0, description="Work effort in hours"
    )
    duration: Optional[float] = Field(
        default=None, ge=0.0, description="Work duration in days"
    )
    length: Optional[float] = Field(
        default=None, ge=0.0, description="Calendar length in days"
    )
            
    # Consolidated task types (PHASE, MILESTONE, WORKPACKAGE)
    task_type: TaskType = Field(default="TASK", description="Type of task")
    phase_number: Optional[int] = Field(
        default=None, ge=1, description="Sequential phase number (when task_type=PHASE)"
    )
    target_date: Optional[date] = Field(
        default=None, description="Target date for milestones (when task_type=MILESTONE)"
    )
    completion_percentage: Optional[float] = Field(
        default=None, ge=0, le=100, description="Completion percentage 0-100 (when task_type=MILESTONE)"
    )

    @field_serializer('task_type')
    def serialize_task_type(self, task_type: TaskType, _info):
        """Serialize TaskType enum to its value for Neo4j storage."""
        if isinstance(task_type, TaskType):
            return task_type.value
        return task_type

    @field_validator('task_type', mode='before')
    @classmethod
    def validate_task_type(cls, v):
        """Validate and normalize task_type from various formats."""
        if isinstance(v, TaskType):
            return v
        if isinstance(v, str):
            # Handle "TaskType.TASK" format from old data
            if v.startswith("TaskType."):
                v = v.replace("TaskType.", "")
            # Now validate against enum values (uppercase for TaskType)
            return TaskType(v.upper())
        return v

    @field_serializer('priority')
    def serialize_priority(self, priority: PriorityEnum, _info):
        """Serialize PriorityEnum to its value."""
        if isinstance(priority, PriorityEnum):
            return priority.value
        return priority

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v):
        """Validate and normalize priority from various formats."""
        if isinstance(v, PriorityEnum):
            return v
        if isinstance(v, str):
            if v.startswith("PriorityEnum."):
                v = v.replace("PriorityEnum.", "")
            # Try case-insensitive match
            return PriorityEnum(v.lower())
        return v


class Company(BaseMind):
    """
    Company Mind type representing an organization.

    Extends BaseMind with company-specific attributes including industry,
    size, and founding date.

    Attributes:
        industry: Industry sector or classification
        size: Optional number of employees
        founded_date: Optional company founding date

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "Company"

    industry: str = Field(
        ...,
        min_length=1,
        description="Industry sector or classification"
    )
    size: Optional[int] = Field(
        default=None,
        ge=1,
        description="Optional number of employees"
    )
    founded_date: Optional[date] = Field(
        default=None,
        description="Optional company founding date"
    )


class Department(BaseMind):
    """
    Department Mind type representing an organizational unit.

    Extends BaseMind with department-specific attributes including department
    code and optional manager identifier.

    Attributes:
        department_code: Unique department code or identifier
        manager: Optional user identifier of the department manager

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "Department"

    department_code: str = Field(
        ...,
        min_length=1,
        description="Unique department code or identifier"
    )
    manager: Optional[str] = Field(
        default=None,
        description="Optional user identifier of the department manager"
    )


class Email(BaseMind):
    """
    Email Mind type representing an email message.

    Extends BaseMind with email-specific attributes including sender,
    recipients, subject, and timestamp.

    Attributes:
        sender: Email address of the sender
        recipients: List of recipient email addresses
        subject: Email subject line
        sent_at: Timestamp when the email was sent

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "Email"

    sender: EmailStr = Field(
        ...,
        description="Email address of the sender"
    )
    recipients: list[EmailStr] = Field(
        ...,
        min_length=1,
        description="List of recipient email addresses"
    )
    subject: str = Field(
        ...,
        min_length=1,
        description="Email subject line"
    )
    sent_at: datetime = Field(
        ...,
        description="Timestamp when the email was sent"
    )


class Knowledge(BaseMind):
    """
    Knowledge Mind type representing a knowledge article or document.

    Extends BaseMind with knowledge-specific attributes including category,
    tags, and content.

    Attributes:
        category: Knowledge category or classification
        tags: List of tags for categorization and search
        content: Knowledge article content

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "Knowledge"

    category: str = Field(
        ...,
        min_length=1,
        description="Knowledge category or classification"
    )
    tags: list[str] = Field(
        ...,
        min_length=1,
        description="List of tags for categorization and search"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Knowledge article content"
    )



class AcceptanceCriteria(BaseMind):
    """
    AcceptanceCriteria Mind type representing acceptance criteria for a requirement.

    Extends BaseMind with acceptance criteria-specific attributes including
    criteria text, verification method, and verification status.

    Attributes:
        criteria_text: Detailed acceptance criteria description
        verification_method: Method used to verify the criteria
        verification_status: Current verification status (pending, verified, failed)

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "AcceptanceCriteria"

    criteria_text: str = Field(
        ...,
        min_length=1,
        description="Detailed acceptance criteria description"
    )
    verification_method: str = Field(
        ...,
        min_length=1,
        description="Method used to verify the criteria"
    )
    verification_status: str = Field(
        ...,
        min_length=1,
        description="Current verification status (pending, verified, failed)"
    )


class Risk(BaseMind):
    """
    Risk Mind type representing a project or process risk.

    Extends BaseMind with risk-specific attributes including severity,
    probability, and optional mitigation plan.

    Attributes:
        severity: Risk severity level (low, medium, high, critical)
        probability: Risk probability (rare, unlikely, possible, likely, certain)
        mitigation_plan: Optional risk mitigation plan

    **Validates: Requirements 2.1, 2.2, 2.3, 9.4**
    """

    __primarylabel__: str = "Risk"

    severity: SeverityEnum = Field(
        ...,
        description="Risk severity level"
    )
    probability: ProbabilityEnum = Field(
        ...,
        description="Risk probability"
    )
    mitigation_plan: Optional[str] = Field(
        default=None,
        description="Optional risk mitigation plan"
    )


    @field_serializer('severity')
    def serialize_severity(self, severity: SeverityEnum, _info):
        """Serialize SeverityEnum to its value."""
        if isinstance(severity, SeverityEnum):
            return severity.value
        return severity

    @field_validator('severity', mode='before')
    @classmethod
    def validate_severity(cls, v):
        """Validate and normalize severity from various formats."""
        if isinstance(v, SeverityEnum):
            return v
        if isinstance(v, str):
            if v.startswith("SeverityEnum."):
                v = v.replace("SeverityEnum.", "")
            return SeverityEnum(v.lower())
        return v

    @field_serializer('probability')
    def serialize_probability(self, probability: ProbabilityEnum, _info):
        """Serialize ProbabilityEnum to its value."""
        if isinstance(probability, ProbabilityEnum):
            return probability.value
        return probability

    @field_validator('probability', mode='before')
    @classmethod
    def validate_probability(cls, v):
        """Validate and normalize probability from various formats."""
        if isinstance(v, ProbabilityEnum):
            return v
        if isinstance(v, str):
            if v.startswith("ProbabilityEnum."):
                v = v.replace("ProbabilityEnum.", "")
            return ProbabilityEnum(v.lower())
        return v



class Failure(BaseMind):
    """
    Failure Mind type representing a failure mode analysis.

    Extends BaseMind with failure-specific attributes including failure mode,
    effects, causes, and optional detection method.

    Attributes:
        failure_mode: Description of the failure mode
        effects: Effects or consequences of the failure
        causes: Root causes of the failure
        detection_method: Optional method for detecting the failure

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "Failure"

    failure_mode: str = Field(
        ...,
        min_length=1,
        description="Description of the failure mode"
    )
    effects: str = Field(
        ...,
        min_length=1,
        description="Effects or consequences of the failure"
    )
    causes: str = Field(
        ...,
        min_length=1,
        description="Root causes of the failure"
    )
    detection_method: Optional[str] = Field(
        default=None,
        description="Optional method for detecting the failure"
    )



class Requirement(BaseMind):
    """Requirement Mind type representing various requirement variants."""
    
    __primarylabel__: str = "Requirement"
    
    requirement_type: RequirementType = Field(..., description="Type of requirement")
    content: str = Field(..., min_length=1, description="Requirement content or text")
    
    # Optional fields
    source: Optional[str] = Field(default=None, description="Source of requirement")
    acceptance_criteria: Optional[str] = Field(
        default=None, description="Acceptance criteria"
    )
    compliance_standard: Optional[str] = Field(
        default=None, description="Compliance standard reference"
    )
    safety_critical: bool = Field(
        default=False, description="Safety-critical flag"
    )


    @field_serializer('requirement_type')
    def serialize_requirement_type(self, requirement_type: RequirementType, _info):
        """Serialize RequirementType enum to its value."""
        if isinstance(requirement_type, RequirementType):
            return requirement_type.value
        return requirement_type

    @field_validator('requirement_type', mode='before')
    @classmethod
    def validate_requirement_type(cls, v):
        """Validate and normalize requirement_type from various formats."""
        if isinstance(v, RequirementType):
            return v
        if isinstance(v, str):
            if v.startswith("RequirementType."):
                v = v.replace("RequirementType.", "")
            return RequirementType(v.upper())
        return v


class Resource(BaseMind):
    """Resource Mind type representing a human or system resource."""

    __primarylabel__: str = "Resource"

    email: Optional[str] = Field(
        default=None, description="Optional email address for the resource"
    )
    workinghours_max_per_week: float = Field(
        default=40.0, ge=0.0, description="Maximal working hours per week"
    )
    workinghours_per_year: float = Field(
        default=1700.0, ge=0.0, description="Working hours per year"
    )
    efficiency: float = Field(
        default=1.0, ge=0.0, le=5.0, description="Work efficiency factor (0.0-5.0)"
    )
    hourly_rate: float = Field(default=100.0, ge=0.0, description="Hourly cost rate in EUR")
    resource_type: ResourceType = Field(
        default=ResourceType.PERSON, description="Type of resource"
    )


    @field_serializer('resource_type')
    def serialize_resource_type(self, resource_type: ResourceType, _info):
        """Serialize ResourceType enum to its value."""
        if isinstance(resource_type, ResourceType):
            return resource_type.value
        return resource_type

    @field_validator('resource_type', mode='before')
    @classmethod
    def validate_resource_type(cls, v):
        """Validate and normalize resource_type from various formats."""
        if isinstance(v, ResourceType):
            return v
        if isinstance(v, str):
            if v.startswith("ResourceType."):
                v = v.replace("ResourceType.", "")
            return ResourceType(v.upper())
        return v


class Journalentry(BaseMind):
    """Journalentry Mind type TO task or project."""

    __primarylabel__: str = "Journalentry"

    severity: SeverityEnum = Field(
        ...,
        description="Severity of the journal entry"
    )


    @field_serializer('severity')
    def serialize_severity(self, severity: SeverityEnum, _info):
        """Serialize SeverityEnum to its value."""
        if isinstance(severity, SeverityEnum):
            return severity.value
        return severity

    @field_validator('severity', mode='before')
    @classmethod
    def validate_severity(cls, v):
        """Validate and normalize severity from various formats."""
        if isinstance(v, SeverityEnum):
            return v
        if isinstance(v, str):
            if v.startswith("SeverityEnum."):
                v = v.replace("SeverityEnum.", "")
            return SeverityEnum(v.lower())
        return v



class Booking(BaseMind):
    """Booking Mind type for booking working hours TO task FOR resource.

    Extends BaseMind with booking-specific attributes including hours worked,
    booking date, hourly rate at time of booking, and computed amount.

    Attributes:
        hours_worked: Hours worked (must be >= 0)
        booking_date: Optional date of the booking
        rate: Optional hourly rate at time of booking
        amount: Optional computed amount (hours × rate)

    **Validates: Requirements 9.2, 9.5**
    """

    __primarylabel__: str = "Booking"

    hours_worked: float = Field(
        ..., ge=0.0, description="Hours worked"
    )
    booking_date: Optional[date] = Field(
        default=None, description="Date of the booking"
    )
    rate: Optional[float] = Field(
        default=None, ge=0.0, description="Hourly rate at time of booking"
    )
    amount: Optional[float] = Field(
        default=None, ge=0.0, description="Computed amount (hours × rate)"
    )

class Sprint(BaseMind):
    """Sprint Mind type for agile iteration tracking.

    Extends BaseMind with sprint-specific attributes including sprint number,
    date range, optional goal, and velocity.

    **Validates: Requirements 9.1, 9.3**
    """

    __primarylabel__: str = "Sprint"

    sprint_number: int = Field(
        ..., ge=1, description="Sprint number"
    )
    start_date: date = Field(
        ..., description="Sprint start date"
    )
    end_date: date = Field(
        ..., description="Sprint end date"
    )
    goal: Optional[str] = Field(
        default=None, max_length=500, description="Sprint goal"
    )
    velocity: Optional[float] = Field(
        default=None, ge=0.0, description="Sprint velocity in story points or hours"
    )

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        """Validate that end_date is after start_date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v




class Account(BaseMind):
    """Account Mind type for cost/revenue tracking."""

    __primarylabel__: str = "Account"

    account_type: AccountType = Field(
        default=AccountType.COST, description="Type of account (COST or REVENUE)"
    )


    @field_serializer('account_type')
    def serialize_account_type(self, account_type: AccountType, _info):
        """Serialize AccountType enum to its value."""
        if isinstance(account_type, AccountType):
            return account_type.value
        return account_type

    @field_validator('account_type', mode='before')
    @classmethod
    def validate_account_type(cls, v):
        """Validate and normalize account_type from various formats."""
        if isinstance(v, AccountType):
            return v
        if isinstance(v, str):
            if v.startswith("AccountType."):
                v = v.replace("AccountType.", "")
            return AccountType(v.upper())
        return v



class ScheduleHistory(BaseMind):
    """Schedule History node for version tracking."""

    __primarylabel__: str = "ScheduleHistory"

    schedule_id: str = Field(..., min_length=1, description="Unique schedule identifier")
    scheduled_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this schedule was computed",
    )
    status: StatusEnum = Field(default=StatusEnum.DONE, description="Schedule status")
    
    total_effort: Optional[float] = Field(default=None, ge=0.0, description="Total work effort")
    total_cost: Optional[float] = Field(default=None, ge=0.0, description="Total project cost")
    global_start: Optional[datetime] = Field(default=None, description="First task start date")
    global_end: Optional[datetime] = Field(default=None, description="Last task end date")


    @field_serializer('status')
    def serialize_status(self, status: StatusEnum, _info):
        """Serialize StatusEnum to its value."""
        if isinstance(status, StatusEnum):
            return status.value
        return status

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Validate and normalize status from various formats."""
        if isinstance(v, StatusEnum):
            return v
        if isinstance(v, str):
            if v.startswith("StatusEnum."):
                v = v.replace("StatusEnum.", "")
            return StatusEnum(v.lower())
        return v



class ScheduledTask(BaseMind):
    """Scheduled Task node with CPM-computed values."""

    __primarylabel__: str = "ScheduledTask"

    source_task_uuid: UUID = Field(..., description="UUID of the source INPUT Task")
    scheduled_start: datetime = Field(..., description="Calculated start date")
    scheduled_end: datetime = Field(..., description="Calculated end date")
    scheduled_duration: Optional[float] = Field(
        default=None, ge=0.0, description="Work duration in days"
    )
    scheduled_length: Optional[float] = Field(
        default=None, ge=0.0, description="Calendar length in days"
    )
    is_critical: bool = Field(default=False, description="On critical path?")
    slack_start: Optional[float] = Field(default=None, description="Float before start")
    slack_end: Optional[float] = Field(default=None, description="Float before end")
    base_cost: Optional[float] = Field(default=None, ge=0.0, description="Base cost")
    variable_cost: Optional[float] = Field(
        default=None, ge=0.0, description="Variable cost (resources)"
    )
    total_cost: Optional[float] = Field(default=None, ge=0.0, description="Total cost")

    @field_serializer('source_task_uuid')
    def serialize_source_task_uuid(self, uuid: UUID, _info) -> str:
        """Serialize source_task_uuid to string for Neo4j compatibility."""
        return str(uuid)
