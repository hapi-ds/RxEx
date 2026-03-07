"""Property-based tests for Mind system.

Tests verify universal properties of the Mind-based data model system.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.enums import StatusEnum
from src.models.mind import BaseMind


class TestBaseMindProperties:
    """Test BaseMind universal properties."""

    def test_initial_version_is_one(self):
        """
        Property 2: Initial Version Number

        For any newly created Mind node, the version number shall be
        initialized to 1.
        """
        mind = BaseMind(
            title="Test Mind",
            creator="test@example.com"
        )
        assert mind.version == 1

    def test_timestamp_set_to_current_time(self):
        """
        Property 3: Creation Timestamp Accuracy

        For any newly created Mind node, the update timestamp shall be set
        to the current time.
        """
        before = datetime.now(timezone.utc)
        mind = BaseMind(
            title="Test Mind",
            creator="test@example.com"
        )
        after = datetime.now(timezone.utc)

        assert mind.updated_at >= before
        assert mind.updated_at <= after

    @pytest.mark.parametrize("valid_status", [s.value for s in StatusEnum])
    def test_valid_status_values_accepted(self, valid_status):
        """
        Property 4: Status Enumeration Validation (Valid Values)

        For any Mind node creation request with a valid status value,
        the system shall accept the request.
        """
        mind = BaseMind(
            title="Test Mind",
            creator="test@example.com",
            status=valid_status
        )
        assert mind.status == StatusEnum(valid_status)

    def test_invalid_status_values_rejected(self):
        """
        Property 4: Status Enumeration Validation (Invalid Values)

        For any Mind node creation request with an invalid status value,
        the system shall reject the request.
        """
        with pytest.raises((ValidationError, ValueError)):
            BaseMind(
                title="Test Mind",
                creator="test@example.com",
                status="invalid_status"  # ty: ignore[invalid-argument-type]
            )

    def test_combined_properties_hold_simultaneously(self):
        """
        Combined Property Test: All base properties hold simultaneously.

        For any newly created Mind node:
        - Version shall be 1
        - Timestamp shall be current
        - Status shall be valid enum value
        """
        mind = BaseMind(
            title="Complete Mind",
            creator="user@example.com",
            description="Full description",
            status=StatusEnum.DONE
        )

        assert mind.version == 1
        assert isinstance(mind.updated_at, datetime)
        assert mind.status == StatusEnum.DONE
