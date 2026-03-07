#!/usr/bin/env python
"""
Verification script for derived Mind types.

This script verifies that all derived Mind types can be instantiated
correctly with valid data.
"""

from datetime import date

from src.models.enums import PriorityEnum
from src.models.mind_types import (
    Milestone,
    Phase,
    Project,
    Task,
)


def verify_project():
    """Verify Project type can be instantiated."""
    project = Project(
        title="Test Project",
        creator="test@example.com",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        budget=50000.0
    )
    print(f"✓ Project created: {project.title}")
    print(f"  - UUID: {project.uuid}")
    print(f"  - Version: {project.version}")
    print(f"  - Start: {project.start_date}, End: {project.end_date}")
    print(f"  - Budget: ${project.budget}")
    return project


def verify_phase():
    """Verify Phase type can be instantiated."""
    phase = Phase(
        title="Phase 1: Planning",
        creator="test@example.com",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        phase_number=1
    )
    print(f"✓ Phase created: {phase.title}")
    print(f"  - UUID: {phase.uuid}")
    print(f"  - Phase Number: {phase.phase_number}")
    print(f"  - Start: {phase.start_date}, End: {phase.end_date}")
    return phase


def verify_task():
    """Verify Task type can be instantiated."""
    task = Task(
        title="Implement authentication",
        creator="test@example.com",
        priority=PriorityEnum.HIGH,
        assignee="dev@example.com",
        due_date=date(2024, 2, 15),
        estimated_hours=8.0
    )
    print(f"✓ Task created: {task.title}")
    print(f"  - UUID: {task.uuid}")
    print(f"  - Priority: {task.priority.value}")
    print(f"  - Assignee: {task.assignee}")
    print(f"  - Due: {task.due_date}, Estimated: {task.estimated_hours}h")
    return task


def verify_milestone():
    """Verify Milestone type can be instantiated."""
    milestone = Milestone(
        title="Project Kickoff",
        creator="test@example.com",
        target_date=date(2024, 1, 15),
        completion_percentage=100.0
    )
    print(f"✓ Milestone created: {milestone.title}")
    print(f"  - UUID: {milestone.uuid}")
    print(f"  - Target: {milestone.target_date}")
    print(f"  - Completion: {milestone.completion_percentage}%")
    return milestone


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Verifying Derived Mind Types (Task 3.1)")
    print("=" * 60)
    print()

    try:
        project = verify_project()
        print()

        phase = verify_phase()
        print()

        task = verify_task()
        print()

        milestone = verify_milestone()
        print()

        print("=" * 60)
        print("✓ All derived Mind types verified successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  - Project: {project.__class__.__name__} with primary label '{Project.__primarylabel__}'")
        print(f"  - Phase: {phase.__class__.__name__} with primary label '{Phase.__primarylabel__}'")
        print(f"  - Task: {task.__class__.__name__} with primary label '{Task.__primarylabel__}'")
        print(f"  - Milestone: {milestone.__class__.__name__} with primary label '{Milestone.__primarylabel__}'")
        print()
        print("All types inherit from BaseMind and include:")
        print("  - uuid, title, version, updated_at, creator, status, description")
        print()

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
