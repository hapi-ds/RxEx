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
            budget=50000.0
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
            end_date=date(2024, 12, 31)
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
            assignee="dev@example.com"
        )

        assert task.title == "Test Task"
        assert task.priority == PriorityEnum.HIGH
        assert task.assignee == "dev@example.com"

    def test_task_with_due_date(self):
        """Test that Task can be created with due date."""
        task = Task(
            title="Task With Due Date",
            creator="test@example.com",
            priority=PriorityEnum.CRITICAL,
            assignee="dev@example.com",
            due_date=date(2024, 6, 30),
            estimated_hours=40
        )

        assert task.due_date == date(2024, 6, 30)
        assert task.estimated_hours == 40

    def test_task_invalid_priority(self):
        """Test that invalid priority raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="Test Task",
                creator="test@example.com",
                assignee="dev@example.com",
                priority="invalid_priority"  # type: ignore[call-arg]
            )

        errors = exc_info.value.errors()
        assert any(e["type"] == "enum" for e in errors)


class TestRisk:
    """Test Risk mind type."""

    def test_valid_risk(self):
        """Test that a valid Risk can be created."""
        risk = Risk(
            title="Technical Risk",
            creator="test@example.com",
            severity=SeverityEnum.HIGH,
            probability=ProbabilityEnum.LIKELY
        )

        assert risk.title == "Technical Risk"
        assert risk.severity == SeverityEnum.HIGH
        assert risk.probability == ProbabilityEnum.LIKELY

    def test_risk_with_mitigation(self):
        """Test that Risk can be created with mitigation plan."""
        risk = Risk(
            title="Risk With Mitigation",
            creator="test@example.com",
            severity=SeverityEnum.MEDIUM,
            probability=ProbabilityEnum.UNLIKELY,
            mitigation_plan="Monitor and review regularly"
        )

        assert risk.mitigation_plan == "Monitor and review regularly"







class TestRequirement:
    """Test Requirement mind type (consolidated from multiple requirement types)."""

    def test_valid_work_instruction_requirement(self):
        """Test that a valid WorkInstructionRequirement can be created using Requirement."""
        instruction = Requirement(
            title="Safety Procedure",
            creator="test@example.com",
            requirement_type=RequirementType.WORK_INSTRUCTION_REQUIREMENT,
            content="Follow safety checklist before operation",
            safety_critical=True
        )

        assert instruction.requirement_type == RequirementType.WORK_INSTRUCTION_REQUIREMENT
        assert instruction.content == "Follow safety checklist before operation"
        assert instruction.safety_critical is True
