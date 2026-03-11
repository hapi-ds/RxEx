"""Integration tests for schema validations.

**Validates: Requirements 3.1, 5.1, 8.4**
"""

from datetime import datetime
from uuid import UUID

from src.models.enums import StatusEnum
from src.schemas.minds import (
    MindBulkUpdate,
    MindCreate,
    MindResponse,
)


class TestSchemaValidations:
    """Integration tests for schema validation edge cases."""

    def test_mind_create_with_all_valid_types(self):
        """Test that all valid mind types can be created."""
        valid_types = [
            "project", "task", "company", "department",
            "resource", "email", "knowledge", "requirement",
            "acceptance_criteria", "risk", "failure", "account",
            "schedulehistory", "scheduledtask"
        ]

        for mind_type in valid_types:
            mind = MindCreate(
                mind_type=mind_type,
                title=f"Test {mind_type}",
                creator="user@example.com"
            )
            assert mind.mind_type == mind_type

    def test_mind_response_with_all_fields(self):
        """Test that MindResponse handles all fields correctly."""
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")

        response = MindResponse(
            uuid=test_uuid,
            mind_type="project",
            title="Full Project",
            version=3,
            updated_at=datetime(2024, 1, 15, 10, 30, 0),
            creator="user@example.com",
            status=StatusEnum.DONE,
            description="Complete project details",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "budget": 75000.0
            }
        )

        assert response.uuid == test_uuid
        assert response.version == 3

    def test_bulk_update_with_various_fields(self):
        """Test bulk update with various field combinations."""
        uuid = UUID("660e8400-e29b-41d4-a716-446655440001")

        update1 = MindBulkUpdate(
            uuid=uuid,
            title="Updated Title",
            type_specific_attributes={"priority": "high"}
        )

        assert update1.title == "Updated Title"

    def test_query_filters_with_complex_combinations(self):
        """Test query filters with complex filter combinations."""
        from src.schemas.minds import MindQueryFilters

        filters = MindQueryFilters(
            mind_type="task",
            status=StatusEnum.DONE,
            creator="user@example.com",
            sort_by="updated_at",
            sort_order="desc",
            page=5,
            page_size=25
        )

        assert filters.mind_type == "task"
        assert filters.status == StatusEnum.DONE
