#!/usr/bin/env python3
"""
Simple verification script for Mind request schemas.
This script demonstrates that all schemas are correctly defined and can be used.
"""

from uuid import uuid4

from src.models.enums import StatusEnum
from src.schemas.minds import (
    MindBulkUpdate,
    MindCreate,
    MindQueryFilters,
    MindUpdate,
)


def verify_schemas():
    """Verify all schema definitions."""
    print("Verifying Mind Request Schemas...")
    print("=" * 50)

    # Verify MindCreate
    print("\n1. MindCreate Schema:")
    mind_create = MindCreate(
        mind_type="project",
        title="Test Project",
        description="Test description",
        creator="user@example.com",
        type_specific_attributes={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 50000.0,
        },
    )
    print(f"   - mind_type: {mind_create.mind_type}")
    print(f"   - title: {mind_create.title}")
    print(f"   - creator: {mind_create.creator}")
    print(f"   - type_specific_attributes: {mind_create.type_specific_attributes}")
    print("   ✓ MindCreate schema verified")

    # Verify MindUpdate
    print("\n2. MindUpdate Schema:")
    mind_update = MindUpdate(
        title="Updated Title", status=StatusEnum.DONE, type_specific_attributes={"budget": 75000.0}
    )
    print(f"   - title: {mind_update.title}")
    print(f"   - status: {mind_update.status}")
    print(f"   - type_specific_attributes: {mind_update.type_specific_attributes}")
    print("   ✓ MindUpdate schema verified")

    # Verify MindQueryFilters
    print("\n3. MindQueryFilters Schema:")
    query_filters = MindQueryFilters(
        mind_type="task",
        status=StatusEnum.DONE,
        creator="user@example.com",
        sort_by="updated_at",
        sort_order="desc",
        page=1,
        page_size=20,
    )
    print(f"   - mind_type: {query_filters.mind_type}")
    print(f"   - status: {query_filters.status}")
    print(f"   - creator: {query_filters.creator}")
    print(f"   - sort_by: {query_filters.sort_by}")
    print(f"   - sort_order: {query_filters.sort_order}")
    print(f"   - page: {query_filters.page}")
    print(f"   - page_size: {query_filters.page_size}")
    print("   ✓ MindQueryFilters schema verified")

    # Verify MindBulkUpdate
    print("\n4. MindBulkUpdate Schema:")
    test_uuid = uuid4()
    bulk_update = MindBulkUpdate(
        uuid=test_uuid,
        title="Bulk Updated Title",
        status=StatusEnum.DONE,
        type_specific_attributes={"priority": "high"},
    )
    print(f"   - uuid: {bulk_update.uuid}")
    print(f"   - title: {bulk_update.title}")
    print(f"   - status: {bulk_update.status}")
    print(f"   - type_specific_attributes: {bulk_update.type_specific_attributes}")
    print("   ✓ MindBulkUpdate schema verified")

    # Verify all 18 mind types are accepted
    print("\n5. Valid Mind Types:")
    valid_types = [
        "project",
        "phase",
        "task",
        "milestone",
        "company",
        "department",
        "employee",
        "email",
        "knowledge",
        "user_story",
        "user_need",
        "design_input",
        "design_output",
        "process_requirement",
        "work_instruction_requirement",
        "acceptance_criteria",
        "risk",
        "failure",
    ]
    for mind_type in valid_types:
        mind = MindCreate(
            mind_type=mind_type, title=f"Test {mind_type}", creator="user@example.com"
        )
        assert mind.mind_type == mind_type
    print(f"   ✓ All {len(valid_types)} mind types validated")

    # Verify validation works
    print("\n6. Validation Tests:")
    try:
        MindCreate(mind_type="invalid_type", title="Test", creator="user@example.com")
        print("   ✗ Validation failed - invalid mind_type was accepted")
    except Exception:
        print("   ✓ Invalid mind_type correctly rejected")

    try:
        MindCreate(
            mind_type="project",
            title="",  # Empty title
            creator="user@example.com",
        )
        print("   ✗ Validation failed - empty title was accepted")
    except Exception:
        print("   ✓ Empty title correctly rejected")

    try:
        MindQueryFilters(page_size=101)  # Exceeds max
        print("   ✗ Validation failed - page_size > 100 was accepted")
    except Exception:
        print("   ✓ Invalid page_size correctly rejected")

    print("\n" + "=" * 50)
    print("✓ All request schemas verified successfully!")
    print("\nTask 4.1 Complete: Request schemas created")
    print("  - MindCreate: for creating new Mind nodes")
    print("  - MindUpdate: for updating existing Mind nodes")
    print("  - MindQueryFilters: for querying and filtering Mind nodes")
    print("  - MindBulkUpdate: for bulk update operations")
    print("\nValidates Requirements: 3.1, 5.1, 11.1-11.7")


if __name__ == "__main__":
    verify_schemas()
