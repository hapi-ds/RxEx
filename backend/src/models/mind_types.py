"""
Derived Mind types for the Mind-Based Data Model System.

This module defines specialized Mind node types that extend BaseMind with
type-specific attributes. Each derived type inherits all base attributes
(uuid, title, version, updated_at, creator, status, description) and adds
its own specialized fields.

**Validates: Requirements 2.1, 2.2, 2.3, 9.1, 9.2, 9.3, 9.4**
"""

from datetime import date, datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from .enums import PriorityEnum, ProbabilityEnum, SeverityEnum
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


class Phase(BaseMind):
    """
    Phase Mind type representing a stage within a project or process.

    Extends BaseMind with phase-specific attributes including start/end dates
    and sequential phase numbering.

    Attributes:
        start_date: Phase start date
        end_date: Phase end date (must be after start_date)
        phase_number: Sequential phase number (1-based)

    **Validates: Requirements 2.1, 2.2, 2.3, 9.1**
    """

    __primarylabel__: str = "Phase"

    start_date: date = Field(
        ...,
        description="Phase start date"
    )
    end_date: date = Field(
        ...,
        description="Phase end date"
    )
    phase_number: int = Field(
        ...,
        ge=1,
        description="Sequential phase number"
    )

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        """Validate that end_date is after start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class Task(BaseMind):
    """
    Task Mind type representing a work item with priority and assignment.

    Extends BaseMind with task-specific attributes including priority level,
    assignee, optional due date, and estimated effort.

    Attributes:
        priority: Task priority level (low, medium, high, critical)
        assignee: User identifier of the person assigned to the task
        due_date: Optional due date for task completion
        estimated_hours: Optional estimated effort in hours

    **Validates: Requirements 2.1, 2.2, 2.3, 9.2**
    """

    __primarylabel__: str = "Task"

    priority: PriorityEnum = Field(
        ...,
        description="Task priority level"
    )
    assignee: str = Field(
        ...,
        min_length=1,
        description="User identifier of the person assigned to the task"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Optional due date for task completion"
    )
    estimated_hours: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional estimated effort in hours"
    )


class Milestone(BaseMind):
    """
    Milestone Mind type representing a significant project checkpoint.

    Extends BaseMind with milestone-specific attributes including target date
    and completion tracking.

    Attributes:
        target_date: Target date for milestone achievement
        completion_percentage: Completion percentage (0-100)

    **Validates: Requirements 2.1, 2.2, 2.3, 9.1**
    """

    __primarylabel__: str = "Milestone"

    target_date: date = Field(
        ...,
        description="Target date for milestone achievement"
    )
    completion_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Completion percentage (0-100)"
    )


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


class Employee(BaseMind):
    """
    Employee Mind type representing a person in an organization.

    Extends BaseMind with employee-specific attributes including email,
    role, hire date, and optional department association.

    Attributes:
        email: Employee email address
        role: Job role or title
        hire_date: Date of employment start
        department_id: Optional department identifier

    **Validates: Requirements 2.1, 2.2, 2.3, 9.3**
    """

    __primarylabel__: str = "Employee"

    email: EmailStr = Field(
        ...,
        description="Employee email address"
    )
    role: str = Field(
        ...,
        min_length=1,
        description="Job role or title"
    )
    hire_date: date = Field(
        ...,
        description="Date of employment start"
    )
    department_id: Optional[str] = Field(
        default=None,
        description="Optional department identifier"
    )

    @field_validator("hire_date")
    @classmethod
    def validate_hire_date(cls, v: date) -> date:
        """Validate that hire_date is not in the future."""
        if v > date.today():
            raise ValueError("hire_date cannot be in the future")
        return v


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


class UserStory(BaseMind):
    """
    UserStory Mind type representing a user story in agile development.

    Extends BaseMind with user story-specific attributes following the
    "As a... I want... So that..." format, plus acceptance criteria references.

    Attributes:
        as_a: User role or persona
        i_want: Desired functionality or feature
        so_that: Business value or benefit
        acceptance_criteria_ids: List of acceptance criteria identifiers

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "UserStory"

    as_a: str = Field(
        ...,
        min_length=1,
        description="User role or persona"
    )
    i_want: str = Field(
        ...,
        min_length=1,
        description="Desired functionality or feature"
    )
    so_that: str = Field(
        ...,
        min_length=1,
        description="Business value or benefit"
    )
    acceptance_criteria_ids: list[str] = Field(
        default_factory=list,
        description="List of acceptance criteria identifiers"
    )


class UserNeed(BaseMind):
    """
    UserNeed Mind type representing a user requirement or need.

    Extends BaseMind with user need-specific attributes including need
    statement and priority level.

    Attributes:
        need_statement: Description of the user need
        priority: Priority level (low, medium, high, critical)

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "UserNeed"

    need_statement: str = Field(
        ...,
        min_length=1,
        description="Description of the user need"
    )
    priority: PriorityEnum = Field(
        ...,
        description="Priority level"
    )


class DesignInput(BaseMind):
    """
    DesignInput Mind type representing input to a design process.

    Extends BaseMind with design input-specific attributes including source,
    input type, and content.

    Attributes:
        source: Source of the design input
        input_type: Type or category of the input
        content: Design input content

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "DesignInput"

    source: str = Field(
        ...,
        min_length=1,
        description="Source of the design input"
    )
    input_type: str = Field(
        ...,
        min_length=1,
        description="Type or category of the input"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Design input content"
    )


class DesignOutput(BaseMind):
    """
    DesignOutput Mind type representing output from a design process.

    Extends BaseMind with design output-specific attributes including output
    type, verification status, and content.

    Attributes:
        output_type: Type or category of the output
        verification_status: Verification or approval status
        content: Design output content

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "DesignOutput"

    output_type: str = Field(
        ...,
        min_length=1,
        description="Type or category of the output"
    )
    verification_status: str = Field(
        ...,
        min_length=1,
        description="Verification or approval status"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Design output content"
    )


class ProcessRequirement(BaseMind):
    """
    ProcessRequirement Mind type representing a process-level requirement.

    Extends BaseMind with process requirement-specific attributes including
    process name, requirement text, and optional compliance standard.

    Attributes:
        process_name: Name of the process
        requirement_text: Detailed requirement description
        compliance_standard: Optional compliance standard reference

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "ProcessRequirement"

    process_name: str = Field(
        ...,
        min_length=1,
        description="Name of the process"
    )
    requirement_text: str = Field(
        ...,
        min_length=1,
        description="Detailed requirement description"
    )
    compliance_standard: Optional[str] = Field(
        default=None,
        description="Optional compliance standard reference"
    )


class WorkInstructionRequirement(BaseMind):
    """
    WorkInstructionRequirement Mind type representing a work instruction.

    Extends BaseMind with work instruction-specific attributes including
    instruction ID, procedure, and safety criticality flag.

    Attributes:
        instruction_id: Unique instruction identifier
        procedure: Detailed procedure or instruction text
        safety_critical: Flag indicating if instruction is safety-critical

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    __primarylabel__: str = "WorkInstructionRequirement"

    instruction_id: str = Field(
        ...,
        min_length=1,
        description="Unique instruction identifier"
    )
    procedure: str = Field(
        ...,
        min_length=1,
        description="Detailed procedure or instruction text"
    )
    safety_critical: bool = Field(
        ...,
        description="Flag indicating if instruction is safety-critical"
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
