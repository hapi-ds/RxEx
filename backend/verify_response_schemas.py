#!/usr/bin/env python3
"""
Verification script for response schemas.

This script validates that all response schemas can be instantiated correctly
and that their validation rules work as expected.
"""

from datetime import datetime
from uuid import uuid4

from src.models.enums import StatusEnum
from src.schemas.minds import (
    ErrorResponse,
    MindResponse,
    QueryResult,
    RelationshipResponse,
)


def test_mind_response():
    """Test MindResponse schema."""
    print("Testing MindResponse...")

    test_uuid = uuid4()
    response = MindResponse(
        uuid=test_uuid,
        mind_type="project",
        title="Test Project",
        version=1,
        updated_at=datetime(2024, 1, 15, 10, 30, 0),
        creator="user@example.com",
        status=StatusEnum.DONE,
        description="Test description",
        type_specific_attributes={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 50000.0,
        },
    )

    assert response.uuid == test_uuid
    assert response.mind_type == "project"
    assert response.title == "Test Project"
    assert response.version == 1
    assert response.status == StatusEnum.DONE
    print("✓ MindResponse works correctly")


def test_query_result():
    """Test QueryResult schema."""
    print("Testing QueryResult...")

    mind_response = MindResponse(
        uuid=uuid4(),
        mind_type="project",
        title="Test Project",
        version=1,
        updated_at=datetime.now(),
        creator="user@example.com",
        status=StatusEnum.DONE,
        type_specific_attributes={},
    )

    result = QueryResult(items=[mind_response], total=42, page=1, page_size=20, total_pages=3)

    assert len(result.items) == 1
    assert result.total == 42
    assert result.page == 1
    assert result.page_size == 20
    assert result.total_pages == 3
    print("✓ QueryResult works correctly")


def test_error_response():
    """Test ErrorResponse schema."""
    print("Testing ErrorResponse...")

    error = ErrorResponse(
        request_id="req_abc123",
        error_type="ValidationError",
        message="Invalid input data",
        details={"field": "start_date", "error": "start_date must be before end_date"},
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
    )

    assert error.request_id == "req_abc123"
    assert error.error_type == "ValidationError"
    assert error.message == "Invalid input data"
    assert error.details is not None
    assert error.details["field"] == "start_date"
    print("✓ ErrorResponse works correctly")


def test_relationship_response():
    """Test RelationshipResponse schema."""
    print("Testing RelationshipResponse...")

    source_uuid = uuid4()
    target_uuid = uuid4()

    relationship = RelationshipResponse(
        relationship_type="contains",
        source_uuid=source_uuid,
        target_uuid=target_uuid,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        properties={"weight": 1.0, "notes": "Primary dependency"},
    )

    assert relationship.relationship_type == "contains"
    assert relationship.source_uuid == source_uuid
    assert relationship.target_uuid == target_uuid
    assert relationship.properties is not None
    assert relationship.properties["weight"] == 1.0
    print("✓ RelationshipResponse works correctly")


def test_all_relationship_types():
    """Test all valid relationship types."""
    print("Testing all relationship types...")

    valid_types = ["contains", "depends_on", "assigned_to", "relates_to", "implements", "mitigates"]

    for rel_type in valid_types:
        relationship = RelationshipResponse(
            relationship_type=rel_type,
            source_uuid=uuid4(),
            target_uuid=uuid4(),
            created_at=datetime.now(),
        )
        assert relationship.relationship_type == rel_type

    print(f"✓ All {len(valid_types)} relationship types validated")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Response Schema Verification")
    print("=" * 60)
    print()

    try:
        test_mind_response()
        test_query_result()
        test_error_response()
        test_relationship_response()
        test_all_relationship_types()

        print()
        print("=" * 60)
        print("✓ All response schemas verified successfully!")
        print("=" * 60)
        return 0
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Verification failed: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
