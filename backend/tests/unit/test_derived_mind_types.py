"""Unit tests for derived Mind types.

Tests validate all 18 specialized Mind types.
"""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.models.enums import (
    PriorityEnum,
    ProbabilityEnum,
    SeverityEnum,
    StatusEnum,
    RequirementType,
    ResourceType,
)
from src.models.mind_types import (
    AcceptanceCriteria,
    Company,
    Department,
    Email,
    Failure,
    Knowledge,
    Project,
    Risk,
    Task,
    Requirement,
    Resource,
)


class TestProject:
    """Test Project mind type."""

    def test_valid_project(self):
        """Test that a valid Project can be created."""
        project = Project(
            title="Test Project",
            creator="test@example.com",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            budget=50000.0,
        )

        assert project.title == "Test Project"
        assert project.start_date == date(2024, 1, 1)
        assert project.end_date == date(2024, 12, 31)
        assert project.budget == 50000.0

    def test_project_without_budget(self):
        """Test that Project can be created without budget."""
        project = Project(
            title="Project Without Budget",
            creator="test@example.com",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        assert project.budget is None


class TestTask:
    """Test Task mind type."""

    def test_valid_task(self):
        """Test that a valid Task can be created."""
        task = Task(
            title="Test Task",
            creator="test@example.com",
            priority=PriorityEnum.HIGH,
        )

        assert task.title == "Test Task"
        assert task.priority == PriorityEnum.HIGH

    def test_task_with_due_date(self):
        """Test that Task can be created with due date."""
        task = Task(
            title="Task With Due Date",
            creator="test@example.com",
            priority=PriorityEnum.CRITICAL,
            due_date=date(2024, 6, 30),
        )

        assert task.due_date == date(2024, 6, 30)

    def test_task_invalid_priority(self):
        """Test that invalid priority raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="Test Task",
                creator="test@example.com",
                priority="invalid_priority",  # type: ignore[call-arg]
            )

        errors = exc_info.value.errors()
        # Custom validator raises value_error instead of enum
        assert any(e["type"] in ("enum", "value_error") for e in errors)
        assert any("priority" in str(e.get("loc", "")) for e in errors)


class TestRisk:
    """Test Risk mind type."""

    def test_valid_risk_with_integer_severity(self):
        """Test that a valid Risk can be created with integer severity."""
        risk = Risk(
            title="Technical Risk",
            creator="test@example.com",
            severity=7,
            probability=ProbabilityEnum.LIKELY,
        )

        assert risk.title == "Technical Risk"
        assert risk.severity == 7
        assert risk.probability == ProbabilityEnum.LIKELY

    def test_risk_backward_compat_enum_string(self):
        """Test that old SeverityEnum string values are mapped to integers."""
        risk = Risk(
            title="Technical Risk",
            creator="test@example.com",
            severity="high",
            probability=ProbabilityEnum.LIKELY,
        )

        assert risk.severity == 7

    def test_risk_with_mitigation(self):
        """Test that Risk can be created with mitigation plan."""
        risk = Risk(
            title="Risk With Mitigation",
            creator="test@example.com",
            severity=5,
            probability=ProbabilityEnum.UNLIKELY,
            mitigation_plan="Monitor and review regularly",
        )

        assert risk.mitigation_plan == "Monitor and review regularly"

    def test_risk_acceptable_limit_default_null(self):
        """Test that Risk created without acceptable_limit stores it as null."""
        risk = Risk(
            title="Risk Without Limit",
            creator="test@example.com",
            severity=3,
            probability=ProbabilityEnum.RARE,
        )

        assert risk.acceptable_limit is None

    def test_risk_with_acceptable_limit(self):
        """Test that Risk can be created with acceptable_limit."""
        risk = Risk(
            title="Risk With Limit",
            creator="test@example.com",
            severity=4,
            probability=ProbabilityEnum.POSSIBLE,
            acceptable_limit="RPN < 100",
        )

        assert risk.acceptable_limit == "RPN < 100"

    def test_risk_severity_out_of_range(self):
        """Test that severity outside 1-10 raises ValidationError."""
        with pytest.raises(ValidationError):
            Risk(
                title="Bad Risk",
                creator="test@example.com",
                severity=0,
                probability=ProbabilityEnum.LIKELY,
            )
        with pytest.raises(ValidationError):
            Risk(
                title="Bad Risk",
                creator="test@example.com",
                severity=11,
                probability=ProbabilityEnum.LIKELY,
            )


class TestFailure:
    """Test Failure mind type."""

    def test_failure_with_minimal_data(self):
        """Test that Failure can be created with minimal data (only title, creator)."""
        failure = Failure(
            title="Test Failure",
            creator="test@example.com",
        )

        assert failure.occurrence is None
        assert failure.detectability is None

    def test_failure_with_valid_occurrence_detectability(self):
        """Test that Failure can be created with valid occurrence/detectability values."""
        failure = Failure(
            title="Test Failure",
            creator="test@example.com",
            occurrence=5,
            detectability=3,
        )

        assert failure.occurrence == 5
        assert failure.detectability == 3

    def test_failure_occurrence_out_of_range(self):
        """Test that occurrence outside 1-10 raises ValidationError."""
        with pytest.raises(ValidationError):
            Failure(
                title="Bad Failure",
                creator="test@example.com",
                occurrence=0,
            )
        with pytest.raises(ValidationError):
            Failure(
                title="Bad Failure",
                creator="test@example.com",
                occurrence=11,
            )

    def test_failure_detectability_out_of_range(self):
        """Test that detectability outside 1-10 raises ValidationError."""
        with pytest.raises(ValidationError):
            Failure(
                title="Bad Failure",
                creator="test@example.com",
                detectability=0,
            )
        with pytest.raises(ValidationError):
            Failure(
                title="Bad Failure",
                creator="test@example.com",
                detectability=11,
            )


class TestRequirement:
    """Test Requirement mind type (consolidated from multiple requirement types)."""

    def test_valid_work_instruction_requirement(self):
        """Test that a valid WorkInstructionRequirement can be created using Requirement."""
        instruction = Requirement(
            title="Safety Procedure",
            creator="test@example.com",
            requirement_type="WORK_INSTRUCTION_REQUIREMENT",
            content="Follow safety checklist before operation",
            safety_critical=True,
        )

        assert instruction.requirement_type.value == "WORK_INSTRUCTION_REQUIREMENT"
        assert instruction.content == "Follow safety checklist before operation"
        assert instruction.safety_critical is True
