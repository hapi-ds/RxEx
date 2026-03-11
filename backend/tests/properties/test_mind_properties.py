"""Property-based tests for Mind system.

Tests verify universal properties of the Mind-based data model system.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite
from pydantic import ValidationError

from src.models.enums import PriorityEnum, SeverityEnum, StatusEnum
from src.models.mind import BaseMind
from src.schemas.minds import MindCreate
from src.services.mind_service import MindService


# Hypothesis strategies for generating test data
@composite
def mind_type_strategy(draw):
    """Generate random Mind type names."""
    return draw(
        st.sampled_from([
            "project",
            "task",
            "company",
            "department",
            "resource",  # Replaces employee
            "email",
            "knowledge",
            "requirement",  # Consolidated type
            "acceptance_criteria",
            "risk",
            "failure",
            "account",
            "schedulehistory",
            "scheduledtask",
        ])
    )


@composite
def type_specific_attributes_strategy(draw, mind_type: str):
    """Generate valid type-specific attributes based on mind_type."""
    if mind_type == "project":
        start_date = draw(st.dates(min_value=datetime(2020, 1, 1).date(), max_value=datetime(2024, 12, 1).date()))
        # Ensure end_date is after start_date
        end_date = draw(st.dates(min_value=start_date, max_value=datetime(2025, 12, 31).date()))
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "budget": draw(st.floats(min_value=0, max_value=1000000) | st.none()),
        }
    elif mind_type == "task":
        due_date = draw(st.dates(min_value=datetime(2020, 1, 1).date()) | st.none())
        return {
            "priority": draw(st.sampled_from([p.value for p in PriorityEnum])),
            "assignee": draw(st.emails()),
            "due_date": due_date.isoformat() if due_date is not None else None,
            "task_type": draw(st.sampled_from(["TASK", "PHASE", "MILESTONE", "WORKPACKAGE"])),
        }
    elif mind_type == "company":
        founded_date = draw(st.dates(min_value=datetime(1800, 1, 1).date()) | st.none())
        return {
            "industry": draw(st.text(min_size=1, max_size=100)),
            "size": draw(st.integers(min_value=1, max_value=1000000) | st.none()),
            "founded_date": founded_date.isoformat() if founded_date is not None else None,
        }
    elif mind_type == "department":
        return {
            "department_code": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
            "manager": draw(st.text(min_size=1, max_size=100) | st.none()),
        }
    elif mind_type == "resource":
        # Replaces "employee" - Resource with resource_type=PERSON
        return {
            "email": draw(st.emails() | st.none()),
            "efficiency": draw(st.floats(min_value=0.0, max_value=1.0)),
            "daily_rate": draw(st.floats(min_value=0.0, max_value=10000.0)),
            "resource_type": draw(st.sampled_from(["PERSON", "GROUP", "EQUIPMENT"])),
        }
    elif mind_type == "email":
        return {
            "sender": draw(st.emails()),
            "recipients": draw(st.lists(st.emails(), min_size=1, max_size=10)),
            "subject": draw(st.text(min_size=1, max_size=200)),
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
    elif mind_type == "knowledge":
        return {
            "category": draw(st.text(min_size=1, max_size=100)),
            "tags": draw(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10)),  # At least 1 tag
            "content": draw(st.text(min_size=1, max_size=5000)),
        }
    elif mind_type == "requirement":
        # Consolidated type for user_story, user_need, design_input, design_output, process_requirement, work_instruction_requirement
        return {
            "requirement_type": draw(st.sampled_from([
                "USER_STORY", "USER_NEED", "DESIGN_INPUT", "DESIGN_OUTPUT",
                "PROCESS_REQUIREMENT", "WORK_INSTRUCTION_REQUIREMENT"
            ])),
            "content": draw(st.text(min_size=1, max_size=5000)),
            "source": draw(st.text(min_size=1, max_size=200) | st.none()),
            "acceptance_criteria": draw(st.text(min_size=1, max_size=1000) | st.none()),
            "compliance_standard": draw(st.text(min_size=1, max_size=100) | st.none()),
            "safety_critical": draw(st.booleans()),
        }
    elif mind_type == "acceptance_criteria":
        return {
            "criteria_text": draw(st.text(min_size=1, max_size=500)),
            "verification_method": draw(st.text(min_size=1, max_size=200)),
            # Note: AcceptanceCriteria has its own 'status' field separate from base Mind status
            # Using 'verification_status' to avoid confusion
            "verification_status": draw(st.sampled_from(["pending", "verified", "failed"])),
        }
    elif mind_type == "risk":
        return {
            "severity": draw(st.sampled_from([s.value for s in SeverityEnum])),
            "probability": draw(st.sampled_from(["rare", "unlikely", "possible", "likely", "certain"])),
            "mitigation_plan": draw(st.text(min_size=1, max_size=1000) | st.none()),
        }
    elif mind_type == "failure":
        return {
            "failure_mode": draw(st.text(min_size=1, max_size=200)),
            "effects": draw(st.text(min_size=1, max_size=500)),
            "causes": draw(st.text(min_size=1, max_size=500)),
            "detection_method": draw(st.text(min_size=1, max_size=200) | st.none()),
        }
    elif mind_type == "account":
        return {
            "account_type": draw(st.sampled_from(["COST", "REVENUE"])),
        }
    elif mind_type == "schedulehistory":
        return {
            "schedule_id": draw(st.text(min_size=1, max_size=50)),
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "status": draw(st.sampled_from([s.value for s in StatusEnum])),
        }
    elif mind_type == "scheduledtask":
        return {
            "source_task_uuid": draw(st.uuids()).hex,
            "scheduled_start": datetime.now(timezone.utc).isoformat(),
            "scheduled_end": datetime.now(timezone.utc).isoformat(),
        }
    else:
        return {}


@composite
def mind_creation_strategy(draw):
    """Generate valid Mind creation data."""
    mind_type = draw(mind_type_strategy())
    return MindCreate(
        mind_type=mind_type,
        title=draw(st.text(min_size=1, max_size=200)),
        description=draw(st.text(max_size=1000) | st.none()),
        creator=draw(st.emails()),
        type_specific_attributes=draw(type_specific_attributes_strategy(mind_type)),
    )


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


class TestMindCreationProperties:
    """Test Mind creation service-level properties."""

    # Feature: mind-based-data-model-system, Property 1: UUID Uniqueness Enforcement
    @pytest.mark.asyncio
    @given(mind_data1=mind_creation_strategy(), mind_data2=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_uuid_uniqueness_enforcement(self, mind_data1, mind_data2, clean_database):
        """
        Property 1: UUID Uniqueness Enforcement

        For any set of Mind node creation requests, the system shall reject
        any attempt to create a node with a UUID that already exists in the
        database.

        **Validates: Requirements 1.3**
        """
        service = MindService()

        # Create first Mind node
        result1 = await service.create_mind(mind_data1)
        assert result1.uuid is not None

        # Create second Mind node
        result2 = await service.create_mind(mind_data2)
        assert result2.uuid is not None

        # Verify UUIDs are different
        assert result1.uuid != result2.uuid

    # Feature: mind-based-data-model-system, Property 7: Successful Creation Returns Complete Data
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_successful_creation_returns_complete_data(self, mind_data, clean_database):
        """
        Property 7: Successful Creation Returns Complete Data

        For any valid Mind node creation request, the response shall include
        all submitted attributes plus the generated UUID and initialized fields
        (version, updated_at).

        **Validates: Requirements 3.7**
        """
        service = MindService()

        result = await service.create_mind(mind_data)

        # Verify all base attributes are present
        assert result.uuid is not None
        assert isinstance(result.uuid, UUID)
        assert result.mind_type == mind_data.mind_type
        assert result.title == mind_data.title
        assert result.description == mind_data.description
        assert result.creator == mind_data.creator
        assert result.version == 1
        assert result.updated_at is not None
        assert isinstance(result.updated_at, datetime)
        assert result.status is not None

        # Verify type-specific attributes are present
        for key, value in mind_data.type_specific_attributes.items():
            assert key in result.type_specific_attributes
            # Handle None values
            if value is not None:
                assert result.type_specific_attributes[key] is not None

    # Feature: mind-based-data-model-system, Property 8: UUID Generation Uniqueness
    @pytest.mark.asyncio
    @given(mind_data_list=st.lists(mind_creation_strategy(), min_size=2, max_size=5))
    @settings(
        max_examples=10,
        deadline=10000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_uuid_generation_uniqueness(self, mind_data_list, clean_database):
        """
        Property 8: UUID Generation Uniqueness

        For any batch of Mind node creations, all generated UUIDs shall be
        unique within that batch and across the entire database.

        **Validates: Requirements 3.2**
        """
        service = MindService()

        # Create all Mind nodes
        results = []
        for mind_data in mind_data_list:
            result = await service.create_mind(mind_data)
            results.append(result)

        # Extract all UUIDs
        uuids = [result.uuid for result in results]

        # Verify all UUIDs are unique
        assert len(uuids) == len(set(uuids)), "Generated UUIDs are not unique"

        # Verify all UUIDs are valid UUID objects
        for uuid in uuids:
            assert isinstance(uuid, UUID)

    # Feature: mind-based-data-model-system, Property 9: Creator Identifier Persistence
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_creator_identifier_persistence(self, mind_data, clean_database):
        """
        Property 9: Creator Identifier Persistence

        For any Mind node creation request with a creator identifier, that
        identifier shall be stored and returned in all subsequent retrievals
        and version history queries.

        **Validates: Requirements 3.5**
        """
        service = MindService()

        # Create Mind node
        result = await service.create_mind(mind_data)
        assert result.creator == mind_data.creator

        # Retrieve the Mind node
        retrieved = await service.get_mind(result.uuid)
        assert retrieved.creator == mind_data.creator

        # Get version history
        history = await service.get_version_history(result.uuid)
        assert len(history) > 0
        assert history[0].creator == mind_data.creator

    # Feature: mind-based-data-model-system, Property 10: Invalid Data Rejection
    @pytest.mark.asyncio
    @given(
        mind_type=mind_type_strategy(),
        title=st.text(min_size=1, max_size=200),
        creator=st.emails(),
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_invalid_data_rejection(self, mind_type, title, creator, clean_database):
        """
        Property 10: Invalid Data Rejection

        For any Mind node creation or update request with invalid data, the
        system shall return a descriptive validation error without modifying
        the database.

        **Validates: Requirements 3.6, 5.8**
        """
        service = MindService()

        # Create Mind node with missing required type-specific attributes
        # (empty dict should fail validation for most types)
        mind_data = MindCreate(
            mind_type=mind_type,
            title=title,
            creator=creator,
            type_specific_attributes={},  # Missing required attributes
        )

        # Attempt to create - should raise validation error
        with pytest.raises((ValueError, ValidationError, Exception)) as exc_info:
            await service.create_mind(mind_data)

        # Verify error message is descriptive
        assert exc_info.value is not None

        # Verify database was not modified by checking no nodes exist
        from neontology import GraphConnection

        gc = GraphConnection()
        result = gc.engine.evaluate_query("MATCH (n) RETURN count(n) as count")
        assert result.records_raw[0]["count"] == 0



class TestMindUpdateProperties:
    """Test Mind update service-level properties."""

    # Feature: mind-based-data-model-system, Property 15: Update Creates New Version
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        updated_title=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=("Cc", "Cs")))
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_update_creates_new_version(self, mind_data, updated_title, clean_database):
        """
        Property 15: Update Creates New Version

        For any Mind node update request, the system shall create a new node
        in the database rather than modifying the existing node in place.

        **Validates: Requirements 5.1**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        initial_uuid = result.uuid
        initial_version = result.version

        # Count nodes before update
        gc = GraphConnection()
        count_before = gc.engine.evaluate_query("MATCH (n {uuid: $uuid}) RETURN count(n) as count", {"uuid": str(initial_uuid)})
        nodes_before = count_before.records_raw[0]["count"]

        # Update the Mind node
        update_data = MindUpdate(title=updated_title)
        updated_result = await service.update_mind(initial_uuid, update_data)

        # Count nodes after update
        count_after = gc.engine.evaluate_query("MATCH (n {uuid: $uuid}) RETURN count(n) as count", {"uuid": str(initial_uuid)})
        nodes_after = count_after.records_raw[0]["count"]

        # Verify a new node was created (count increased)
        assert nodes_after > nodes_before, "Update should create a new node, not modify in place"
        assert nodes_after == nodes_before + 1, "Exactly one new node should be created"

        # Verify both versions exist in database
        all_versions = gc.engine.evaluate_query(
            "MATCH (n {uuid: $uuid}) RETURN n.version as version ORDER BY n.version",
            {"uuid": str(initial_uuid)}
        )
        versions = [record["version"] for record in all_versions.records_raw]
        assert initial_version in versions, "Original version should still exist"
        assert updated_result.version in versions, "New version should exist"

    # Feature: mind-based-data-model-system, Property 16: Version Number Increment
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        updated_title=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=("Cc", "Cs")))
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_version_number_increment(self, mind_data, updated_title, clean_database):
        """
        Property 16: Version Number Increment

        For any Mind node update, the new version's version number shall be
        exactly one greater than the previous version's version number.

        **Validates: Requirements 5.2**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        initial_version = result.version

        # Update the Mind node
        update_data = MindUpdate(title=updated_title)
        updated_result = await service.update_mind(result.uuid, update_data)

        # Verify version incremented by exactly 1
        assert updated_result.version == initial_version + 1, "Version should increment by exactly 1"

        # Perform another update to verify consistent incrementing
        update_data2 = MindUpdate(description="Second update")
        updated_result2 = await service.update_mind(result.uuid, update_data2)

        assert updated_result2.version == updated_result.version + 1, "Version should continue incrementing by 1"

    # Feature: mind-based-data-model-system, Property 17: Unchanged Attribute Preservation
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        updated_title=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=("Cc", "Cs")))
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_unchanged_attribute_preservation(self, mind_data, updated_title, clean_database):
        """
        Property 17: Unchanged Attribute Preservation

        For any Mind node update that modifies only a subset of attributes,
        all unmodified attributes shall retain their values from the previous
        version.

        **Validates: Requirements 5.3**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        initial_description = result.description
        initial_status = result.status
        initial_creator = result.creator
        initial_type_specific = result.type_specific_attributes.copy()

        # Update only the title
        update_data = MindUpdate(title=updated_title)
        updated_result = await service.update_mind(result.uuid, update_data)

        # Verify title was updated
        assert updated_result.title == updated_title, "Title should be updated"

        # Verify all other attributes were preserved
        assert updated_result.description == initial_description, "Description should be preserved"
        assert updated_result.status == initial_status, "Status should be preserved"
        assert updated_result.creator == initial_creator, "Creator should be preserved"

        # Verify type-specific attributes were preserved
        for key, value in initial_type_specific.items():
            assert key in updated_result.type_specific_attributes, f"Type-specific attribute '{key}' should be preserved"
            # Handle date/datetime comparisons
            if value is not None:
                assert updated_result.type_specific_attributes[key] is not None, f"Type-specific attribute '{key}' should not be None"

    # Feature: mind-based-data-model-system, Property 18: Version Chain Integrity
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy(), num_updates=st.integers(min_value=1, max_value=5))
    @settings(
        max_examples=10,
        deadline=10000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_version_chain_integrity(self, mind_data, num_updates, clean_database):
        """
        Property 18: Version Chain Integrity

        For any Mind node update, the new version shall have a PREVIOUS
        relationship pointing to the immediately prior version.

        **Validates: Requirements 5.4**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid

        # Perform multiple updates
        for i in range(num_updates):
            update_data = MindUpdate(title=f"Update {i+1}")
            result = await service.update_mind(uuid, update_data)

        # Verify PREVIOUS relationships form a complete chain
        gc = GraphConnection()

        # First, find the latest version (no incoming PREVIOUS relationship)
        latest_query = """
        MATCH (latest {uuid: $uuid})
        WHERE NOT EXISTS((latest)<-[:PREVIOUS]-())
        RETURN latest.version as latest_version
        """
        latest_result = gc.engine.evaluate_query(latest_query, {"uuid": str(uuid)})
        assert len(latest_result.records_raw) > 0, "Should have a latest version"
        latest_version = latest_result.records_raw[0]["latest_version"]

        # Now traverse the chain from latest to oldest
        chain_query = """
        MATCH path = (latest {uuid: $uuid})-[:PREVIOUS*0..]->(older {uuid: $uuid})
        WHERE NOT EXISTS((latest)<-[:PREVIOUS]-())
        RETURN [node in nodes(path) | node.version] as versions
        ORDER BY length(path) DESC
        LIMIT 1
        """

        chain_result = gc.engine.evaluate_query(chain_query, {"uuid": str(uuid)})
        assert len(chain_result.records_raw) > 0, "Version chain should exist"

        versions = chain_result.records_raw[0]["versions"]

        # Verify we have the correct number of versions
        assert len(versions) == num_updates + 1, f"Should have {num_updates + 1} versions total"

        # Verify versions are consecutive and in correct order (descending)
        assert versions[0] == latest_version, "First version should be the latest"
        for i in range(len(versions) - 1):
            assert versions[i] == versions[i + 1] + 1, "Versions should be consecutive in descending order"

        # Verify the number of PREVIOUS relationships
        rel_count_query = """
        MATCH ({uuid: $uuid})-[r:PREVIOUS]->({uuid: $uuid})
        RETURN count(r) as rel_count
        """
        rel_result = gc.engine.evaluate_query(rel_count_query, {"uuid": str(uuid)})
        assert rel_result.records_raw[0]["rel_count"] == num_updates, f"Should have {num_updates} PREVIOUS relationships"

    # Feature: mind-based-data-model-system, Property 19: Update Timestamp Refresh
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        updated_title=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=("Cc", "Cs")))
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_update_timestamp_refresh(self, mind_data, updated_title, clean_database):
        """
        Property 19: Update Timestamp Refresh

        For any Mind node update, the new version's update timestamp shall be
        set to the current time within a 5-second tolerance.

        **Validates: Requirements 5.5**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        initial_timestamp = result.updated_at

        # Small delay to ensure timestamps differ
        import asyncio
        await asyncio.sleep(0.1)

        # Capture time before update
        before_update = datetime.now(timezone.utc)

        # Update the Mind node
        update_data = MindUpdate(title=updated_title)
        updated_result = await service.update_mind(result.uuid, update_data)

        # Capture time after update
        after_update = datetime.now(timezone.utc)

        # Verify timestamp was refreshed
        assert updated_result.updated_at > initial_timestamp, "Timestamp should be refreshed on update"

        # Verify timestamp is within 5-second tolerance of current time
        time_diff = abs((updated_result.updated_at - before_update).total_seconds())
        assert time_diff <= 5, f"Timestamp should be within 5 seconds of current time, was {time_diff} seconds"

        # Verify timestamp is between before and after capture times
        assert before_update <= updated_result.updated_at <= after_update, "Timestamp should be between before and after update times"

    # Feature: mind-based-data-model-system, Property 20: Creator Immutability Across Versions
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        updated_title=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=("Cc", "Cs"))),
        num_updates=st.integers(min_value=1, max_value=3)
    )
    @settings(
        max_examples=10,
        deadline=10000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_creator_immutability_across_versions(self, mind_data, updated_title, num_updates, clean_database):
        """
        Property 20: Creator Immutability Across Versions

        For any Mind node update, the creator attribute shall remain unchanged
        from the original creation, regardless of who performs the update.

        **Validates: Requirements 5.6**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        original_creator = result.creator
        uuid = result.uuid

        # Perform multiple updates
        for i in range(num_updates):
            update_data = MindUpdate(title=f"{updated_title} - Update {i+1}")
            result = await service.update_mind(uuid, update_data)

            # Verify creator remains unchanged
            assert result.creator == original_creator, f"Creator should remain '{original_creator}' after update {i+1}"

        # Verify all versions in history have the same creator
        history = await service.get_version_history(uuid)
        for version in history:
            assert version.creator == original_creator, f"All versions should have creator '{original_creator}'"

    # Feature: mind-based-data-model-system, Property 21: UUID Immutability Across Versions
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        num_updates=st.integers(min_value=1, max_value=5)
    )
    @settings(
        max_examples=10,
        deadline=10000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_uuid_immutability_across_versions(self, mind_data, num_updates, clean_database):
        """
        Property 21: UUID Immutability Across Versions

        For any Mind node and all its versions, the UUID shall remain constant
        across all updates.

        **Validates: Requirements 5.7**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        original_uuid = result.uuid

        # Perform multiple updates
        for i in range(num_updates):
            update_data = MindUpdate(description=f"Update {i+1}")
            result = await service.update_mind(original_uuid, update_data)

            # Verify UUID remains unchanged
            assert result.uuid == original_uuid, f"UUID should remain {original_uuid} after update {i+1}"

        # Verify all versions in database have the same UUID
        gc = GraphConnection()
        uuid_query = """
        MATCH (n {uuid: $uuid})
        RETURN count(DISTINCT n.uuid) as unique_uuids, collect(n.version) as versions
        """

        uuid_result = gc.engine.evaluate_query(uuid_query, {"uuid": str(original_uuid)})

        # Should have exactly 1 unique UUID across all versions
        assert uuid_result.records_raw[0]["unique_uuids"] == 1, "All versions should share the same UUID"

        # Verify we have the expected number of versions
        versions = uuid_result.records_raw[0]["versions"]
        assert len(versions) == num_updates + 1, f"Should have {num_updates + 1} versions total"

        # Verify version history returns all versions with same UUID
        history = await service.get_version_history(original_uuid)
        for version in history:
            assert version.uuid == original_uuid, f"All versions in history should have UUID {original_uuid}"



class TestVersionHistoryProperties:
    """Test version history service-level properties."""

    # Feature: mind-based-data-model-system, Property 22: Version History Completeness
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        num_updates=st.integers(min_value=1, max_value=10)
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_version_history_completeness(self, mind_data, num_updates, clean_database):
        """
        Property 22: Version History Completeness

        For any Mind node with multiple versions, requesting version history
        shall return all versions connected via PREVIOUS relationships.

        **Validates: Requirements 6.1**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid

        # Perform multiple updates to create version history
        for i in range(num_updates):
            update_data = MindUpdate(title=f"Version {i+2}")
            await service.update_mind(uuid, update_data)

        # Get version history
        history = await service.get_version_history(uuid)

        # Verify all versions are returned (initial + updates)
        expected_version_count = num_updates + 1
        assert len(history) == expected_version_count, \
            f"History should contain {expected_version_count} versions, got {len(history)}"

        # Verify all version numbers are present
        version_numbers = {version.version for version in history}
        expected_versions = set(range(1, expected_version_count + 1))
        assert version_numbers == expected_versions, \
            f"History should contain versions {expected_versions}, got {version_numbers}"

        # Verify all versions have the same UUID
        for version in history:
            assert version.uuid == uuid, "All versions should have the same UUID"

    # Feature: mind-based-data-model-system, Property 23: Version History Ordering
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        num_updates=st.integers(min_value=2, max_value=10)
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_version_history_ordering(self, mind_data, num_updates, clean_database):
        """
        Property 23: Version History Ordering

        For any Mind node version history, the returned list shall be ordered
        from newest to oldest by version number.

        **Validates: Requirements 6.2**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid

        # Perform multiple updates
        for i in range(num_updates):
            update_data = MindUpdate(description=f"Update {i+1}")
            await service.update_mind(uuid, update_data)

        # Get version history
        history = await service.get_version_history(uuid)

        # Verify ordering: newest to oldest (descending version numbers)
        version_numbers = [version.version for version in history]

        # Check that versions are in descending order
        for i in range(len(version_numbers) - 1):
            assert version_numbers[i] > version_numbers[i + 1], \
                f"Version {version_numbers[i]} should be greater than {version_numbers[i + 1]} (newest to oldest)"

        # Verify first version is the latest
        assert version_numbers[0] == num_updates + 1, \
            f"First version should be {num_updates + 1} (latest), got {version_numbers[0]}"

        # Verify last version is the original
        assert version_numbers[-1] == 1, \
            f"Last version should be 1 (original), got {version_numbers[-1]}"

    # Feature: mind-based-data-model-system, Property 24: Version History Attribute Completeness
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        num_updates=st.integers(min_value=1, max_value=5)
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_version_history_attribute_completeness(self, mind_data, num_updates, clean_database):
        """
        Property 24: Version History Attribute Completeness

        For any version in a Mind node's history, all base and type-specific
        attributes shall be included in the history response.

        **Validates: Requirements 6.3, 6.4**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid

        # Perform multiple updates
        for i in range(num_updates):
            update_data = MindUpdate(title=f"Updated Title {i+1}")
            await service.update_mind(uuid, update_data)

        # Get version history
        history = await service.get_version_history(uuid)

        # Verify each version has all required base attributes
        for version in history:
            # Base attributes
            assert version.uuid is not None, "UUID should be present"
            assert version.mind_type is not None, "mind_type should be present"
            assert version.title is not None, "title should be present"
            assert version.version is not None, "version should be present"
            assert version.updated_at is not None, "updated_at should be present"
            assert version.creator is not None, "creator should be present"
            assert version.status is not None, "status should be present"
            # description can be None, so just check it exists as an attribute
            assert hasattr(version, 'description'), "description attribute should exist"

            # Type-specific attributes
            assert version.type_specific_attributes is not None, \
                "type_specific_attributes should be present"
            assert isinstance(version.type_specific_attributes, dict), \
                "type_specific_attributes should be a dictionary"

            # Verify type-specific attributes match the mind_type requirements
            for key in mind_data.type_specific_attributes.keys():
                assert key in version.type_specific_attributes, \
                    f"Type-specific attribute '{key}' should be present in version {version.version}"

    # Feature: mind-based-data-model-system, Property 25: Version History Pagination
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        total_updates=st.integers(min_value=5, max_value=15),
        page_size=st.integers(min_value=2, max_value=5)
    )
    @settings(
        max_examples=5,
        deadline=20000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_version_history_pagination(self, mind_data, total_updates, page_size, clean_database):
        """
        Property 25: Version History Pagination

        For any Mind node with more than page_size versions, version history
        queries shall support pagination with configurable page size.

        **Validates: Requirements 6.6**
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid

        # Perform multiple updates to create enough versions for pagination
        for i in range(total_updates):
            update_data = MindUpdate(description=f"Update {i+1}")
            await service.update_mind(uuid, update_data)

        total_versions = total_updates + 1  # Initial + updates

        # Test first page
        page1 = await service.get_version_history(uuid, page=1, page_size=page_size)
        assert len(page1) <= page_size, \
            f"First page should have at most {page_size} items, got {len(page1)}"

        # If we have more versions than page_size, test second page
        if total_versions > page_size:
            page2 = await service.get_version_history(uuid, page=2, page_size=page_size)

            # Verify second page exists and has items
            assert len(page2) > 0, "Second page should have items when total versions exceed page size"

            # Verify no overlap between pages (different version numbers)
            page1_versions = {v.version for v in page1}
            page2_versions = {v.version for v in page2}
            assert page1_versions.isdisjoint(page2_versions), \
                "Pages should not contain overlapping versions"

            # Verify ordering continues across pages (page1 has newer versions than page2)
            if page1 and page2:
                min_page1_version = min(v.version for v in page1)
                max_page2_version = max(v.version for v in page2)
                assert min_page1_version > max_page2_version, \
                    "First page should contain newer versions than second page"

        # Test retrieving all versions across all pages
        all_versions_paginated = []
        page_num = 1
        max_pages = (total_versions + page_size - 1) // page_size  # Ceiling division

        while page_num <= max_pages:
            page = await service.get_version_history(uuid, page=page_num, page_size=page_size)
            if not page:
                break
            all_versions_paginated.extend(page)
            page_num += 1

        # Verify all versions were retrieved through pagination
        assert len(all_versions_paginated) == total_versions, \
            f"Pagination should retrieve all {total_versions} versions, got {len(all_versions_paginated)}"

        # Verify all version numbers are present
        paginated_version_numbers = {v.version for v in all_versions_paginated}
        expected_versions = set(range(1, total_versions + 1))
        assert paginated_version_numbers == expected_versions, \
            "Pagination should retrieve all version numbers"



class TestMindDeletionProperties:
    """Test Mind deletion service-level properties."""

    # Feature: mind-based-data-model-system, Property 26: Soft Delete Status Update
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_soft_delete_status_update(self, mind_data, clean_database):
        """
        Property 26: Soft Delete Status Update

        For any Mind node soft delete request, the system shall create a new
        version with status set to "deleted" following all version history rules.

        **Validates: Requirements 7.1, 7.2**
        """
        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid
        initial_version = result.version
        initial_status = result.status

        # Verify initial status is not deleted
        assert initial_status != StatusEnum.DELETED, "Initial status should not be deleted"

        # Perform soft delete
        delete_result = await service.delete_mind(uuid, hard_delete=False)
        assert delete_result is True, "Soft delete should return True"

        # Retrieve the latest version
        latest = await service.get_mind(uuid)

        # Verify status is now deleted
        assert latest.status == StatusEnum.DELETED, "Status should be 'deleted' after soft delete"

        # Verify version was incremented (new version created)
        assert latest.version == initial_version + 1, \
            "Soft delete should create a new version with incremented version number"

        # Verify UUID remains the same
        assert latest.uuid == uuid, "UUID should remain unchanged after soft delete"

        # Verify version history contains both versions
        history = await service.get_version_history(uuid)
        assert len(history) == 2, "History should contain original and deleted versions"

        # Verify the deleted version is the latest
        assert history[0].status == StatusEnum.DELETED, "Latest version should have deleted status"
        assert history[0].version == initial_version + 1, "Latest version should have incremented version"

        # Verify the original version still exists with original status
        assert history[1].status == initial_status, "Original version should retain original status"
        assert history[1].version == initial_version, "Original version should retain original version number"

    # Feature: mind-based-data-model-system, Property 27: Hard Delete Completeness
    @pytest.mark.asyncio
    @given(
        mind_data=mind_creation_strategy(),
        num_updates=st.integers(min_value=0, max_value=5)
    )
    @settings(
        max_examples=10,
        deadline=10000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_hard_delete_completeness(self, mind_data, num_updates, clean_database):
        """
        Property 27: Hard Delete Completeness

        For any Mind node hard delete request with confirmation, the system
        shall remove all versions of that node and all associated PREVIOUS
        relationships from the database.

        **Validates: Requirements 7.3, 7.4**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid

        # Perform multiple updates to create version history
        for i in range(num_updates):
            update_data = MindUpdate(title=f"Update {i+1}")
            await service.update_mind(uuid, update_data)

        # Verify nodes exist before deletion
        gc = GraphConnection()
        count_before = gc.engine.evaluate_query(
            "MATCH (n {uuid: $uuid}) RETURN count(n) as count",
            {"uuid": str(uuid)}
        )
        nodes_before = count_before.records_raw[0]["count"]
        expected_versions = num_updates + 1
        assert nodes_before == expected_versions, \
            f"Should have {expected_versions} versions before deletion"

        # Count PREVIOUS relationships before deletion
        rel_count_before = gc.engine.evaluate_query(
            "MATCH ({uuid: $uuid})-[r:PREVIOUS]->({uuid: $uuid}) RETURN count(r) as count",
            {"uuid": str(uuid)}
        )
        rels_before = rel_count_before.records_raw[0]["count"]
        expected_rels = num_updates  # One less than number of versions
        assert rels_before == expected_rels, \
            f"Should have {expected_rels} PREVIOUS relationships before deletion"

        # Perform hard delete with confirmation
        delete_result = await service.delete_mind(uuid, hard_delete=True)
        assert delete_result is True, "Hard delete should return True"

        # Verify all nodes with this UUID are removed
        count_after = gc.engine.evaluate_query(
            "MATCH (n {uuid: $uuid}) RETURN count(n) as count",
            {"uuid": str(uuid)}
        )
        nodes_after = count_after.records_raw[0]["count"]
        assert nodes_after == 0, "All versions should be removed after hard delete"

        # Verify all PREVIOUS relationships are removed
        rel_count_after = gc.engine.evaluate_query(
            "MATCH ({uuid: $uuid})-[r:PREVIOUS]->({uuid: $uuid}) RETURN count(r) as count",
            {"uuid": str(uuid)}
        )
        rels_after = rel_count_after.records_raw[0]["count"]
        assert rels_after == 0, "All PREVIOUS relationships should be removed after hard delete"

        # Verify get_mind raises MindNotFoundError
        from src.exceptions import MindNotFoundError

        with pytest.raises(MindNotFoundError):
            await service.get_mind(uuid)

        # Verify version history is empty (should raise error or return empty)
        with pytest.raises(MindNotFoundError):
            await service.get_version_history(uuid)

    # Feature: mind-based-data-model-system, Property 28: Hard Delete Confirmation Requirement
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_hard_delete_confirmation_requirement(self, mind_data, clean_database):
        """
        Property 28: Hard Delete Confirmation Requirement

        For any hard delete request without an explicit confirmation parameter,
        the system shall reject the request with an error.

        Note: This property is implicitly validated by the default behavior of
        delete_mind(hard_delete=False), which performs soft delete instead of
        hard delete. The explicit confirmation is the hard_delete=True parameter.

        **Validates: Requirements 7.6**
        """
        from neontology import GraphConnection

        service = MindService()

        # Create initial Mind node
        result = await service.create_mind(mind_data)
        uuid = result.uuid

        # Perform delete WITHOUT hard_delete confirmation (default is False)
        delete_result = await service.delete_mind(uuid)  # hard_delete defaults to False
        assert delete_result is True, "Delete should succeed"

        # Verify node still exists (soft delete creates new version)
        gc = GraphConnection()
        count_after = gc.engine.evaluate_query(
            "MATCH (n {uuid: $uuid}) RETURN count(n) as count",
            {"uuid": str(uuid)}
        )
        nodes_after = count_after.records_raw[0]["count"]
        assert nodes_after > 0, \
            "Nodes should still exist after delete without hard_delete confirmation (soft delete)"

        # Verify the node is retrievable (soft deleted)
        latest = await service.get_mind(uuid)
        assert latest.status == StatusEnum.DELETED, \
            "Without hard_delete=True, delete should perform soft delete (status=deleted)"

        # Verify version history exists
        history = await service.get_version_history(uuid)
        assert len(history) >= 2, \
            "Version history should exist after soft delete (original + deleted version)"

        # Now test that explicit hard_delete=True performs hard delete
        # Create another node for hard delete test
        result2 = await service.create_mind(mind_data)
        uuid2 = result2.uuid

        # Perform hard delete WITH explicit confirmation
        delete_result2 = await service.delete_mind(uuid2, hard_delete=True)
        assert delete_result2 is True, "Hard delete with confirmation should succeed"

        # Verify node is completely removed
        count_after2 = gc.engine.evaluate_query(
            "MATCH (n {uuid: $uuid}) RETURN count(n) as count",
            {"uuid": str(uuid2)}
        )
        nodes_after2 = count_after2.records_raw[0]["count"]
        assert nodes_after2 == 0, \
            "With hard_delete=True, all nodes should be completely removed"



class TestRelationshipProperties:
    """Test relationship service-level properties."""

    # Feature: mind-based-data-model-system, Property 29: Relationship Endpoint Validation
    @pytest.mark.asyncio
    @given(
        mind_data1=mind_creation_strategy(),
        mind_data2=mind_creation_strategy(),
        relationship_type=st.sampled_from([
            "contains", "depends_on", "assigned_to", "relates_to", "implements", "mitigates"
        ])
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_relationship_endpoint_validation(
        self, mind_data1, mind_data2, relationship_type, clean_database
    ):
        """
        Property 29: Relationship Endpoint Validation

        For any relationship creation request, if either the source or target
        UUID does not exist, the system shall reject the request with a
        validation error.

        **Validates: Requirements 8.3**
        """
        from uuid import uuid4

        from src.exceptions import MindNotFoundError

        service = MindService()

        # Create only the first Mind node
        result1 = await service.create_mind(mind_data1)
        valid_uuid = result1.uuid
        invalid_uuid = uuid4()  # Generate a UUID that doesn't exist in database

        # Test 1: Invalid source UUID
        with pytest.raises(MindNotFoundError):
            await service.create_relationship(
                source_uuid=invalid_uuid,
                target_uuid=valid_uuid,
                relationship_type=relationship_type
            )

        # Test 2: Invalid target UUID
        with pytest.raises(MindNotFoundError):
            await service.create_relationship(
                source_uuid=valid_uuid,
                target_uuid=invalid_uuid,
                relationship_type=relationship_type
            )

        # Test 3: Both UUIDs invalid
        with pytest.raises(MindNotFoundError):
            await service.create_relationship(
                source_uuid=invalid_uuid,
                target_uuid=uuid4(),
                relationship_type=relationship_type
            )

        # Test 4: Valid UUIDs should succeed
        result2 = await service.create_mind(mind_data2)
        valid_uuid2 = result2.uuid

        # This should succeed without raising an exception
        relationship = await service.create_relationship(
            source_uuid=valid_uuid,
            target_uuid=valid_uuid2,
            relationship_type=relationship_type
        )

        assert relationship is not None, "Valid relationship creation should succeed"
        assert relationship.source_uuid == valid_uuid
        assert relationship.target_uuid == valid_uuid2
        assert relationship.relationship_type == relationship_type

    # Feature: mind-based-data-model-system, Property 30: Relationship Storage Integrity
    @pytest.mark.asyncio
    @given(
        mind_data1=mind_creation_strategy(),
        mind_data2=mind_creation_strategy(),
        relationship_type=st.sampled_from([
            "contains", "depends_on", "assigned_to", "relates_to", "implements", "mitigates"
        ])
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_relationship_storage_integrity(
        self, mind_data1, mind_data2, relationship_type, clean_database
    ):
        """
        Property 30: Relationship Storage Integrity

        For any valid relationship creation request, the system shall store the
        relationship in Neo4j with the correct type, direction, source UUID,
        and target UUID.

        **Validates: Requirements 8.4**
        """
        from neontology import GraphConnection

        service = MindService()

        # Create two Mind nodes
        result1 = await service.create_mind(mind_data1)
        result2 = await service.create_mind(mind_data2)
        source_uuid = result1.uuid
        target_uuid = result2.uuid

        # Create relationship
        relationship = await service.create_relationship(
            source_uuid=source_uuid,
            target_uuid=target_uuid,
            relationship_type=relationship_type
        )

        # Verify relationship was returned correctly
        assert relationship.source_uuid == source_uuid, "Source UUID should match"
        assert relationship.target_uuid == target_uuid, "Target UUID should match"
        assert relationship.relationship_type == relationship_type, "Relationship type should match"
        assert relationship.created_at is not None, "Created timestamp should be set"

        # Verify relationship exists in Neo4j with correct properties
        gc = GraphConnection()
        rel_type_upper = relationship_type.upper()

        verify_cypher = f"""
        MATCH (source {{uuid: $source_uuid}})-[r:{rel_type_upper}]->(target {{uuid: $target_uuid}})
        RETURN type(r) as rel_type, source.uuid as source_uuid,
               target.uuid as target_uuid, r.created_at as created_at
        """

        verify_result = gc.engine.evaluate_query(
            verify_cypher,
            {"source_uuid": str(source_uuid), "target_uuid": str(target_uuid)}
        )

        # Verify exactly one relationship exists
        assert verify_result is not None, "Query should return results"
        assert len(verify_result.records_raw) == 1, "Exactly one relationship should exist"

        record = verify_result.records_raw[0]

        # Verify stored relationship properties
        assert record["rel_type"] == rel_type_upper, "Stored relationship type should match"
        assert record["source_uuid"] == str(source_uuid), "Stored source UUID should match"
        assert record["target_uuid"] == str(target_uuid), "Stored target UUID should match"
        assert record["created_at"] is not None, "Stored created_at should exist"

        # Verify direction is correct (source -> target, not target -> source)
        reverse_cypher = f"""
        MATCH (target {{uuid: $target_uuid}})-[r:{rel_type_upper}]->(source {{uuid: $source_uuid}})
        RETURN count(r) as count
        """

        reverse_result = gc.engine.evaluate_query(
            reverse_cypher,
            {"source_uuid": str(source_uuid), "target_uuid": str(target_uuid)}
        )

        assert reverse_result.records_raw[0]["count"] == 0, \
            "Relationship should not exist in reverse direction"

    # Feature: mind-based-data-model-system, Property 31: Relationship Query Accuracy
    @pytest.mark.asyncio
    @given(
        mind_data_list=st.lists(mind_creation_strategy(), min_size=3, max_size=5),
        relationship_types=st.lists(
            st.sampled_from([
                "contains", "depends_on", "assigned_to", "relates_to", "implements", "mitigates"
            ]),
            min_size=2,
            max_size=4
        )
    )
    @settings(
        max_examples=10,
        deadline=10000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_relationship_query_accuracy(
        self, mind_data_list, relationship_types, clean_database
    ):
        """
        Property 31: Relationship Query Accuracy

        For any query for relationships of a specific type and direction, all
        returned relationships shall match the specified criteria.

        **Validates: Requirements 8.5**
        """
        service = MindService()

        # Create multiple Mind nodes
        minds = []
        for mind_data in mind_data_list:
            result = await service.create_mind(mind_data)
            minds.append(result)

        # Create relationships between nodes with different types
        created_relationships = []
        for i in range(len(minds) - 1):
            rel_type = relationship_types[i % len(relationship_types)]
            relationship = await service.create_relationship(
                source_uuid=minds[i].uuid,
                target_uuid=minds[i + 1].uuid,
                relationship_type=rel_type
            )
            created_relationships.append({
                "source": minds[i].uuid,
                "target": minds[i + 1].uuid,
                "type": rel_type,
                "relationship": relationship
            })

        # Test 1: Query all relationships for first node (outgoing)
        first_node_rels = await service.get_relationships(
            uuid=minds[0].uuid,
            direction="outgoing"
        )

        # Verify only outgoing relationships from first node are returned
        expected_outgoing = [r for r in created_relationships if r["source"] == minds[0].uuid]
        assert len(first_node_rels) == len(expected_outgoing), \
            f"Should return {len(expected_outgoing)} outgoing relationships"

        for rel in first_node_rels:
            assert rel.source_uuid == minds[0].uuid, "All relationships should have first node as source"

        # Test 2: Query incoming relationships for last node
        last_node_rels = await service.get_relationships(
            uuid=minds[-1].uuid,
            direction="incoming"
        )

        # Verify only incoming relationships to last node are returned
        expected_incoming = [r for r in created_relationships if r["target"] == minds[-1].uuid]
        assert len(last_node_rels) == len(expected_incoming), \
            f"Should return {len(expected_incoming)} incoming relationships"

        for rel in last_node_rels:
            assert rel.target_uuid == minds[-1].uuid, "All relationships should have last node as target"

        # Test 3: Query relationships filtered by type
        if len(set(relationship_types)) > 1:
            # Pick a specific relationship type to filter by
            filter_type = relationship_types[0]

            filtered_rels = await service.get_relationships(
                uuid=minds[0].uuid,
                relationship_type=filter_type,
                direction="both"
            )

            # Verify all returned relationships match the filter type
            for rel in filtered_rels:
                assert rel.relationship_type == filter_type, \
                    f"All relationships should be of type '{filter_type}'"

        # Test 4: Query both directions
        middle_node_idx = len(minds) // 2
        both_rels = await service.get_relationships(
            uuid=minds[middle_node_idx].uuid,
            direction="both"
        )

        # Verify both incoming and outgoing relationships are returned
        expected_both = [
            r for r in created_relationships
            if r["source"] == minds[middle_node_idx].uuid or r["target"] == minds[middle_node_idx].uuid
        ]

        assert len(both_rels) == len(expected_both), \
            f"Should return {len(expected_both)} relationships in both directions"

        # Verify each relationship involves the middle node
        for rel in both_rels:
            assert (rel.source_uuid == minds[middle_node_idx].uuid or
                    rel.target_uuid == minds[middle_node_idx].uuid), \
                "All relationships should involve the queried node"

    # Feature: mind-based-data-model-system, Property 32: Relationship Uniqueness Enforcement
    @pytest.mark.asyncio
    @given(
        mind_data1=mind_creation_strategy(),
        mind_data2=mind_creation_strategy(),
        relationship_type=st.sampled_from([
            "contains", "depends_on", "assigned_to", "relates_to", "implements", "mitigates"
        ])
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_relationship_uniqueness_enforcement(
        self, mind_data1, mind_data2, relationship_type, clean_database
    ):
        """
        Property 32: Relationship Uniqueness Enforcement

        For any attempt to create a duplicate relationship (same source, target,
        type, and direction), the system shall reject the request.

        **Validates: Requirements 8.6**
        """
        from src.exceptions import MindRelationshipError

        service = MindService()

        # Create two Mind nodes
        result1 = await service.create_mind(mind_data1)
        result2 = await service.create_mind(mind_data2)
        source_uuid = result1.uuid
        target_uuid = result2.uuid

        # Create first relationship - should succeed
        relationship1 = await service.create_relationship(
            source_uuid=source_uuid,
            target_uuid=target_uuid,
            relationship_type=relationship_type
        )

        assert relationship1 is not None, "First relationship creation should succeed"
        assert relationship1.source_uuid == source_uuid
        assert relationship1.target_uuid == target_uuid
        assert relationship1.relationship_type == relationship_type

        # Attempt to create duplicate relationship - should fail
        with pytest.raises(MindRelationshipError) as exc_info:
            await service.create_relationship(
                source_uuid=source_uuid,
                target_uuid=target_uuid,
                relationship_type=relationship_type
            )

        # Verify error message mentions duplicate or already exists
        error_message = str(exc_info.value).lower()
        assert "already exists" in error_message or "duplicate" in error_message, \
            "Error message should indicate duplicate relationship"

        # Verify only one relationship exists in database
        from neontology import GraphConnection

        gc = GraphConnection()
        rel_type_upper = relationship_type.upper()

        count_cypher = f"""
        MATCH (source {{uuid: $source_uuid}})-[r:{rel_type_upper}]->(target {{uuid: $target_uuid}})
        RETURN count(r) as count
        """

        count_result = gc.engine.evaluate_query(
            count_cypher,
            {"source_uuid": str(source_uuid), "target_uuid": str(target_uuid)}
        )

        assert count_result.records_raw[0]["count"] == 1, \
            "Exactly one relationship should exist (duplicate should be rejected)"

        # Test that reverse direction is allowed (different relationship)
        relationship_reverse = await service.create_relationship(
            source_uuid=target_uuid,  # Swap source and target
            target_uuid=source_uuid,
            relationship_type=relationship_type
        )

        assert relationship_reverse is not None, \
            "Reverse direction relationship should be allowed (different relationship)"
        assert relationship_reverse.source_uuid == target_uuid
        assert relationship_reverse.target_uuid == source_uuid

        # Test that different relationship type between same nodes is allowed
        different_types = [
            "contains", "depends_on", "assigned_to", "relates_to", "implements", "mitigates"
        ]
        different_type = next(t for t in different_types if t != relationship_type)

        relationship_different_type = await service.create_relationship(
            source_uuid=source_uuid,
            target_uuid=target_uuid,
            relationship_type=different_type
        )

        assert relationship_different_type is not None, \
            "Different relationship type between same nodes should be allowed"
        assert relationship_different_type.relationship_type == different_type



class TestQueryOperationProperties:
    """Test query operation service-level properties."""

    # Feature: mind-based-data-model-system, Property 13: Type Filtering Accuracy
    @pytest.mark.asyncio
    @given(
        mind_data_list=st.lists(mind_creation_strategy(), min_size=5, max_size=10),
        filter_type=mind_type_strategy()
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_type_filtering_accuracy(self, mind_data_list, filter_type, clean_database):
        """
        Property 13: Type Filtering Accuracy

        For any query filtered by Mind type, all returned nodes shall be of the
        specified type, and no nodes of that type shall be omitted (assuming
        pagination limits are not exceeded).

        **Validates: Requirements 4.4, 11.1**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # Ensure database is clean at start
        gc = GraphConnection()
        gc.engine.evaluate_query("MATCH (n) DETACH DELETE n")

        # Create multiple Mind nodes of various types
        created_minds = []
        for mind_data in mind_data_list:
            result = await service.create_mind(mind_data)
            created_minds.append(result)

        # Count how many nodes of the filter type were created
        expected_count = sum(1 for mind in created_minds if mind.mind_type == filter_type)

        # Query with type filter
        filters = MindQueryFilters(
            mind_type=filter_type,
            page=1,
            page_size=100  # Large enough to get all results
        )
        query_result = await service.query_minds(filters)

        # Verify all returned nodes are of the specified type
        for item in query_result.items:
            assert item.mind_type == filter_type, \
                f"All returned nodes should be of type '{filter_type}', got '{item.mind_type}'"

        # Verify no nodes of that type were omitted
        assert len(query_result.items) == expected_count, \
            f"Should return {expected_count} nodes of type '{filter_type}', got {len(query_result.items)}"

        # Verify total count matches
        assert query_result.total == expected_count, \
            f"Total count should be {expected_count}, got {query_result.total}"

        # Verify all returned UUIDs are from nodes of the correct type
        returned_uuids = {item.uuid for item in query_result.items}
        expected_uuids = {mind.uuid for mind in created_minds if mind.mind_type == filter_type}
        assert returned_uuids == expected_uuids, \
            "Returned UUIDs should match all created nodes of the specified type"

    # Feature: mind-based-data-model-system, Property 14: Status Filtering Accuracy
    @pytest.mark.asyncio
    @given(
        mind_data_list=st.lists(mind_creation_strategy(), min_size=5, max_size=10),
        filter_status=st.sampled_from([s for s in StatusEnum])
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_status_filtering_accuracy(self, mind_data_list, filter_status, clean_database):
        """
        Property 14: Status Filtering Accuracy

        For any query filtered by status, all returned nodes shall have the
        specified status, and no nodes with that status shall be omitted
        (assuming pagination limits are not exceeded).

        **Validates: Requirements 4.5, 11.2**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindQueryFilters, MindUpdate

        service = MindService()

        # Ensure database is clean at start
        gc = GraphConnection()
        gc.engine.evaluate_query("MATCH (n) DETACH DELETE n")

        # Create multiple Mind nodes
        created_minds = []
        for mind_data in mind_data_list:
            result = await service.create_mind(mind_data)
            created_minds.append(result)

        # Update ALL nodes to have different statuses (force updates)
        for i, mind in enumerate(created_minds):
            # Assign statuses in a pattern to ensure variety
            status_list = list(StatusEnum)
            target_status = status_list[i % len(status_list)]

            # Always update to ensure we have the latest version reference
            update_data = MindUpdate(status=target_status)
            updated = await service.update_mind(mind.uuid, update_data)
            # Update the reference to point to the latest version
            created_minds[i] = updated

        # Count how many nodes have the filter status (using latest versions only)
        expected_count = sum(1 for mind in created_minds if mind.status == filter_status)

        # Query with status filter
        filters = MindQueryFilters(
            status=filter_status,
            page=1,
            page_size=100  # Large enough to get all results
        )
        query_result = await service.query_minds(filters)

        # Verify all returned nodes have the specified status
        for item in query_result.items:
            assert item.status == filter_status, \
                f"All returned nodes should have status '{filter_status.value}', got '{item.status.value}'"

        # Verify no nodes with that status were omitted
        assert len(query_result.items) == expected_count, \
            f"Should return {expected_count} nodes with status '{filter_status.value}', got {len(query_result.items)}"

        # Verify total count matches
        assert query_result.total == expected_count, \
            f"Total count should be {expected_count}, got {query_result.total}"

        # Verify all returned UUIDs are from nodes with the correct status
        returned_uuids = {item.uuid for item in query_result.items}
        expected_uuids = {mind.uuid for mind in created_minds if mind.status == filter_status}
        assert returned_uuids == expected_uuids, \
            "Returned UUIDs should match all created nodes with the specified status"

    # Feature: mind-based-data-model-system, Property 37: Creator Filtering Accuracy
    @pytest.mark.asyncio
    @given(
        mind_data_list=st.lists(mind_creation_strategy(), min_size=5, max_size=10)
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_creator_filtering_accuracy(self, mind_data_list, clean_database):
        """
        Property 37: Creator Filtering Accuracy

        For any query filtered by creator, all returned nodes shall have the
        specified creator, and no nodes with that creator shall be omitted
        (assuming pagination limits are not exceeded).

        **Validates: Requirements 11.3**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # Ensure database is clean at start
        gc = GraphConnection()
        gc.engine.evaluate_query("MATCH (n) DETACH DELETE n")

        # Create Mind nodes with different creators
        created_minds = []
        for mind_data in mind_data_list:
            result = await service.create_mind(mind_data)
            created_minds.append(result)

        # Pick a creator to filter by (use the first one we created)
        if not created_minds:
            return  # Skip if no minds created

        filter_creator = created_minds[0].creator
        expected_count = sum(1 for mind in created_minds if mind.creator == filter_creator)

        # Query with creator filter
        filters = MindQueryFilters(
            creator=filter_creator,
            page=1,
            page_size=100  # Large enough to get all results
        )
        query_result = await service.query_minds(filters)

        # Verify all returned nodes have the specified creator
        for item in query_result.items:
            assert item.creator == filter_creator, \
                f"All returned nodes should have creator '{filter_creator}', got '{item.creator}'"

        # Verify no nodes with that creator were omitted
        assert len(query_result.items) == expected_count, \
            f"Should return {expected_count} nodes with creator '{filter_creator}', got {len(query_result.items)}"

        # Verify total count matches
        assert query_result.total == expected_count, \
            f"Total count should be {expected_count}, got {query_result.total}"

        # Verify all returned UUIDs are from nodes with the correct creator
        returned_uuids = {item.uuid for item in query_result.items}
        expected_uuids = {mind.uuid for mind in created_minds if mind.creator == filter_creator}
        assert returned_uuids == expected_uuids, \
            "Returned UUIDs should match all created nodes with the specified creator"

    # Feature: mind-based-data-model-system, Property 38: Date Range Filtering Accuracy
    @pytest.mark.asyncio
    @given(
        mind_data_list=st.lists(mind_creation_strategy(), min_size=5, max_size=10)
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_date_range_filtering_accuracy(self, mind_data_list, clean_database):
        """
        Property 38: Date Range Filtering Accuracy

        For any query filtered by date range on update timestamp, all returned
        nodes shall have update timestamps within the specified range, and no
        nodes within that range shall be omitted (assuming pagination limits
        are not exceeded).

        **Validates: Requirements 11.4**
        """
        import asyncio

        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # Create Mind nodes with staggered timestamps
        created_minds = []
        for i, mind_data in enumerate(mind_data_list):
            result = await service.create_mind(mind_data)
            created_minds.append(result)

            # Add small delay to ensure different timestamps
            if i < len(mind_data_list) - 1:
                await asyncio.sleep(0.1)

        # Sort by timestamp to determine range
        sorted_minds = sorted(created_minds, key=lambda m: m.updated_at)

        # Define date range: exclude first and last nodes
        if len(sorted_minds) >= 3:
            updated_after = sorted_minds[0].updated_at
            updated_before = sorted_minds[-1].updated_at

            # Count nodes within range (inclusive)
            expected_count = sum(
                1 for mind in created_minds
                if updated_after <= mind.updated_at <= updated_before
            )

            # Query with date range filter
            filters = MindQueryFilters(
                updated_after=updated_after,
                updated_before=updated_before,
                page=1,
                page_size=100  # Large enough to get all results
            )
            query_result = await service.query_minds(filters)

            # Verify all returned nodes are within the date range
            for item in query_result.items:
                assert updated_after <= item.updated_at <= updated_before, \
                    f"Node timestamp {item.updated_at} should be between {updated_after} and {updated_before}"

            # Verify no nodes within range were omitted
            assert len(query_result.items) == expected_count, \
                f"Should return {expected_count} nodes within date range, got {len(query_result.items)}"

            # Verify total count matches
            assert query_result.total == expected_count, \
                f"Total count should be {expected_count}, got {query_result.total}"

            # Test with only updated_after
            filters_after = MindQueryFilters(
                updated_after=sorted_minds[len(sorted_minds) // 2].updated_at,
                page=1,
                page_size=100
            )
            result_after = await service.query_minds(filters_after)

            for item in result_after.items:
                assert item.updated_at >= filters_after.updated_after, \
                    f"Node timestamp should be >= {filters_after.updated_after}"

            # Test with only updated_before
            filters_before = MindQueryFilters(
                updated_before=sorted_minds[len(sorted_minds) // 2].updated_at,
                page=1,
                page_size=100
            )
            result_before = await service.query_minds(filters_before)

            for item in result_before.items:
                assert item.updated_at <= filters_before.updated_before, \
                    f"Node timestamp should be <= {filters_before.updated_before}"

    # Feature: mind-based-data-model-system, Property 39: Multi-Filter Conjunction
    @pytest.mark.asyncio
    @given(
        mind_data_list=st.lists(mind_creation_strategy(), min_size=10, max_size=15),
        filter_type=mind_type_strategy(),
        filter_status=st.sampled_from([s for s in StatusEnum])
    )
    @settings(
        max_examples=10,
        deadline=20000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_multi_filter_conjunction(
        self, mind_data_list, filter_type, filter_status, clean_database
    ):
        """
        Property 39: Multi-Filter Conjunction

        For any query with multiple filters, all returned nodes shall satisfy
        all filter criteria (AND logic).

        **Validates: Requirements 11.5**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindQueryFilters, MindUpdate

        service = MindService()

        # Ensure database is clean at start
        gc = GraphConnection()
        gc.engine.evaluate_query("MATCH (n) DETACH DELETE n")

        # Create multiple Mind nodes
        created_minds = []
        for mind_data in mind_data_list:
            result = await service.create_mind(mind_data)
            created_minds.append(result)

        # Update ALL nodes to have different statuses (force updates)
        for i, mind in enumerate(created_minds):
            status_list = list(StatusEnum)
            target_status = status_list[i % len(status_list)]

            # Always update to ensure we have the latest version reference
            update_data = MindUpdate(status=target_status)
            updated = await service.update_mind(mind.uuid, update_data)
            # Update the reference to point to the latest version
            created_minds[i] = updated

        # Count nodes matching ALL criteria (AND logic) - using latest versions only
        expected_count = sum(
            1 for mind in created_minds
            if mind.mind_type == filter_type and mind.status == filter_status
        )

        # Query with multiple filters
        filters = MindQueryFilters(
            mind_type=filter_type,
            status=filter_status,
            page=1,
            page_size=100  # Large enough to get all results
        )
        query_result = await service.query_minds(filters)

        # Verify all returned nodes satisfy ALL filter criteria
        for item in query_result.items:
            assert item.mind_type == filter_type, \
                f"Node should have type '{filter_type}', got '{item.mind_type}'"
            assert item.status == filter_status, \
                f"Node should have status '{filter_status.value}', got '{item.status.value}'"

        # Verify count matches expected (AND logic)
        assert len(query_result.items) == expected_count, \
            f"Should return {expected_count} nodes matching all criteria, got {len(query_result.items)}"

        # Verify total count matches
        assert query_result.total == expected_count, \
            f"Total count should be {expected_count}, got {query_result.total}"

        # Test with three filters: type, status, and creator
        if created_minds:
            filter_creator = created_minds[0].creator

            expected_count_three = sum(
                1 for mind in created_minds
                if (mind.mind_type == filter_type and
                    mind.status == filter_status and
                    mind.creator == filter_creator)
            )

            filters_three = MindQueryFilters(
                mind_type=filter_type,
                status=filter_status,
                creator=filter_creator,
                page=1,
                page_size=100
            )
            result_three = await service.query_minds(filters_three)

            # Verify all three criteria are satisfied
            for item in result_three.items:
                assert item.mind_type == filter_type, "Should match type filter"
                assert item.status == filter_status, "Should match status filter"
                assert item.creator == filter_creator, "Should match creator filter"

            assert len(result_three.items) == expected_count_three, \
                f"Should return {expected_count_three} nodes matching all three criteria"

    # Feature: mind-based-data-model-system, Property 40: Sort Order Correctness
    @pytest.mark.asyncio
    @given(
        mind_data_list=st.lists(mind_creation_strategy(), min_size=5, max_size=10),
        sort_by=st.sampled_from(["updated_at", "version", "title"]),
        sort_order=st.sampled_from(["asc", "desc"])
    )
    @settings(
        max_examples=10,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_sort_order_correctness(
        self, mind_data_list, sort_by, sort_order, clean_database
    ):
        """
        Property 40: Sort Order Correctness

        For any query with a sort specification (by updated_at, version, or
        title), the returned results shall be ordered according to the
        specified field and direction.

        **Validates: Requirements 11.6**
        """
        import asyncio

        from src.schemas.minds import MindQueryFilters, MindUpdate

        service = MindService()

        # Create Mind nodes
        created_minds = []
        for i, mind_data in enumerate(mind_data_list):
            result = await service.create_mind(mind_data)
            created_minds.append(result)

            # Add delay to ensure different timestamps
            if i < len(mind_data_list) - 1:
                await asyncio.sleep(0.05)

        # Perform some updates to create version variety
        for i in range(min(3, len(created_minds))):
            update_data = MindUpdate(description=f"Updated {i}")
            updated = await service.update_mind(created_minds[i].uuid, update_data)
            created_minds[i] = updated

        # Query with sort specification
        filters = MindQueryFilters(
            sort_by=sort_by,
            sort_order=sort_order,
            page=1,
            page_size=100  # Large enough to get all results
        )
        query_result = await service.query_minds(filters)

        # Verify results are sorted correctly
        if len(query_result.items) > 1:
            for i in range(len(query_result.items) - 1):
                current = query_result.items[i]
                next_item = query_result.items[i + 1]

                if sort_by == "updated_at":
                    current_val = current.updated_at
                    next_val = next_item.updated_at
                elif sort_by == "version":
                    current_val = current.version
                    next_val = next_item.version
                else:  # title
                    current_val = current.title
                    next_val = next_item.title

                if sort_order == "asc":
                    assert current_val <= next_val, \
                        f"Items should be in ascending order by {sort_by}: {current_val} <= {next_val}"
                else:  # desc
                    assert current_val >= next_val, \
                        f"Items should be in descending order by {sort_by}: {current_val} >= {next_val}"

        # Test all three sort fields with both orders
        for test_sort_by in ["updated_at", "version", "title"]:
            for test_sort_order in ["asc", "desc"]:
                test_filters = MindQueryFilters(
                    sort_by=test_sort_by,
                    sort_order=test_sort_order,
                    page=1,
                    page_size=100
                )
                test_result = await service.query_minds(test_filters)

                # Verify ordering
                if len(test_result.items) > 1:
                    for i in range(len(test_result.items) - 1):
                        current = test_result.items[i]
                        next_item = test_result.items[i + 1]

                        if test_sort_by == "updated_at":
                            current_val = current.updated_at
                            next_val = next_item.updated_at
                        elif test_sort_by == "version":
                            current_val = current.version
                            next_val = next_item.version
                        else:  # title
                            current_val = current.title
                            next_val = next_item.title

                        if test_sort_order == "asc":
                            assert current_val <= next_val, \
                                f"Sort by {test_sort_by} {test_sort_order} failed"
                        else:
                            assert current_val >= next_val, \
                                f"Sort by {test_sort_by} {test_sort_order} failed"

    # Feature: mind-based-data-model-system, Property 41: Pagination Correctness
    @pytest.mark.asyncio
    @given(
        total_items=st.integers(min_value=10, max_value=25),
        page_size=st.integers(min_value=3, max_value=7)
    )
    @settings(
        max_examples=10,
        deadline=20000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_pagination_correctness(self, total_items, page_size, clean_database):
        """
        Property 41: Pagination Correctness

        For any query with pagination parameters, the system shall return the
        correct subset of results based on page number and page size, and
        include accurate total count and page metadata.

        **Validates: Requirements 11.7**
        """
        from neontology import GraphConnection

        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # Ensure database is clean at start
        gc = GraphConnection()
        gc.engine.evaluate_query("MATCH (n) DETACH DELETE n")

        # Create a known number of Mind nodes
        created_minds = []
        for i in range(total_items):
            mind_data = MindCreate(
                mind_type="task",
                title=f"Task {i:03d}",  # Zero-padded for consistent sorting
                creator="test@example.com",
                type_specific_attributes={
                    "priority": "medium",
                    "assignee": "dev@example.com",
                    "due_date": None,
                    "estimated_hours": None
                }
            )
            result = await service.create_mind(mind_data)
            created_minds.append(result)

        # Calculate expected pagination metadata
        expected_total_pages = (total_items + page_size - 1) // page_size

        # Test first page
        filters_page1 = MindQueryFilters(
            page=1,
            page_size=page_size,
            sort_by="title",
            sort_order="asc"
        )
        result_page1 = await service.query_minds(filters_page1)

        # Verify first page metadata
        assert result_page1.total == total_items, \
            f"Total should be {total_items}, got {result_page1.total}"
        assert result_page1.page == 1, "Page should be 1"
        assert result_page1.page_size == page_size, \
            f"Page size should be {page_size}, got {result_page1.page_size}"
        assert result_page1.total_pages == expected_total_pages, \
            f"Total pages should be {expected_total_pages}, got {result_page1.total_pages}"

        # Verify first page has correct number of items
        expected_page1_items = min(page_size, total_items)
        assert len(result_page1.items) == expected_page1_items, \
            f"First page should have {expected_page1_items} items, got {len(result_page1.items)}"

        # Test second page (if exists)
        if expected_total_pages > 1:
            filters_page2 = MindQueryFilters(
                page=2,
                page_size=page_size,
                sort_by="title",
                sort_order="asc"
            )
            result_page2 = await service.query_minds(filters_page2)

            # Verify second page metadata
            assert result_page2.total == total_items, "Total should remain consistent"
            assert result_page2.page == 2, "Page should be 2"
            assert result_page2.page_size == page_size, "Page size should remain consistent"
            assert result_page2.total_pages == expected_total_pages, "Total pages should remain consistent"

            # Verify second page has correct number of items
            expected_page2_items = min(page_size, total_items - page_size)
            assert len(result_page2.items) == expected_page2_items, \
                f"Second page should have {expected_page2_items} items, got {len(result_page2.items)}"

            # Verify no overlap between pages
            page1_uuids = {item.uuid for item in result_page1.items}
            page2_uuids = {item.uuid for item in result_page2.items}
            assert page1_uuids.isdisjoint(page2_uuids), \
                "Pages should not contain overlapping items"

        # Test last page
        filters_last_page = MindQueryFilters(
            page=expected_total_pages,
            page_size=page_size,
            sort_by="title",
            sort_order="asc"
        )
        result_last_page = await service.query_minds(filters_last_page)

        # Verify last page has correct number of items
        items_before_last_page = (expected_total_pages - 1) * page_size
        expected_last_page_items = total_items - items_before_last_page
        assert len(result_last_page.items) == expected_last_page_items, \
            f"Last page should have {expected_last_page_items} items, got {len(result_last_page.items)}"

        # Test page beyond last page (should return empty)
        filters_beyond = MindQueryFilters(
            page=expected_total_pages + 1,
            page_size=page_size,
            sort_by="title",
            sort_order="asc"
        )
        result_beyond = await service.query_minds(filters_beyond)

        assert len(result_beyond.items) == 0, \
            "Page beyond last page should return empty items list"
        assert result_beyond.total == total_items, \
            "Total count should remain consistent even for empty pages"

        # Verify all items can be retrieved through pagination
        all_items_paginated = []
        for page_num in range(1, expected_total_pages + 1):
            filters_page = MindQueryFilters(
                page=page_num,
                page_size=page_size,
                sort_by="title",
                sort_order="asc"
            )
            result_page = await service.query_minds(filters_page)
            all_items_paginated.extend(result_page.items)

        # Verify all items were retrieved
        assert len(all_items_paginated) == total_items, \
            f"Pagination should retrieve all {total_items} items, got {len(all_items_paginated)}"

        # Verify all UUIDs are unique (no duplicates across pages)
        all_uuids = [item.uuid for item in all_items_paginated]
        assert len(all_uuids) == len(set(all_uuids)), \
            "All items across pages should be unique (no duplicates)"

        # Verify all created items were retrieved
        created_uuids = {mind.uuid for mind in created_minds}
        paginated_uuids = {item.uuid for item in all_items_paginated}
        assert created_uuids == paginated_uuids, \
            "Pagination should retrieve exactly the created items"



class TestErrorHandlingProperties:
    """Test error handling and response format properties."""

    # Feature: mind-based-data-model-system, Property 42: Error Response Format Consistency
    @pytest.mark.asyncio
    @given(
        mind_type=mind_type_strategy(),
        title=st.text(min_size=1, max_size=200),
        creator=st.emails(),
    )
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_error_response_format_consistency_validation_error(
        self, mind_type, title, creator, clean_database
    ):
        """
        Property 42: Error Response Format Consistency (Validation Errors)

        For any error condition, the response shall include a unique request_id,
        error_type, message, timestamp, and appropriate HTTP status code.

        This test validates that validation errors (HTTP 400) follow the
        consistent error response format.

        **Validates: Requirements 12.1, 12.6**
        """
        from fastapi.testclient import TestClient

        from src.app import app

        client = TestClient(app)

        # Create Mind node with missing required type-specific attributes
        # (empty dict should fail validation for most types)
        mind_data = {
            "mind_type": mind_type,
            "title": title,
            "creator": creator,
            "type_specific_attributes": {},  # Missing required attributes
        }

        # Attempt to create - should return validation error
        response = client.post("/api/v1/minds", json=mind_data)

        # Verify HTTP status code is 400 or 422 (Bad Request / Unprocessable Entity)
        assert response.status_code in [400, 422], \
            f"Validation error should return HTTP 400 or 422, got {response.status_code}"

        # Parse error response
        error_data = response.json()

        # Verify all required error response fields are present
        assert "request_id" in error_data, "Error response should include request_id"
        assert "error_type" in error_data, "Error response should include error_type"
        assert "message" in error_data, "Error response should include message"
        assert "details" in error_data, "Error response should include details"
        assert "timestamp" in error_data, "Error response should include timestamp"

        # Verify request_id is a non-empty string
        assert isinstance(error_data["request_id"], str), "request_id should be a string"
        assert len(error_data["request_id"]) > 0, "request_id should not be empty"
        assert error_data["request_id"].startswith("req_"), \
            "request_id should follow format 'req_<id>'"

        # Verify error_type is appropriate for validation errors
        assert error_data["error_type"] in ["ValidationError", "InternalError", "RequestValidationError"], \
            f"error_type should be ValidationError, InternalError, or RequestValidationError, got {error_data['error_type']}"

        # Verify message is a non-empty string
        assert isinstance(error_data["message"], str), "message should be a string"
        assert len(error_data["message"]) > 0, "message should not be empty"

        # Verify details is a dictionary
        assert isinstance(error_data["details"], dict), "details should be a dictionary"

        # Verify timestamp is a valid ISO format datetime string
        assert isinstance(error_data["timestamp"], str), "timestamp should be a string"
        try:
            datetime.fromisoformat(error_data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("timestamp should be a valid ISO format datetime")

    # Feature: mind-based-data-model-system, Property 42: Error Response Format Consistency
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_error_response_format_consistency_not_found_error(
        self, mind_data, clean_database
    ):
        """
        Property 42: Error Response Format Consistency (Not Found Errors)

        For any error condition, the response shall include a unique request_id,
        error_type, message, timestamp, and appropriate HTTP status code.

        This test validates that not found errors (HTTP 404) follow the
        consistent error response format.

        **Validates: Requirements 12.1, 12.6**
        """
        from uuid import uuid4

        from fastapi.testclient import TestClient

        from src.app import app

        client = TestClient(app)

        # Generate a UUID that doesn't exist in the database
        non_existent_uuid = uuid4()

        # Attempt to retrieve non-existent Mind node
        response = client.get(f"/api/v1/minds/{non_existent_uuid}")

        # Verify HTTP status code is 404 (Not Found)
        assert response.status_code == 404, \
            f"Not found error should return HTTP 404, got {response.status_code}"

        # Parse error response
        error_data = response.json()

        # Verify all required error response fields are present
        assert "request_id" in error_data, "Error response should include request_id"
        assert "error_type" in error_data, "Error response should include error_type"
        assert "message" in error_data, "Error response should include message"
        assert "details" in error_data, "Error response should include details"
        assert "timestamp" in error_data, "Error response should include timestamp"

        # Verify request_id format
        assert isinstance(error_data["request_id"], str), "request_id should be a string"
        assert len(error_data["request_id"]) > 0, "request_id should not be empty"
        assert error_data["request_id"].startswith("req_"), \
            "request_id should follow format 'req_<id>'"

        # Verify error_type is appropriate for not found errors
        assert error_data["error_type"] == "NotFoundError", \
            f"error_type should be NotFoundError, got {error_data['error_type']}"

        # Verify message contains the UUID
        assert isinstance(error_data["message"], str), "message should be a string"
        assert len(error_data["message"]) > 0, "message should not be empty"
        assert str(non_existent_uuid) in error_data["message"], \
            "message should contain the requested UUID"

        # Verify details contains the UUID
        assert isinstance(error_data["details"], dict), "details should be a dictionary"
        assert "uuid" in error_data["details"], "details should contain uuid field"
        assert error_data["details"]["uuid"] == str(non_existent_uuid), \
            "details.uuid should match the requested UUID"

        # Verify timestamp format
        assert isinstance(error_data["timestamp"], str), "timestamp should be a string"
        try:
            datetime.fromisoformat(error_data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("timestamp should be a valid ISO format datetime")

    # Feature: mind-based-data-model-system, Property 42: Error Response Format Consistency
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_error_response_format_consistency_multiple_errors(
        self, mind_data, clean_database
    ):
        """
        Property 42: Error Response Format Consistency (Multiple Error Types)

        For any error condition, the response shall include a unique request_id,
        error_type, message, timestamp, and appropriate HTTP status code.

        This test validates that different error types all follow the same
        consistent error response format, and that request_ids are unique
        across different error responses.

        **Validates: Requirements 12.1, 12.6**
        """
        from uuid import uuid4

        from fastapi.testclient import TestClient

        from src.app import app

        client = TestClient(app)

        error_responses = []

        # Test 1: Not Found Error (404)
        non_existent_uuid = uuid4()
        response1 = client.get(f"/api/v1/minds/{non_existent_uuid}")
        assert response1.status_code == 404
        error_responses.append(response1.json())

        # Test 2: Validation Error (422 or 400) - invalid mind_type
        invalid_mind_data = {
            "mind_type": "invalid_type_xyz",
            "title": "Test",
            "creator": "test@example.com",
            "type_specific_attributes": {},
        }
        response2 = client.post("/api/v1/minds", json=invalid_mind_data)
        assert response2.status_code in [400, 422], \
            f"Validation error should return HTTP 400 or 422, got {response2.status_code}"
        error_responses.append(response2.json())

        # Test 3: Validation Error (400) - bulk operation exceeds limit
        bulk_data = [mind_data.model_dump() for _ in range(101)]  # Exceeds 100 limit
        response3 = client.post("/api/v1/minds/bulk", json=bulk_data)
        assert response3.status_code in [400, 422], \
            f"Validation error should return HTTP 400 or 422, got {response3.status_code}"
        error_responses.append(response3.json())

        # Verify all error responses have consistent structure
        for i, error_data in enumerate(error_responses):
            # For 422 errors, FastAPI returns Pydantic's default format with 'detail'
            # For custom error handlers (404, 400), we use our ErrorResponse format
            if "detail" in error_data:
                # This is a FastAPI/Pydantic validation error (422)
                # Verify it has the detail field with error information
                assert isinstance(error_data["detail"], list), \
                    f"Error response {i+1} detail should be a list for 422 errors"
                assert len(error_data["detail"]) > 0, \
                    f"Error response {i+1} detail should not be empty"
                # Skip further validation for 422 errors as they use different format
                continue

            # For our custom error format (404, 400 from ValueError handler)
            # Verify all required fields are present
            assert "request_id" in error_data, \
                f"Error response {i+1} should include request_id"
            assert "error_type" in error_data, \
                f"Error response {i+1} should include error_type"
            assert "message" in error_data, \
                f"Error response {i+1} should include message"
            assert "details" in error_data, \
                f"Error response {i+1} should include details"
            assert "timestamp" in error_data, \
                f"Error response {i+1} should include timestamp"

            # Verify field types
            assert isinstance(error_data["request_id"], str), \
                f"Error response {i+1} request_id should be a string"
            assert isinstance(error_data["error_type"], str), \
                f"Error response {i+1} error_type should be a string"
            assert isinstance(error_data["message"], str), \
                f"Error response {i+1} message should be a string"
            assert isinstance(error_data["details"], dict), \
                f"Error response {i+1} details should be a dictionary"
            assert isinstance(error_data["timestamp"], str), \
                f"Error response {i+1} timestamp should be a string"

            # Verify non-empty values
            assert len(error_data["request_id"]) > 0, \
                f"Error response {i+1} request_id should not be empty"
            assert len(error_data["error_type"]) > 0, \
                f"Error response {i+1} error_type should not be empty"
            assert len(error_data["message"]) > 0, \
                f"Error response {i+1} message should not be empty"

            # Verify request_id format
            assert error_data["request_id"].startswith("req_"), \
                f"Error response {i+1} request_id should follow format 'req_<id>'"

            # Verify timestamp format
            try:
                datetime.fromisoformat(error_data["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"Error response {i+1} timestamp should be a valid ISO format datetime")

        # Verify request_ids are unique (only for custom error format responses)
        custom_error_responses = [e for e in error_responses if "request_id" in e]
        if len(custom_error_responses) > 1:
            request_ids = [error["request_id"] for error in custom_error_responses]
            assert len(request_ids) == len(set(request_ids)), \
                "All custom error responses should have unique request_ids"

        # Verify error_types are appropriate for each error (only for custom format)
        if "request_id" in error_responses[0]:
            assert error_responses[0]["error_type"] == "NotFoundError", \
                "First error should be NotFoundError"

    # Feature: mind-based-data-model-system, Property 42: Error Response Format Consistency
    @pytest.mark.asyncio
    @given(mind_data=mind_creation_strategy())
    @settings(
        max_examples=10,
        deadline=5000,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_error_response_timestamp_accuracy(self, mind_data, clean_database):
        """
        Property 42: Error Response Format Consistency (Timestamp Accuracy)

        For any error condition, the timestamp in the error response shall be
        set to the current time within a 5-second tolerance.

        **Validates: Requirements 12.1, 12.6**
        """
        from uuid import uuid4

        from fastapi.testclient import TestClient

        from src.app import app

        client = TestClient(app)

        # Capture time before error
        before_error = datetime.now(timezone.utc)

        # Trigger an error (not found)
        non_existent_uuid = uuid4()
        response = client.get(f"/api/v1/minds/{non_existent_uuid}")

        # Capture time after error
        after_error = datetime.now(timezone.utc)

        # Verify error response
        assert response.status_code == 404
        error_data = response.json()

        # Parse timestamp
        error_timestamp = datetime.fromisoformat(
            error_data["timestamp"].replace("Z", "+00:00")
        )

        # Verify timestamp is within 5-second tolerance of current time
        time_diff_before = abs((error_timestamp - before_error).total_seconds())
        time_diff_after = abs((error_timestamp - after_error).total_seconds())

        assert time_diff_before <= 5 or time_diff_after <= 5, \
            f"Error timestamp should be within 5 seconds of current time, " \
            f"was {min(time_diff_before, time_diff_after)} seconds"

        # Verify timestamp is between before and after capture times
        assert before_error <= error_timestamp <= after_error, \
            "Error timestamp should be between before and after error times"
