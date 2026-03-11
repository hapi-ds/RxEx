"""
Unit tests for MindService class.

This module contains unit tests for the MindService class, focusing on
CRUD operations, version history, relationships, and query functionality.

**Validates: Requirements 3.1-3.7**
"""

from datetime import datetime, timezone

import pytest

from src.schemas.minds import MindBulkUpdate, MindCreate, MindQueryFilters
from src.services.mind_service import MindService


class TestMindServiceCreate:
    """Test suite for MindService.create_mind method."""

    @pytest.mark.asyncio
    async def test_create_project_mind(self, clean_database):
        """
        Test creating a Project Mind node.

        Validates that create_mind:
        - Generates a UUID (Requirement 3.2)
        - Initializes version to 1 (Requirement 3.3)
        - Sets timestamp (Requirement 3.4)
        - Records creator (Requirement 3.5)
        - Returns complete node data (Requirement 3.7)
        """
        service = MindService()

        # Create a project Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Test Project",
            description="A test project for unit testing",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "budget": 50000.0,
            },
        )

        result = await service.create_mind(mind_data)

        # Verify UUID was generated (Requirement 3.2)
        assert result.uuid is not None
        assert isinstance(result.uuid, type(result.uuid))  # UUID type

        # Verify version initialized to 1 (Requirement 3.3)
        assert result.version == 1

        # Verify timestamp was set (Requirement 3.4)
        assert result.updated_at is not None
        assert isinstance(result.updated_at, datetime)
        # Timestamp should be recent (within last 10 seconds)
        time_diff = datetime.now(timezone.utc) - result.updated_at
        assert time_diff.total_seconds() < 10

        # Verify creator was recorded (Requirement 3.5)
        assert result.creator == "test@example.com"

        # Verify complete node data returned (Requirement 3.7)
        assert result.mind_type == "project"
        assert result.title == "Test Project"
        assert result.description == "A test project for unit testing"
        assert result.type_specific_attributes["start_date"] == "2024-01-01"
        assert result.type_specific_attributes["end_date"] == "2024-12-31"
        assert result.type_specific_attributes["budget"] == 50000.0

    @pytest.mark.asyncio
    async def test_create_task_mind(self, clean_database):
        """
        Test creating a Task Mind node with type-specific attributes.

        Validates that create_mind handles Task-specific attributes correctly.
        """
        service = MindService()

        mind_data = MindCreate(
            mind_type="task",
            title="Implement authentication",
            description="Add JWT-based authentication",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
                "due_date": "2024-01-20",
                "estimated_hours": 8.0,
            },
        )

        result = await service.create_mind(mind_data)

        # Verify base attributes
        assert result.uuid is not None
        assert result.version == 1
        assert result.creator == "dev@example.com"

        # Verify Task-specific attributes
        assert result.mind_type == "task"
        assert result.type_specific_attributes["priority"] == "high"
        assert result.type_specific_attributes["assignee"] == "dev@example.com"
        assert result.type_specific_attributes["due_date"] == "2024-01-20"
        assert result.type_specific_attributes["estimated_hours"] == 8.0

    @pytest.mark.asyncio
    async def test_create_risk_mind(self, clean_database):
        """
        Test creating a Risk Mind node with severity and probability.

        Validates that create_mind handles Risk-specific attributes correctly.
        """
        service = MindService()

        mind_data = MindCreate(
            mind_type="risk",
            title="Database failure risk",
            description="Risk of database connection failure",
            creator="admin@example.com",
            type_specific_attributes={
                "severity": "high",
                "probability": "unlikely",
                "mitigation_plan": "Implement connection pooling and retry logic",
            },
        )

        result = await service.create_mind(mind_data)

        # Verify base attributes
        assert result.uuid is not None
        assert result.version == 1
        assert result.creator == "admin@example.com"

        # Verify Risk-specific attributes
        assert result.mind_type == "risk"
        assert result.type_specific_attributes["severity"] == "high"
        assert result.type_specific_attributes["probability"] == "unlikely"
        assert (
            result.type_specific_attributes["mitigation_plan"]
            == "Implement connection pooling and retry logic"
        )

    @pytest.mark.asyncio
    async def test_create_mind_with_minimal_data(self, clean_database):
        """
        Test creating a Mind node with minimal required data.

        Validates that create_mind works with only required fields.
        """
        service = MindService()

        mind_data = MindCreate(
            mind_type="knowledge",
            title="Test Knowledge Article",
            creator="author@example.com",
            type_specific_attributes={
                "category": "Technical",
                "tags": ["testing", "documentation"],
                "content": "This is a test knowledge article.",
            },
        )

        result = await service.create_mind(mind_data)

        # Verify base attributes
        assert result.uuid is not None
        assert result.version == 1
        assert result.creator == "author@example.com"
        assert result.description is None  # Optional field not provided

        # Verify Knowledge-specific attributes
        assert result.mind_type == "knowledge"
        assert result.type_specific_attributes["category"] == "Technical"
        assert result.type_specific_attributes["tags"] == ["testing", "documentation"]
        assert result.type_specific_attributes["content"] == "This is a test knowledge article."

    @pytest.mark.asyncio
    async def test_create_mind_invalid_type(self, clean_database):
        """
        Test that MindCreate validation rejects unsupported mind_type.

        Validates error handling for invalid mind types at the schema level.
        """
        from pydantic import ValidationError

        # Pydantic validation should catch invalid mind_type before service layer
        with pytest.raises(ValidationError, match="mind_type must be one of"):
            MindCreate(
                mind_type="invalid_type",
                title="Test",
                creator="test@example.com",
                type_specific_attributes={},
            )


class TestMindServiceGet:
    """Test suite for MindService.get_mind method."""

    @pytest.mark.asyncio
    async def test_get_mind_retrieves_created_node(self, clean_database):
        """
        Test that get_mind retrieves a previously created Mind node.

        Validates that get_mind:
        - Retrieves node by UUID (Requirement 4.1)
        - Returns all base attributes (Requirement 4.2)
        - Returns all type-specific attributes (Requirement 4.2)
        """
        service = MindService()

        # Create a project Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Test Project",
            description="A test project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "budget": 50000.0,
            },
        )

        created = await service.create_mind(mind_data)

        # Retrieve the node by UUID
        retrieved = await service.get_mind(created.uuid)

        # Verify all base attributes match (Requirement 4.2)
        assert retrieved.uuid == created.uuid
        assert retrieved.mind_type == "project"
        assert retrieved.title == "Test Project"
        assert retrieved.description == "A test project"
        assert retrieved.creator == "test@example.com"
        assert retrieved.version == 1
        assert retrieved.status == created.status

        # Verify type-specific attributes match (Requirement 4.2)
        assert retrieved.type_specific_attributes["start_date"] == "2024-01-01"
        assert retrieved.type_specific_attributes["end_date"] == "2024-12-31"
        assert retrieved.type_specific_attributes["budget"] == 50000.0

    @pytest.mark.asyncio
    async def test_get_mind_with_task_type(self, clean_database):
        """
        Test that get_mind retrieves Task Mind nodes correctly.

        Validates retrieval of Task-specific attributes.
        """
        service = MindService()

        # Create a task Mind node
        mind_data = MindCreate(
            mind_type="task",
            title="Implement feature",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
                "due_date": "2024-02-01",
                "estimated_hours": 16.0,
            },
        )

        created = await service.create_mind(mind_data)

        # Retrieve the node
        retrieved = await service.get_mind(created.uuid)

        # Verify Task-specific attributes
        assert retrieved.mind_type == "task"
        assert retrieved.type_specific_attributes["priority"] == "high"
        assert retrieved.type_specific_attributes["assignee"] == "dev@example.com"
        assert retrieved.type_specific_attributes["due_date"] == "2024-02-01"
        assert retrieved.type_specific_attributes["estimated_hours"] == 16.0

    @pytest.mark.asyncio
    async def test_get_mind_with_risk_type(self, clean_database):
        """
        Test that get_mind retrieves Risk Mind nodes correctly.

        Validates retrieval of Risk-specific attributes.
        """
        service = MindService()

        # Create a risk Mind node
        mind_data = MindCreate(
            mind_type="risk",
            title="Security vulnerability",
            creator="security@example.com",
            type_specific_attributes={
                "severity": "critical",
                "probability": "likely",
                "mitigation_plan": "Apply security patches immediately",
            },
        )

        created = await service.create_mind(mind_data)

        # Retrieve the node
        retrieved = await service.get_mind(created.uuid)

        # Verify Risk-specific attributes
        assert retrieved.mind_type == "risk"
        assert retrieved.type_specific_attributes["severity"] == "critical"
        assert retrieved.type_specific_attributes["probability"] == "likely"
        assert (
            retrieved.type_specific_attributes["mitigation_plan"]
            == "Apply security patches immediately"
        )

    @pytest.mark.asyncio
    async def test_get_mind_nonexistent_uuid_raises_error(self, clean_database):
        """
        Test that get_mind raises MindNotFoundError for non-existent UUID.

        Validates error handling for non-existent UUIDs (Requirement 4.3).
        """
        from uuid import uuid4

        from src.exceptions import MindNotFoundError

        service = MindService()

        # Try to retrieve a non-existent UUID
        nonexistent_uuid = uuid4()

        with pytest.raises(MindNotFoundError) as exc_info:
            await service.get_mind(nonexistent_uuid)

        # Verify the error message contains the UUID
        assert str(nonexistent_uuid) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_mind_with_minimal_attributes(self, clean_database):
        """
        Test that get_mind retrieves nodes with minimal attributes.

        Validates retrieval when optional fields are not provided.
        """
        service = MindService()

        # Create a knowledge Mind node with minimal data
        mind_data = MindCreate(
            mind_type="knowledge",
            title="Quick Note",
            creator="author@example.com",
            type_specific_attributes={
                "category": "General",
                "tags": ["note"],
                "content": "Brief content",
            },
        )

        created = await service.create_mind(mind_data)

        # Retrieve the node
        retrieved = await service.get_mind(created.uuid)

        # Verify retrieval works with minimal data
        assert retrieved.uuid == created.uuid
        assert retrieved.title == "Quick Note"
        assert retrieved.description is None
        assert retrieved.type_specific_attributes["category"] == "General"
        assert retrieved.type_specific_attributes["tags"] == ["note"]
        assert retrieved.type_specific_attributes["content"] == "Brief content"



class TestMindServiceUpdate:
    """Test suite for MindService.update_mind method."""

    @pytest.mark.asyncio
    async def test_update_mind_creates_new_version(self, clean_database):
        """
        Test that update_mind creates a new version node.

        Validates that update_mind:
        - Creates a new node rather than modifying in place (Requirement 5.1)
        - Increments version number by 1 (Requirement 5.2)
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Initial Project",
            description="Initial description",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "budget": 50000.0,
            },
        )
        created = await service.create_mind(mind_data)
        assert created.version == 1

        # Update the Mind node
        update_data = MindUpdate(
            title="Updated Project",
            description="Updated description",
        )
        updated = await service.update_mind(created.uuid, update_data)

        # Verify new version was created (Requirement 5.1, 5.2)
        assert updated.version == 2
        assert updated.uuid == created.uuid  # UUID remains the same

    @pytest.mark.asyncio
    async def test_update_mind_preserves_unchanged_attributes(self, clean_database):
        """
        Test that update_mind preserves unchanged attributes.

        Validates that update_mind:
        - Copies unchanged attributes from previous version (Requirement 5.3)
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="task",
            title="Initial Task",
            description="Initial description",
            creator="test@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
                "due_date": "2024-01-20",
                "estimated_hours": 8.0,
            },
        )
        created = await service.create_mind(mind_data)

        # Update only the title
        update_data = MindUpdate(title="Updated Task")
        updated = await service.update_mind(created.uuid, update_data)

        # Verify unchanged attributes are preserved (Requirement 5.3)
        assert updated.title == "Updated Task"  # Changed
        assert updated.description == created.description  # Unchanged
        assert updated.type_specific_attributes["priority"] == "high"  # Unchanged
        assert updated.type_specific_attributes["assignee"] == "dev@example.com"  # Unchanged
        assert updated.type_specific_attributes["due_date"] == "2024-01-20"  # Unchanged
        assert updated.type_specific_attributes["estimated_hours"] == 8.0  # Unchanged

    @pytest.mark.asyncio
    async def test_update_mind_preserves_creator(self, clean_database):
        """
        Test that update_mind preserves the original creator.

        Validates that update_mind:
        - Preserves creator attribute from original creation (Requirement 5.6)
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="original@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        created = await service.create_mind(mind_data)

        # Update the Mind node
        update_data = MindUpdate(title="Updated Project")
        updated = await service.update_mind(created.uuid, update_data)

        # Verify creator is preserved (Requirement 5.6)
        assert updated.creator == "original@example.com"
        assert updated.creator == created.creator

    @pytest.mark.asyncio
    async def test_update_mind_preserves_uuid(self, clean_database):
        """
        Test that update_mind preserves UUID across versions.

        Validates that update_mind:
        - Maintains same UUID across all versions (Requirement 5.7)
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        created = await service.create_mind(mind_data)
        original_uuid = created.uuid

        # Perform multiple updates
        for i in range(3):
            update_data = MindUpdate(title=f"Updated Project {i+1}")
            updated = await service.update_mind(original_uuid, update_data)

            # Verify UUID remains constant (Requirement 5.7)
            assert updated.uuid == original_uuid

    @pytest.mark.asyncio
    async def test_update_mind_sets_new_timestamp(self, clean_database):
        """
        Test that update_mind sets a new timestamp.

        Validates that update_mind:
        - Sets new timestamp to current time (Requirement 5.5)
        """
        import asyncio

        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        created = await service.create_mind(mind_data)
        original_timestamp = created.updated_at

        # Wait a moment to ensure timestamp difference
        await asyncio.sleep(0.1)

        # Update the Mind node
        update_data = MindUpdate(title="Updated Project")
        updated = await service.update_mind(created.uuid, update_data)

        # Verify new timestamp was set (Requirement 5.5)
        assert updated.updated_at > original_timestamp
        # Timestamp should be recent (within last 10 seconds)
        time_diff = datetime.now(timezone.utc) - updated.updated_at
        assert time_diff.total_seconds() < 10

    @pytest.mark.asyncio
    async def test_update_mind_with_type_specific_attributes(self, clean_database):
        """
        Test updating type-specific attributes.

        Validates that update_mind:
        - Updates type-specific attributes correctly
        - Preserves unchanged type-specific attributes (Requirement 5.3)
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "budget": 50000.0,
            },
        )
        created = await service.create_mind(mind_data)

        # Update only budget
        update_data = MindUpdate(
            type_specific_attributes={"budget": 75000.0}
        )
        updated = await service.update_mind(created.uuid, update_data)

        # Verify budget was updated and dates preserved
        assert updated.type_specific_attributes["budget"] == 75000.0
        assert updated.type_specific_attributes["start_date"] == "2024-01-01"
        assert updated.type_specific_attributes["end_date"] == "2024-12-31"

    @pytest.mark.asyncio
    async def test_update_mind_with_status_change(self, clean_database):
        """
        Test updating the status attribute.

        Validates that update_mind:
        - Updates status correctly
        """
        from src.models.enums import StatusEnum
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="task",
            title="Test Task",
            creator="test@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        created = await service.create_mind(mind_data)
        assert created.status == StatusEnum.DRAFT

        # Update status to frozen
        update_data = MindUpdate(status=StatusEnum.FROZEN)
        updated = await service.update_mind(created.uuid, update_data)

        # Verify status was updated
        assert updated.status == StatusEnum.FROZEN
        assert updated.version == 2

    @pytest.mark.asyncio
    async def test_update_mind_nonexistent_uuid_raises_error(self, clean_database):
        """
        Test that updating a non-existent UUID raises MindNotFoundError.

        Validates that update_mind:
        - Raises MindNotFoundError for non-existent UUIDs
        """
        from uuid import uuid4

        from src.exceptions import MindNotFoundError
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Try to update a non-existent UUID
        fake_uuid = uuid4()
        update_data = MindUpdate(title="Updated Title")

        with pytest.raises(MindNotFoundError):
            await service.update_mind(fake_uuid, update_data)

    @pytest.mark.asyncio
    async def test_update_mind_multiple_sequential_updates(self, clean_database):
        """
        Test multiple sequential updates create proper version chain.

        Validates that update_mind:
        - Correctly increments version with each update (Requirement 5.2)
        - Maintains UUID across all versions (Requirement 5.7)
        """
        from src.schemas.minds import MindUpdate

        service = MindService()

        # Create initial Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Version 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        v1 = await service.create_mind(mind_data)
        assert v1.version == 1

        # Update to version 2
        v2 = await service.update_mind(v1.uuid, MindUpdate(title="Version 2"))
        assert v2.version == 2
        assert v2.uuid == v1.uuid

        # Update to version 3
        v3 = await service.update_mind(v1.uuid, MindUpdate(title="Version 3"))
        assert v3.version == 3
        assert v3.uuid == v1.uuid

        # Update to version 4
        v4 = await service.update_mind(v1.uuid, MindUpdate(title="Version 4"))
        assert v4.version == 4
        assert v4.uuid == v1.uuid


class TestMindServiceVersionHistory:
        """Test suite for MindService.get_version_history method."""

        @pytest.mark.asyncio
        async def test_get_version_history_single_version(self, clean_database):
            """
            Test that get_version_history returns single-item list for new nodes.

            Validates that get_version_history:
            - Returns single-item list for nodes with no previous versions (Requirement 6.5)
            """
            service = MindService()

            # Create a Mind node (version 1)
            mind_data = MindCreate(
                mind_type="project",
                title="Test Project",
                creator="test@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            )
            created = await service.create_mind(mind_data)

            # Get version history
            history = await service.get_version_history(created.uuid)

            # Verify single-item list (Requirement 6.5)
            assert len(history) == 1
            assert history[0].uuid == created.uuid
            assert history[0].version == 1
            assert history[0].title == "Test Project"

        @pytest.mark.asyncio
        async def test_get_version_history_multiple_versions(self, clean_database):
            """
            Test that get_version_history returns all versions in correct order.

            Validates that get_version_history:
            - Returns all versions (Requirement 6.1)
            - Orders from newest to oldest (Requirement 6.2)
            - Includes all attributes for each version (Requirement 6.3)
            """
            from src.schemas.minds import MindUpdate

            service = MindService()

            # Create initial Mind node
            mind_data = MindCreate(
                mind_type="project",
                title="Version 1",
                creator="test@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "budget": 50000.0,
                },
            )
            v1 = await service.create_mind(mind_data)

            # Create version 2
            await service.update_mind(v1.uuid, MindUpdate(title="Version 2"))

            # Create version 3
            await service.update_mind(v1.uuid, MindUpdate(title="Version 3", type_specific_attributes={"budget": 75000.0}))

            # Get version history
            history = await service.get_version_history(v1.uuid)

            # Verify all versions returned (Requirement 6.1)
            assert len(history) == 3

            # Verify ordering from newest to oldest (Requirement 6.2)
            assert history[0].version == 3
            assert history[0].title == "Version 3"
            assert history[1].version == 2
            assert history[1].title == "Version 2"
            assert history[2].version == 1
            assert history[2].title == "Version 1"

            # Verify all attributes included (Requirement 6.3)
            for version in history:
                assert version.uuid == v1.uuid
                assert version.creator == "test@example.com"
                assert version.updated_at is not None
                assert "start_date" in version.type_specific_attributes
                assert "end_date" in version.type_specific_attributes

            # Verify budget changes tracked correctly
            assert history[0].type_specific_attributes["budget"] == 75000.0
            assert history[1].type_specific_attributes["budget"] == 50000.0
            assert history[2].type_specific_attributes["budget"] == 50000.0

        @pytest.mark.asyncio
        async def test_get_version_history_preserves_all_attributes(self, clean_database):
            """
            Test that version history includes all base and type-specific attributes.

            Validates that get_version_history:
            - Includes all base attributes (Requirement 6.3)
            - Includes all type-specific attributes (Requirement 6.3)
            - Includes update timestamps (Requirement 6.4)
            """
            from src.schemas.minds import MindUpdate

            service = MindService()

            # Create initial Task node with all attributes
            mind_data = MindCreate(
                mind_type="task",
                title="Initial Task",
                description="Initial description",
                creator="dev@example.com",
                type_specific_attributes={
                    "priority": "low",
                    "assignee": "dev1@example.com",
                    "due_date": "2024-01-20",
                    "estimated_hours": 8.0,
                },
            )
            v1 = await service.create_mind(mind_data)

            # Update task
            await service.update_mind(
                v1.uuid,
                MindUpdate(
                    title="Updated Task",
                    type_specific_attributes={
                        "priority": "high",
                        "assignee": "dev2@example.com",
                    }
                )
            )

            # Get version history
            history = await service.get_version_history(v1.uuid)

            # Verify all base attributes present in all versions
            for version in history:
                assert version.uuid is not None
                assert version.mind_type == "task"
                assert version.title is not None
                assert version.version is not None
                assert version.updated_at is not None  # Requirement 6.4
                assert version.creator == "dev@example.com"
                assert version.status is not None
                # description can be None

            # Verify all type-specific attributes present
            for version in history:
                assert "priority" in version.type_specific_attributes
                assert "assignee" in version.type_specific_attributes
                assert "due_date" in version.type_specific_attributes
                assert "estimated_hours" in version.type_specific_attributes

            # Verify attribute changes tracked
            assert history[0].title == "Updated Task"
            assert history[0].type_specific_attributes["priority"] == "high"
            assert history[0].type_specific_attributes["assignee"] == "dev2@example.com"

            assert history[1].title == "Initial Task"
            assert history[1].type_specific_attributes["priority"] == "low"
            assert history[1].type_specific_attributes["assignee"] == "dev1@example.com"

        @pytest.mark.asyncio
        async def test_get_version_history_pagination(self, clean_database):
            """
            Test that get_version_history supports pagination.

            Validates that get_version_history:
            - Supports pagination with page and page_size parameters (Requirement 6.6)
            """
            from src.schemas.minds import MindUpdate

            service = MindService()

            # Create initial Mind node
            mind_data = MindCreate(
                mind_type="project",
                title="Version 1",
                creator="test@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            )
            v1 = await service.create_mind(mind_data)

            # Create 9 more versions (total 10 versions)
            for i in range(2, 11):
                await service.update_mind(v1.uuid, MindUpdate(title=f"Version {i}"))

            # Test first page with page_size=3
            page1 = await service.get_version_history(v1.uuid, page=1, page_size=3)
            assert len(page1) == 3
            assert page1[0].version == 10  # Newest
            assert page1[1].version == 9
            assert page1[2].version == 8

            # Test second page
            page2 = await service.get_version_history(v1.uuid, page=2, page_size=3)
            assert len(page2) == 3
            assert page2[0].version == 7
            assert page2[1].version == 6
            assert page2[2].version == 5

            # Test third page
            page3 = await service.get_version_history(v1.uuid, page=3, page_size=3)
            assert len(page3) == 3
            assert page3[0].version == 4
            assert page3[1].version == 3
            assert page3[2].version == 2

            # Test fourth page (only 1 item left)
            page4 = await service.get_version_history(v1.uuid, page=4, page_size=3)
            assert len(page4) == 1
            assert page4[0].version == 1  # Oldest

        @pytest.mark.asyncio
        async def test_get_version_history_default_page_size(self, clean_database):
            """
            Test that get_version_history uses default page_size of 100.

            Validates that get_version_history:
            - Defaults to page_size=100 when not specified
            """
            from src.schemas.minds import MindUpdate

            service = MindService()

            # Create initial Mind node
            mind_data = MindCreate(
                mind_type="project",
                title="Version 1",
                creator="test@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            )
            v1 = await service.create_mind(mind_data)

            # Create 9 more versions (total 10 versions)
            for i in range(2, 11):
                await service.update_mind(v1.uuid, MindUpdate(title=f"Version {i}"))

            # Get version history without specifying page_size
            history = await service.get_version_history(v1.uuid)

            # Should return all 10 versions (less than default 100)
            assert len(history) == 10
            assert history[0].version == 10
            assert history[9].version == 1

        @pytest.mark.asyncio
        async def test_get_version_history_nonexistent_uuid_raises_error(self, clean_database):
            """
            Test that get_version_history raises MindNotFoundError for non-existent UUID.

            Validates error handling for non-existent UUIDs.
            """
            from uuid import uuid4

            from src.exceptions import MindNotFoundError

            service = MindService()

            # Try to get version history for non-existent UUID
            nonexistent_uuid = uuid4()

            with pytest.raises(MindNotFoundError) as exc_info:
                await service.get_version_history(nonexistent_uuid)

            # Verify the error message contains the UUID
            assert str(nonexistent_uuid) in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_get_version_history_tracks_timestamp_changes(self, clean_database):
            """
            Test that version history includes different timestamps for each version.

            Validates that get_version_history:
            - Includes update timestamp for each version (Requirement 6.4)
            - Timestamps increase with each version
            """
            import asyncio

            from src.schemas.minds import MindUpdate

            service = MindService()

            # Create initial Mind node
            mind_data = MindCreate(
                mind_type="project",
                title="Version 1",
                creator="test@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            )
            v1 = await service.create_mind(mind_data)

            # Wait and create version 2
            await asyncio.sleep(0.1)
            await service.update_mind(v1.uuid, MindUpdate(title="Version 2"))

            # Wait and create version 3
            await asyncio.sleep(0.1)
            await service.update_mind(v1.uuid, MindUpdate(title="Version 3"))

            # Get version history
            history = await service.get_version_history(v1.uuid)

            # Verify all versions have timestamps
            assert all(version.updated_at is not None for version in history)

            # Verify timestamps increase from oldest to newest
            # history[2] is oldest (version 1), history[0] is newest (version 3)
            assert history[2].updated_at < history[1].updated_at
            assert history[1].updated_at < history[0].updated_at

        @pytest.mark.asyncio
        async def test_get_version_history_with_different_mind_types(self, clean_database):
            """
            Test that version history works correctly for different Mind types.

            Validates that get_version_history works with various derived types.
            """
            from src.schemas.minds import MindUpdate

            service = MindService()

            # Test with Task type
            task_data = MindCreate(
                mind_type="task",
                title="Task Version 1",
                creator="dev@example.com",
                type_specific_attributes={
                    "priority": "low",
                    "assignee": "dev@example.com",
                },
            )
            task = await service.create_mind(task_data)
            await service.update_mind(task.uuid, MindUpdate(title="Task Version 2"))

            task_history = await service.get_version_history(task.uuid)
            assert len(task_history) == 2
            assert all(v.mind_type == "task" for v in task_history)

            # Test with Risk type
            risk_data = MindCreate(
                mind_type="risk",
                title="Risk Version 1",
                creator="admin@example.com",
                type_specific_attributes={
                    "severity": "low",
                    "probability": "unlikely",
                },
            )
            risk = await service.create_mind(risk_data)
            await service.update_mind(risk.uuid, MindUpdate(title="Risk Version 2"))

            risk_history = await service.get_version_history(risk.uuid)
            assert len(risk_history) == 2
            assert all(v.mind_type == "risk" for v in risk_history)



class TestMindServiceDelete:
    """Test suite for MindService.delete_mind method."""

    @pytest.mark.asyncio
    async def test_soft_delete_creates_new_version_with_deleted_status(self, clean_database):
        """
        Test that soft delete creates a new version with status="deleted".

        Validates that delete_mind with soft delete:
        - Creates a new version (Requirement 7.2)
        - Sets status to "deleted" (Requirement 7.1)
        - Follows version history rules (increments version, creates PREVIOUS relationship)
        - Preserves UUID and creator
        """
        from src.models.enums import StatusEnum

        service = MindService()

        # Create a Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Project to Delete",
            description="This project will be soft deleted",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        created = await service.create_mind(mind_data)
        original_uuid = created.uuid
        original_creator = created.creator

        # Perform soft delete (default behavior)
        result = await service.delete_mind(created.uuid)

        # Verify deletion was successful
        assert result is True

        # Retrieve the node to verify it has deleted status
        deleted_node = await service.get_mind(original_uuid)

        # Verify status is "deleted" (Requirement 7.1)
        assert deleted_node.status == StatusEnum.DELETED

        # Verify new version was created (Requirement 7.2)
        assert deleted_node.version == 2

        # Verify UUID and creator are preserved
        assert deleted_node.uuid == original_uuid
        assert deleted_node.creator == original_creator

        # Verify version history shows both versions
        history = await service.get_version_history(original_uuid)
        assert len(history) == 2
        assert history[0].status == StatusEnum.DELETED  # Latest version
        assert history[1].status != StatusEnum.DELETED  # Original version

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_all_attributes(self, clean_database):
        """
        Test that soft delete preserves all node attributes except status.

        Validates that soft delete follows version history rules by preserving
        all unchanged attributes.
        """
        from src.models.enums import StatusEnum

        service = MindService()

        # Create a Task Mind node with specific attributes
        mind_data = MindCreate(
            mind_type="task",
            title="Task to Delete",
            description="Important task",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
                "due_date": "2024-02-01",
                "estimated_hours": 8.0,
            },
        )
        created = await service.create_mind(mind_data)

        # Perform soft delete
        await service.delete_mind(created.uuid)

        # Retrieve the deleted node
        deleted_node = await service.get_mind(created.uuid)

        # Verify all attributes are preserved except status
        assert deleted_node.title == "Task to Delete"
        assert deleted_node.description == "Important task"
        assert deleted_node.creator == "dev@example.com"
        assert deleted_node.type_specific_attributes["priority"] == "high"
        assert deleted_node.type_specific_attributes["assignee"] == "dev@example.com"
        assert deleted_node.type_specific_attributes["due_date"] == "2024-02-01"
        assert deleted_node.type_specific_attributes["estimated_hours"] == 8.0

        # Only status should change
        assert deleted_node.status == StatusEnum.DELETED

    @pytest.mark.asyncio
    async def test_hard_delete_removes_all_versions(self, clean_database):
        """
        Test that hard delete removes all versions of a Mind node.

        Validates that delete_mind with hard_delete=True:
        - Removes all versions from the database (Requirement 7.3)
        - Removes all PREVIOUS relationships (Requirement 7.4)
        """
        from src.exceptions import MindNotFoundError

        service = MindService()

        # Create a Mind node
        mind_data = MindCreate(
            mind_type="project",
            title="Project Version 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        created = await service.create_mind(mind_data)
        node_uuid = created.uuid

        # Create multiple versions
        from src.schemas.minds import MindUpdate
        await service.update_mind(node_uuid, MindUpdate(title="Project Version 2"))
        await service.update_mind(node_uuid, MindUpdate(title="Project Version 3"))

        # Verify we have 3 versions
        history = await service.get_version_history(node_uuid)
        assert len(history) == 3

        # Perform hard delete with explicit confirmation (Requirement 7.6)
        result = await service.delete_mind(node_uuid, hard_delete=True)

        # Verify deletion was successful
        assert result is True

        # Verify the node no longer exists (Requirements 7.3, 7.4)
        with pytest.raises(MindNotFoundError):
            await service.get_mind(node_uuid)

        # Verify version history also fails (all versions removed)
        with pytest.raises(MindNotFoundError):
            await service.get_version_history(node_uuid)

    @pytest.mark.asyncio
    async def test_hard_delete_requires_explicit_parameter(self, clean_database):
        """
        Test that hard delete requires explicit hard_delete=True parameter.

        Validates that delete_mind defaults to soft delete unless explicitly
        requested (Requirement 7.6).
        """
        from src.models.enums import StatusEnum

        service = MindService()

        # Create a Mind node
        mind_data = MindCreate(
            mind_type="task",
            title="Task to Delete",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "medium",
                "assignee": "dev@example.com",
            },
        )
        created = await service.create_mind(mind_data)

        # Call delete_mind without hard_delete parameter (should default to soft delete)
        await service.delete_mind(created.uuid)

        # Verify node still exists with deleted status (soft delete was performed)
        deleted_node = await service.get_mind(created.uuid)
        assert deleted_node.status == StatusEnum.DELETED

        # Node should still be retrievable (not hard deleted)
        assert deleted_node.uuid == created.uuid

    @pytest.mark.asyncio
    async def test_delete_nonexistent_uuid_raises_error(self, clean_database):
        """
        Test that deleting a non-existent UUID raises MindNotFoundError.

        Validates error handling for non-existent UUIDs (Requirement 7.5).
        """
        from uuid import uuid4

        from src.exceptions import MindNotFoundError

        service = MindService()

        # Try to delete non-existent UUID
        nonexistent_uuid = uuid4()

        # Should raise MindNotFoundError for both soft and hard delete
        with pytest.raises(MindNotFoundError):
            await service.delete_mind(nonexistent_uuid)

        with pytest.raises(MindNotFoundError):
            await service.delete_mind(nonexistent_uuid, hard_delete=True)

    @pytest.mark.asyncio
    async def test_soft_delete_multiple_times(self, clean_database):
        """
        Test that soft deleting an already deleted node creates another version.

        Validates that soft delete can be called multiple times, creating
        additional versions each time.
        """
        from src.models.enums import StatusEnum

        service = MindService()

        # Create a Mind node
        mind_data = MindCreate(
            mind_type="knowledge",
            title="Knowledge Article",
            creator="author@example.com",
            type_specific_attributes={
                "category": "Technical",
                "tags": ["test"],
                "content": "Test content",
            },
        )
        created = await service.create_mind(mind_data)

        # Soft delete once
        await service.delete_mind(created.uuid)
        first_delete = await service.get_mind(created.uuid)
        assert first_delete.version == 2
        assert first_delete.status == StatusEnum.DELETED

        # Soft delete again (should create version 3)
        await service.delete_mind(created.uuid)
        second_delete = await service.get_mind(created.uuid)
        assert second_delete.version == 3
        assert second_delete.status == StatusEnum.DELETED

        # Verify version history shows all versions
        history = await service.get_version_history(created.uuid)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_hard_delete_with_different_mind_types(self, clean_database):
        """
        Test that hard delete works correctly for different Mind types.

        Validates that hard delete works with various derived types.
        """
        from src.exceptions import MindNotFoundError

        service = MindService()

        # Test with Project type
        project_data = MindCreate(
            mind_type="project",
            title="Project to Hard Delete",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        project = await service.create_mind(project_data)
        await service.delete_mind(project.uuid, hard_delete=True)

        with pytest.raises(MindNotFoundError):
            await service.get_mind(project.uuid)

        # Test with Risk type
        risk_data = MindCreate(
            mind_type="risk",
            title="Risk to Hard Delete",
            creator="admin@example.com",
            type_specific_attributes={
                "severity": "low",
                "probability": "unlikely",
            },
        )
        risk = await service.create_mind(risk_data)
        await service.delete_mind(risk.uuid, hard_delete=True)

        with pytest.raises(MindNotFoundError):
            await service.get_mind(risk.uuid)

    @pytest.mark.asyncio
    async def test_soft_delete_updates_timestamp(self, clean_database):
        """
        Test that soft delete updates the timestamp.

        Validates that soft delete creates a new version with updated timestamp.
        """
        import asyncio

        service = MindService()

        # Create a Mind node
        mind_data = MindCreate(
            mind_type="milestone",
            title="Milestone to Delete",
            creator="pm@example.com",
            type_specific_attributes={
                "target_date": "2024-06-01",
                "completion_percentage": 0.0,
            },
        )
        created = await service.create_mind(mind_data)
        original_timestamp = created.updated_at

        # Wait a bit to ensure timestamp difference
        await asyncio.sleep(0.1)

        # Perform soft delete
        await service.delete_mind(created.uuid)

        # Retrieve the deleted node
        deleted_node = await service.get_mind(created.uuid)

        # Verify timestamp was updated
        assert deleted_node.updated_at > original_timestamp



class TestMindServiceCreateRelationship:
    """Test suite for MindService.create_relationship method."""

    @pytest.mark.asyncio
    async def test_create_relationship_contains(self, clean_database):
        """
        Test creating a 'contains' relationship between two Mind nodes.

        Validates that create_relationship:
        - Creates a typed relationship (Requirement 8.2)
        - Stores relationship in Neo4j (Requirement 8.4)
        - Returns complete relationship data
        """
        service = MindService()

        # Create source node (project)
        project_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        project = await service.create_mind(project_data)

        # Create target node (phase)
        phase_data = MindCreate(
            mind_type="phase",
            title="Test Phase",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        phase = await service.create_mind(phase_data)

        # Create relationship
        relationship = await service.create_relationship(
            project.uuid, phase.uuid, "contains"
        )

        # Verify relationship data (Requirement 8.4)
        assert relationship.relationship_type == "contains"
        assert relationship.source_uuid == project.uuid
        assert relationship.target_uuid == phase.uuid
        assert relationship.created_at is not None
        assert isinstance(relationship.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_relationship_depends_on(self, clean_database):
        """
        Test creating a 'depends_on' relationship between tasks.

        Validates that create_relationship supports depends_on type (Requirement 8.2).
        """
        service = MindService()

        # Create two task nodes
        task1_data = MindCreate(
            mind_type="task",
            title="Task 1",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        task1 = await service.create_mind(task1_data)

        task2_data = MindCreate(
            mind_type="task",
            title="Task 2",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "medium",
                "assignee": "dev@example.com",
            },
        )
        task2 = await service.create_mind(task2_data)

        # Create depends_on relationship (task2 depends on task1)
        relationship = await service.create_relationship(
            task2.uuid, task1.uuid, "depends_on"
        )

        # Verify relationship
        assert relationship.relationship_type == "depends_on"
        assert relationship.source_uuid == task2.uuid
        assert relationship.target_uuid == task1.uuid

    @pytest.mark.asyncio
    async def test_create_relationship_assigned_to(self, clean_database):
        """
        Test creating an 'assigned_to' relationship.

        Validates that create_relationship supports assigned_to type (Requirement 8.2).
        """
        service = MindService()

        # Create task node
        task_data = MindCreate(
            mind_type="task",
            title="Assigned Task",
            creator="pm@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        task = await service.create_mind(task_data)

        # Create resource node (replaces employee)
        resource_data = MindCreate(
            mind_type="resource",
            title="John Doe",
            creator="hr@example.com",
            type_specific_attributes={
                "email": "john.doe@example.com",
                "resource_type": "PERSON",
                "efficiency": 1.0,
                "daily_rate": 800.0,
            },
        )
        resource = await service.create_mind(resource_data)

        # Create assigned_to relationship
        relationship = await service.create_relationship(
            task.uuid, resource.uuid, "assigned_to"
        )

        # Verify relationship
        assert relationship.relationship_type == "assigned_to"
        assert relationship.source_uuid == task.uuid
        assert relationship.target_uuid == resource.uuid

    @pytest.mark.asyncio
    async def test_create_relationship_relates_to(self, clean_database):
        """
        Test creating a 'relates_to' relationship.

        Validates that create_relationship supports relates_to type (Requirement 8.2).
        """
        service = MindService()

        # Create two design nodes
        design_input_data = MindCreate(
            mind_type="design_input",
            title="User Requirements",
            creator="analyst@example.com",
            type_specific_attributes={
                "source": "Customer",
                "input_type": "Requirements",
                "content": "User needs authentication",
            },
        )
        design_input = await service.create_mind(design_input_data)

        design_output_data = MindCreate(
            mind_type="design_output",
            title="Authentication Design",
            creator="architect@example.com",
            type_specific_attributes={
                "output_type": "Technical Design",
                "verification_status": "Pending",
                "content": "JWT-based authentication design",
            },
        )
        design_output = await service.create_mind(design_output_data)

        # Create relates_to relationship
        relationship = await service.create_relationship(
            design_output.uuid, design_input.uuid, "relates_to"
        )

        # Verify relationship
        assert relationship.relationship_type == "relates_to"
        assert relationship.source_uuid == design_output.uuid
        assert relationship.target_uuid == design_input.uuid

    @pytest.mark.asyncio
    async def test_create_relationship_implements(self, clean_database):
        """
        Test creating an 'implements' relationship.

        Validates that create_relationship supports implements type (Requirement 8.2).
        """
        service = MindService()

        # Create acceptance criteria node
        criteria_data = MindCreate(
            mind_type="acceptance_criteria",
            title="Login Criteria",
            creator="pm@example.com",
            type_specific_attributes={
                "criteria_text": "User can login with email and password",
                "verification_method": "Manual Testing",
                "verification_status": "pending",
            },
        )
        criteria = await service.create_mind(criteria_data)

        # Create user story node
        story_data = MindCreate(
            mind_type="user_story",
            title="User Login",
            creator="pm@example.com",
            type_specific_attributes={
                "as_a": "user",
                "i_want": "to login",
                "so_that": "I can access my account",
                "acceptance_criteria_ids": [],
            },
        )
        story = await service.create_mind(story_data)

        # Create implements relationship
        relationship = await service.create_relationship(
            criteria.uuid, story.uuid, "implements"
        )

        # Verify relationship
        assert relationship.relationship_type == "implements"
        assert relationship.source_uuid == criteria.uuid
        assert relationship.target_uuid == story.uuid

    @pytest.mark.asyncio
    async def test_create_relationship_mitigates(self, clean_database):
        """
        Test creating a 'mitigates' relationship.

        Validates that create_relationship supports mitigates type (Requirement 8.2).
        """
        service = MindService()

        # Create risk node
        risk_data = MindCreate(
            mind_type="risk",
            title="Data Loss Risk",
            creator="admin@example.com",
            type_specific_attributes={
                "severity": "high",
                "probability": "unlikely",
                "mitigation_plan": "Implement backup strategy",
            },
        )
        risk = await service.create_mind(risk_data)

        # Create failure node
        failure_data = MindCreate(
            mind_type="failure",
            title="Database Failure",
            creator="admin@example.com",
            type_specific_attributes={
                "failure_mode": "Database crash",
                "effects": "Data loss",
                "causes": "Hardware failure",
                "detection_method": "Monitoring alerts",
            },
        )
        failure = await service.create_mind(failure_data)

        # Create mitigates relationship
        relationship = await service.create_relationship(
            risk.uuid, failure.uuid, "mitigates"
        )

        # Verify relationship
        assert relationship.relationship_type == "mitigates"
        assert relationship.source_uuid == risk.uuid
        assert relationship.target_uuid == failure.uuid

    @pytest.mark.asyncio
    async def test_create_relationship_validates_source_uuid_exists(self, clean_database):
        """
        Test that create_relationship validates source UUID exists.

        Validates that create_relationship:
        - Validates source UUID exists (Requirement 8.3)
        - Raises MindNotFoundError for non-existent source
        """
        from uuid import uuid4

        from src.exceptions import MindNotFoundError

        service = MindService()

        # Create target node
        target_data = MindCreate(
            mind_type="task",
            title="Target Task",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "medium",
                "assignee": "dev@example.com",
            },
        )
        target = await service.create_mind(target_data)

        # Try to create relationship with non-existent source UUID
        fake_source_uuid = uuid4()

        with pytest.raises(MindNotFoundError) as exc_info:
            await service.create_relationship(
                fake_source_uuid, target.uuid, "depends_on"
            )

        # Verify error message contains the UUID
        assert str(fake_source_uuid) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_relationship_validates_target_uuid_exists(self, clean_database):
        """
        Test that create_relationship validates target UUID exists.

        Validates that create_relationship:
        - Validates target UUID exists (Requirement 8.3)
        - Raises MindNotFoundError for non-existent target
        """
        from uuid import uuid4

        from src.exceptions import MindNotFoundError

        service = MindService()

        # Create source node
        source_data = MindCreate(
            mind_type="task",
            title="Source Task",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        source = await service.create_mind(source_data)

        # Try to create relationship with non-existent target UUID
        fake_target_uuid = uuid4()

        with pytest.raises(MindNotFoundError) as exc_info:
            await service.create_relationship(
                source.uuid, fake_target_uuid, "depends_on"
            )

        # Verify error message contains the UUID
        assert str(fake_target_uuid) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_relationship_prevents_duplicates(self, clean_database):
        """
        Test that create_relationship prevents duplicate relationships.

        Validates that create_relationship:
        - Prevents duplicate relationships (Requirement 8.6)
        - Raises MindRelationshipError for duplicates
        """
        from src.exceptions import MindRelationshipError

        service = MindService()

        # Create two nodes
        node1_data = MindCreate(
            mind_type="project",
            title="Project 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node1 = await service.create_mind(node1_data)

        node2_data = MindCreate(
            mind_type="phase",
            title="Phase 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        node2 = await service.create_mind(node2_data)

        # Create relationship
        await service.create_relationship(node1.uuid, node2.uuid, "contains")

        # Try to create the same relationship again
        with pytest.raises(MindRelationshipError) as exc_info:
            await service.create_relationship(node1.uuid, node2.uuid, "contains")

        # Verify error message mentions duplicate
        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_relationship_allows_different_types_same_nodes(self, clean_database):
        """
        Test that different relationship types between same nodes are allowed.

        Validates that create_relationship allows multiple relationship types
        between the same two nodes (only same type+direction is duplicate).
        """
        service = MindService()

        # Create two nodes
        node1_data = MindCreate(
            mind_type="task",
            title="Task 1",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        node1 = await service.create_mind(node1_data)

        node2_data = MindCreate(
            mind_type="task",
            title="Task 2",
            creator="dev@example.com",
            type_specific_attributes={
                "priority": "medium",
                "assignee": "dev@example.com",
            },
        )
        node2 = await service.create_mind(node2_data)

        # Create depends_on relationship
        rel1 = await service.create_relationship(node1.uuid, node2.uuid, "depends_on")
        assert rel1.relationship_type == "depends_on"

        # Create relates_to relationship (different type, should succeed)
        rel2 = await service.create_relationship(node1.uuid, node2.uuid, "relates_to")
        assert rel2.relationship_type == "relates_to"

        # Both relationships should exist
        assert rel1.source_uuid == rel2.source_uuid
        assert rel1.target_uuid == rel2.target_uuid

    @pytest.mark.asyncio
    async def test_create_relationship_invalid_type_raises_error(self, clean_database):
        """
        Test that create_relationship rejects invalid relationship types.

        Validates that create_relationship validates relationship type.
        """
        service = MindService()

        # Create two nodes
        node1_data = MindCreate(
            mind_type="project",
            title="Project 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node1 = await service.create_mind(node1_data)

        node2_data = MindCreate(
            mind_type="phase",
            title="Phase 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        node2 = await service.create_mind(node2_data)

        # Try to create relationship with invalid type
        with pytest.raises(ValueError) as exc_info:
            await service.create_relationship(node1.uuid, node2.uuid, "invalid_type")

        # Verify error message mentions invalid type
        assert "Invalid relationship_type" in str(exc_info.value)
        assert "invalid_type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_relationship_timestamp_is_recent(self, clean_database):
        """
        Test that create_relationship sets a recent timestamp.

        Validates that the created_at timestamp is set to current time.
        """
        service = MindService()

        # Create two nodes
        node1_data = MindCreate(
            mind_type="project",
            title="Project 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node1 = await service.create_mind(node1_data)

        node2_data = MindCreate(
            mind_type="phase",
            title="Phase 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        node2 = await service.create_mind(node2_data)

        # Create relationship
        relationship = await service.create_relationship(
            node1.uuid, node2.uuid, "contains"
        )

        # Verify timestamp is recent (within last 10 seconds)
        time_diff = datetime.now(timezone.utc) - relationship.created_at
        assert time_diff.total_seconds() < 10

    @pytest.mark.asyncio
    async def test_create_relationship_with_all_supported_types(self, clean_database):
        """
        Test that all supported relationship types can be created.

        Validates that create_relationship supports all 6 relationship types
        defined in Requirement 8.2.
        """
        service = MindService()

        # Create nodes for testing all relationship types
        nodes = []
        for i in range(6):
            node_data = MindCreate(
                mind_type="knowledge",
                title=f"Node {i}",
                creator="test@example.com",
                type_specific_attributes={
                    "category": "Test",
                    "tags": ["test"],
                    "content": f"Content {i}",
                },
            )
            node = await service.create_mind(node_data)
            nodes.append(node)

        # Test all 6 relationship types
        relationship_types = [
            "contains",
            "depends_on",
            "assigned_to",
            "relates_to",
            "implements",
            "mitigates",
        ]

        for i, rel_type in enumerate(relationship_types):
            relationship = await service.create_relationship(
                nodes[i].uuid, nodes[(i + 1) % 6].uuid, rel_type
            )
            assert relationship.relationship_type == rel_type
            assert relationship.source_uuid == nodes[i].uuid
            assert relationship.target_uuid == nodes[(i + 1) % 6].uuid


class TestMindService:
    """Test suite for MindService.get_relationships method."""

    @pytest.mark.asyncio
    async def test_get_relationships(self, clean_database):
        """
        Test that get_relationships retrieves relationships correctly.

        Validates that get_relationships:
        - Retrieves outgoing relationships when direction="outgoing"
        - Retrieves incoming relationships when direction="incoming"
        - Retrieves both directions when direction="both"
        - Filters by relationship type when specified
        - Returns correct relationship data (type, source, target, created_at)
        """
        service = MindService()

        # Create three nodes
        node1_data = MindCreate(
            mind_type="project",
            title="Project A",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node1 = await service.create_mind(node1_data)

        node2_data = MindCreate(
            mind_type="phase",
            title="Phase 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        node2 = await service.create_mind(node2_data)

        node3_data = MindCreate(
            mind_type="task",
            title="Task 1",
            creator="test@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        node3 = await service.create_mind(node3_data)

        # Create relationships:
        # node1 -[contains]-> node2
        # node2 -[contains]-> node3
        # node2 -[depends_on]-> node1
        await service.create_relationship(node1.uuid, node2.uuid, "contains")
        await service.create_relationship(node2.uuid, node3.uuid, "contains")
        await service.create_relationship(node2.uuid, node1.uuid, "depends_on")

        # Test 1: Get all relationships for node2 (both directions)
        relationships = await service.get_relationships(node2.uuid, direction="both")
        assert len(relationships) == 3

        # Verify relationship types and directions
        rel_types = {(r.relationship_type, str(r.source_uuid), str(r.target_uuid)) for r in relationships}
        assert ("contains", str(node1.uuid), str(node2.uuid)) in rel_types
        assert ("contains", str(node2.uuid), str(node3.uuid)) in rel_types
        assert ("depends_on", str(node2.uuid), str(node1.uuid)) in rel_types

        # Test 2: Get only outgoing relationships for node2
        outgoing = await service.get_relationships(node2.uuid, direction="outgoing")
        assert len(outgoing) == 2
        for rel in outgoing:
            assert rel.source_uuid == node2.uuid

        # Test 3: Get only incoming relationships for node2
        incoming = await service.get_relationships(node2.uuid, direction="incoming")
        assert len(incoming) == 1
        assert incoming[0].target_uuid == node2.uuid
        assert incoming[0].relationship_type == "contains"

        # Test 4: Filter by relationship type
        contains_rels = await service.get_relationships(
            node2.uuid, relationship_type="contains", direction="both"
        )
        assert len(contains_rels) == 2
        for rel in contains_rels:
            assert rel.relationship_type == "contains"

        depends_rels = await service.get_relationships(
            node2.uuid, relationship_type="depends_on", direction="both"
        )
        assert len(depends_rels) == 1
        assert depends_rels[0].relationship_type == "depends_on"

        # Test 5: Verify relationship data completeness
        for rel in relationships:
            assert rel.relationship_type is not None
            assert rel.source_uuid is not None
            assert rel.target_uuid is not None
            assert rel.created_at is not None
            assert rel.properties is not None

    @pytest.mark.asyncio
    async def test_get_relationships_nonexistent_uuid_raises_error(self, clean_database):
        """
        Test that get_relationships raises MindNotFoundError for non-existent UUID.

        Validates error handling for non-existent UUIDs.
        """
        from uuid import uuid4

        from src.exceptions import MindNotFoundError

        service = MindService()

        # Try to get relationships for a non-existent UUID
        nonexistent_uuid = uuid4()

        with pytest.raises(MindNotFoundError) as exc_info:
            await service.get_relationships(nonexistent_uuid)

        # Verify the error message contains the UUID
        assert str(nonexistent_uuid) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_relationships_invalid_direction_raises_error(self, clean_database):
        """
        Test that get_relationships raises ValueError for invalid direction.

        Validates parameter validation for direction parameter.
        """
        service = MindService()

        # Create a node
        node_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node = await service.create_mind(node_data)

        # Try to get relationships with invalid direction
        with pytest.raises(ValueError, match="Invalid direction"):
            await service.get_relationships(node.uuid, direction="invalid")

    @pytest.mark.asyncio
    async def test_get_relationships_invalid_type_raises_error(self, clean_database):
        """
        Test that get_relationships raises ValueError for invalid relationship type.

        Validates parameter validation for relationship_type parameter.
        """
        service = MindService()

        # Create a node
        node_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node = await service.create_mind(node_data)

        # Try to get relationships with invalid type
        with pytest.raises(ValueError, match="Invalid relationship_type"):
            await service.get_relationships(node.uuid, relationship_type="invalid_type")

    @pytest.mark.asyncio
    async def test_get_relationships_no_relationships_returns_empty_list(self, clean_database):
        """
        Test that get_relationships returns empty list when node has no relationships.

        Validates behavior for nodes without relationships.
        """
        service = MindService()

        # Create a node with no relationships
        node_data = MindCreate(
            mind_type="project",
            title="Isolated Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node = await service.create_mind(node_data)

        # Get relationships
        relationships = await service.get_relationships(node.uuid)

        # Verify empty list returned
        assert relationships == []
        assert len(relationships) == 0

    @pytest.mark.asyncio
    async def test_get_relationships_outgoing_only(self, clean_database):
        """
        Test that get_relationships with direction="outgoing" returns only outgoing relationships.

        Validates directional filtering for outgoing relationships.
        """
        service = MindService()

        # Create nodes
        source_data = MindCreate(
            mind_type="project",
            title="Source Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="phase",
            title="Target Phase",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        target = await service.create_mind(target_data)

        # Create relationship: source -> target
        await service.create_relationship(source.uuid, target.uuid, "contains")

        # Get outgoing relationships for source
        outgoing = await service.get_relationships(source.uuid, direction="outgoing")
        assert len(outgoing) == 1
        assert outgoing[0].source_uuid == source.uuid
        assert outgoing[0].target_uuid == target.uuid

        # Get outgoing relationships for target (should be empty)
        target_outgoing = await service.get_relationships(target.uuid, direction="outgoing")
        assert len(target_outgoing) == 0

    @pytest.mark.asyncio
    async def test_get_relationships_incoming_only(self, clean_database):
        """
        Test that get_relationships with direction="incoming" returns only incoming relationships.

        Validates directional filtering for incoming relationships.
        """
        service = MindService()

        # Create nodes
        source_data = MindCreate(
            mind_type="project",
            title="Source Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="phase",
            title="Target Phase",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        target = await service.create_mind(target_data)

        # Create relationship: source -> target
        await service.create_relationship(source.uuid, target.uuid, "contains")

        # Get incoming relationships for target
        incoming = await service.get_relationships(target.uuid, direction="incoming")
        assert len(incoming) == 1
        assert incoming[0].source_uuid == source.uuid
        assert incoming[0].target_uuid == target.uuid

        # Get incoming relationships for source (should be empty)
        source_incoming = await service.get_relationships(source.uuid, direction="incoming")
        assert len(source_incoming) == 0


class TestMindServiceQueryMinds:
    """Test suite for MindService.query_minds method."""

    @pytest.mark.asyncio
    async def test_query_minds(self, clean_database):
        """
        Test basic query_minds functionality with filtering and pagination.

        Validates that query_minds:
        - Returns all nodes when no filters are applied
        - Filters by mind_type correctly (Requirements 4.4, 11.1)
        - Filters by status correctly (Requirements 4.5, 11.2)
        - Filters by creator correctly (Requirement 11.3)
        - Filters by date range correctly (Requirement 11.4)
        - Combines multiple filters with AND logic (Requirement 11.5)
        - Sorts results correctly (Requirement 11.6)
        - Paginates results correctly (Requirement 11.7)
        - Returns only latest versions of nodes
        """
        from datetime import datetime, timedelta, timezone

        from src.models.enums import StatusEnum
        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # Create test nodes with different types, statuses, and creators
        # Node 1: Project, draft status, creator1, older timestamp
        node1_data = MindCreate(
            mind_type="project",
            title="Project Alpha",
            creator="creator1@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node1 = await service.create_mind(node1_data)

        # Node 2: Task, draft status, creator2, newer timestamp
        node2_data = MindCreate(
            mind_type="task",
            title="Task Beta",
            creator="creator2@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        node2 = await service.create_mind(node2_data)

        # Node 3: Project, draft status, creator1, newest timestamp
        node3_data = MindCreate(
            mind_type="project",
            title="Project Gamma",
            creator="creator1@example.com",
            type_specific_attributes={
                "start_date": "2024-02-01",
                "end_date": "2024-12-31",
            },
        )
        node3 = await service.create_mind(node3_data)

        # Update node1 to create a new version (should only return latest)
        from src.schemas.minds import MindUpdate

        update_data = MindUpdate(title="Project Alpha Updated")
        node1_updated = await service.update_mind(node1.uuid, update_data)

        # Test 1: Query all nodes (no filters)
        filters = MindQueryFilters()
        result = await service.query_minds(filters)

        assert result.total == 3  # 3 unique UUIDs
        assert len(result.items) == 3
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 1

        # Verify only latest versions returned
        node1_in_results = [item for item in result.items if item.uuid == node1.uuid]
        assert len(node1_in_results) == 1
        assert node1_in_results[0].version == 2  # Latest version
        assert node1_in_results[0].title == "Project Alpha Updated"

        # Test 2: Filter by mind_type (Requirements 4.4, 11.1)
        filters = MindQueryFilters(mind_type="project")
        result = await service.query_minds(filters)

        assert result.total == 2  # 2 projects
        assert len(result.items) == 2
        for item in result.items:
            assert item.mind_type == "project"

        # Test 3: Filter by creator (Requirement 11.3)
        filters = MindQueryFilters(creator="creator1@example.com")
        result = await service.query_minds(filters)

        assert result.total == 2  # 2 nodes by creator1
        assert len(result.items) == 2
        for item in result.items:
            assert item.creator == "creator1@example.com"

        # Test 4: Combine multiple filters - AND logic (Requirement 11.5)
        filters = MindQueryFilters(
            mind_type="project",
            creator="creator1@example.com"
        )
        result = await service.query_minds(filters)

        assert result.total == 2  # 2 projects by creator1
        assert len(result.items) == 2
        for item in result.items:
            assert item.mind_type == "project"
            assert item.creator == "creator1@example.com"

        # Test 5: Sort by title ascending (Requirement 11.6)
        filters = MindQueryFilters(sort_by="title", sort_order="asc")
        result = await service.query_minds(filters)

        assert len(result.items) == 3
        titles = [item.title for item in result.items]
        assert titles == sorted(titles)  # Verify ascending order

        # Test 6: Sort by title descending (Requirement 11.6)
        filters = MindQueryFilters(sort_by="title", sort_order="desc")
        result = await service.query_minds(filters)

        assert len(result.items) == 3
        titles = [item.title for item in result.items]
        assert titles == sorted(titles, reverse=True)  # Verify descending order

        # Test 7: Pagination (Requirement 11.7)
        filters = MindQueryFilters(page=1, page_size=2, sort_by="title", sort_order="asc")
        result = await service.query_minds(filters)

        assert result.total == 3
        assert len(result.items) == 2  # First page with 2 items
        assert result.page == 1
        assert result.page_size == 2
        assert result.total_pages == 2

        # Get second page
        filters = MindQueryFilters(page=2, page_size=2, sort_by="title", sort_order="asc")
        result = await service.query_minds(filters)

        assert result.total == 3
        assert len(result.items) == 1  # Second page with 1 item
        assert result.page == 2
        assert result.page_size == 2
        assert result.total_pages == 2

        # Test 8: Date range filtering (Requirement 11.4)
        # Query for nodes updated after a time before all nodes were created
        very_old_time = datetime.now(timezone.utc) - timedelta(days=1)

        filters = MindQueryFilters(
            updated_after=very_old_time
        )
        result = await service.query_minds(filters)

        # Should get all 3 nodes since they were all created recently
        assert result.total == 3

        # Test 9: Filter by status (Requirements 4.5, 11.2)
        # Update node2 to have a different status
        update_data = MindUpdate(status=StatusEnum.READY)
        await service.update_mind(node2.uuid, update_data)

        filters = MindQueryFilters(status=StatusEnum.READY)
        result = await service.query_minds(filters)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].uuid == node2.uuid
        assert result.items[0].status == StatusEnum.READY

    @pytest.mark.asyncio
    async def test_query_minds_empty_results(self, clean_database):
        """
        Test that query_minds returns empty results when no nodes match filters.

        Validates behavior when filters match no nodes.
        """
        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # Create a project node
        node_data = MindCreate(
            mind_type="project",
            title="Test Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        await service.create_mind(node_data)

        # Query for a different type
        filters = MindQueryFilters(mind_type="task")
        result = await service.query_minds(filters)

        assert result.total == 0
        assert len(result.items) == 0
        assert result.page == 1
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_query_minds_invalid_mind_type_raises_error(self, clean_database):
        """
        Test that query_minds raises ValueError for invalid mind_type.

        Validates parameter validation for mind_type filter.
        """
        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # This should fail at the Pydantic validation level, but if it somehow
        # gets through, the service should catch it
        # Note: Pydantic validation in MindQueryFilters should prevent this
        # but we test the service layer validation as well

        # Create a filter with an invalid mind_type by bypassing validation
        filters = MindQueryFilters.model_construct(mind_type="invalid_type")

        with pytest.raises(ValueError, match="Unsupported mind_type"):
            await service.query_minds(filters)

    @pytest.mark.asyncio
    async def test_query_minds_sort_by_version(self, clean_database):
        """
        Test that query_minds can sort by version number.

        Validates sorting by version field (Requirement 11.6).
        """
        from src.schemas.minds import MindQueryFilters, MindUpdate

        service = MindService()

        # Create nodes
        node1_data = MindCreate(
            mind_type="project",
            title="Project 1",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node1 = await service.create_mind(node1_data)

        node2_data = MindCreate(
            mind_type="project",
            title="Project 2",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node2 = await service.create_mind(node2_data)

        # Update node1 multiple times to increase version
        for i in range(3):
            update_data = MindUpdate(title=f"Project 1 v{i+2}")
            await service.update_mind(node1.uuid, update_data)

        # Query sorted by version descending
        filters = MindQueryFilters(sort_by="version", sort_order="desc")
        result = await service.query_minds(filters)

        assert len(result.items) == 2
        # node1 should be first (version 4), node2 second (version 1)
        assert result.items[0].uuid == node1.uuid
        assert result.items[0].version == 4
        assert result.items[1].uuid == node2.uuid
        assert result.items[1].version == 1

    @pytest.mark.asyncio
    async def test_query_minds_date_range_filtering(self, clean_database):
        """
        Test that query_minds filters by date range correctly.

        Validates date range filtering (Requirement 11.4).
        """
        from datetime import timedelta

        from src.schemas.minds import MindQueryFilters

        service = MindService()

        # Create nodes at different times
        node1_data = MindCreate(
            mind_type="project",
            title="Old Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node1 = await service.create_mind(node1_data)

        # Wait a moment to ensure different timestamps
        import asyncio
        await asyncio.sleep(0.1)

        node2_data = MindCreate(
            mind_type="project",
            title="New Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        node2 = await service.create_mind(node2_data)

        # Query for nodes updated after node1
        filters = MindQueryFilters(
            updated_after=node1.updated_at + timedelta(milliseconds=50)
        )
        result = await service.query_minds(filters)

        assert result.total == 1
        assert result.items[0].uuid == node2.uuid

        # Query for nodes updated before node2
        filters = MindQueryFilters(
            updated_before=node2.updated_at - timedelta(milliseconds=50)
        )
        result = await service.query_minds(filters)

        assert result.total == 1
        assert result.items[0].uuid == node1.uuid

        # Query for nodes in a range
        filters = MindQueryFilters(
            updated_after=node1.updated_at - timedelta(seconds=1),
            updated_before=node2.updated_at + timedelta(seconds=1)
        )
        result = await service.query_minds(filters)

        assert result.total == 2


class TestMindServiceBulkOperations:
    """Test suite for MindService bulk operations (bulk_create and bulk_update)."""

    async def test_bulk_create_multiple_minds(self, clean_database):
        """
        Test that bulk_create successfully creates multiple Mind nodes.
        Validates Requirement 10.1, 10.3, 10.4.
        """
        service = MindService()

        minds_data = [
            MindCreate(
                mind_type="project",
                title="Project 1",
                creator="user@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            ),
            MindCreate(
                mind_type="task",
                title="Task 1",
                creator="user@example.com",
                type_specific_attributes={
                    "priority": "high",
                    "assignee": "dev@example.com"
                }
            ),
            MindCreate(
                mind_type="risk",
                title="Risk 1",
                creator="user@example.com",
                type_specific_attributes={
                    "severity": "high",
                    "probability": "likely"
                }
            )
        ]

        # Create all nodes
        created_nodes = await service.bulk_create(minds_data)

        # Verify all nodes were created
        assert len(created_nodes) == 3
        assert created_nodes[0].mind_type == "project"
        assert created_nodes[0].title == "Project 1"
        assert created_nodes[1].mind_type == "task"
        assert created_nodes[1].title == "Task 1"
        assert created_nodes[2].mind_type == "risk"
        assert created_nodes[2].title == "Risk 1"

        # Verify all have version 1
        for node in created_nodes:
            assert node.version == 1

    async def test_bulk_create_validates_all_before_creating(self, clean_database):
        """
        Test that bulk_create validates all items before creating any.
        Validates Requirement 10.1, 10.2.
        """
        service = MindService()

        minds_data = [
            MindCreate(
                mind_type="project",
                title="Valid Project",
                creator="user@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            ),
            MindCreate(
                mind_type="project",
                title="Invalid Project - Missing dates",
                creator="user@example.com",
                type_specific_attributes={}  # Missing required start_date and end_date
            )
        ]

        # Should raise ValueError due to missing required attributes
        with pytest.raises(ValueError) as exc_info:
            await service.bulk_create(minds_data)

        assert "Bulk create validation failed" in str(exc_info.value)

        # Verify no nodes were created
        filters = MindQueryFilters(mind_type="project")
        result = await service.query_minds(filters)
        assert result.total == 0

    async def test_bulk_create_rejects_batch_exceeding_100(self, clean_database):
        """
        Test that bulk_create rejects batches exceeding 100 nodes.
        Validates Requirement 10.5.
        """
        service = MindService()

        # Create 101 minds
        minds_data = [
            MindCreate(
                mind_type="task",
                title=f"Task {i}",
                creator="user@example.com",
                type_specific_attributes={
                    "priority": "low",
                    "assignee": "dev@example.com"
                }
            )
            for i in range(101)
        ]

        # Should raise ValueError due to batch size
        with pytest.raises(ValueError) as exc_info:
            await service.bulk_create(minds_data)

        assert "exceeds maximum of 100 nodes" in str(exc_info.value)

    async def test_bulk_create_validates_type_specific_attributes(self, clean_database):
        """
        Test that bulk_create validates type-specific attributes.
        Validates Requirement 10.1, 10.2.
        """
        service = MindService()

        minds_data = [
            MindCreate(
                mind_type="project",
                title="Project 1",
                creator="user@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            ),
            MindCreate(
                mind_type="project",
                title="Project 2 - Missing dates",
                creator="user@example.com",
                type_specific_attributes={}  # Missing required start_date and end_date
            )
        ]

        # Should raise ValueError due to missing required attributes
        with pytest.raises(ValueError) as exc_info:
            await service.bulk_create(minds_data)

        assert "Bulk create validation failed" in str(exc_info.value)

    async def test_bulk_update_multiple_minds(self, clean_database):
        """
        Test that bulk_update successfully updates multiple Mind nodes.
        Validates Requirement 10.2, 10.3, 10.4.
        """
        service = MindService()

        # Create initial nodes
        node1 = await service.create_mind(
            MindCreate(
                mind_type="task",
                title="Task 1",
                creator="user@example.com",
                type_specific_attributes={
                    "priority": "low",
                    "assignee": "dev1@example.com"
                }
            )
        )

        node2 = await service.create_mind(
            MindCreate(
                mind_type="task",
                title="Task 2",
                creator="user@example.com",
                type_specific_attributes={
                    "priority": "medium",
                    "assignee": "dev2@example.com"
                }
            )
        )

        # Update both nodes
        updates_data = [
            MindBulkUpdate(
                uuid=node1.uuid,
                title="Updated Task 1",
                type_specific_attributes={"priority": "high"}
            ),
            MindBulkUpdate(
                uuid=node2.uuid,
                title="Updated Task 2",
                type_specific_attributes={"priority": "critical"}
            )
        ]

        updated_nodes = await service.bulk_update(updates_data)

        # Verify all nodes were updated
        assert len(updated_nodes) == 2
        assert updated_nodes[0].title == "Updated Task 1"
        assert updated_nodes[0].type_specific_attributes["priority"] == "high"
        assert updated_nodes[0].version == 2
        assert updated_nodes[1].title == "Updated Task 2"
        assert updated_nodes[1].type_specific_attributes["priority"] == "critical"
        assert updated_nodes[1].version == 2

    async def test_bulk_update_validates_all_before_updating(self, clean_database):
        """
        Test that bulk_update validates all items before updating any.
        Validates Requirement 10.1, 10.2.
        """
        service = MindService()

        # Create initial node
        node1 = await service.create_mind(
            MindCreate(
                mind_type="task",
                title="Task 1",
                creator="user@example.com",
                type_specific_attributes={
                    "priority": "low",
                    "assignee": "dev@example.com"
                }
            )
        )

        from uuid import uuid4

        # One valid update, one with non-existent UUID
        updates_data = [
            MindBulkUpdate(
                uuid=node1.uuid,
                title="Updated Task 1"
            ),
            MindBulkUpdate(
                uuid=uuid4(),  # Non-existent UUID
                title="This should fail"
            )
        ]

        # Should raise ValueError due to non-existent UUID
        with pytest.raises(ValueError) as exc_info:
            await service.bulk_update(updates_data)

        assert "Bulk update validation failed" in str(exc_info.value)
        assert "not found in database" in str(exc_info.value)

        # Verify first node was not updated
        retrieved = await service.get_mind(node1.uuid)
        assert retrieved.title == "Task 1"  # Original title
        assert retrieved.version == 1  # Still version 1

    async def test_bulk_update_rejects_batch_exceeding_100(self, clean_database):
        """
        Test that bulk_update rejects batches exceeding 100 nodes.
        Validates Requirement 10.5.
        """
        service = MindService()

        from uuid import uuid4

        # Create 101 updates
        updates_data = [
            MindBulkUpdate(
                uuid=uuid4(),
                title=f"Updated Task {i}"
            )
            for i in range(101)
        ]

        # Should raise ValueError due to batch size
        with pytest.raises(ValueError) as exc_info:
            await service.bulk_update(updates_data)

        assert "exceeds maximum of 100 nodes" in str(exc_info.value)

    async def test_bulk_update_validates_type_specific_attributes(self, clean_database):
        """
        Test that bulk_update validates type-specific attributes.
        Validates Requirement 10.1, 10.2.
        """
        service = MindService()

        # Create initial node
        node1 = await service.create_mind(
            MindCreate(
                mind_type="project",
                title="Project 1",
                creator="user@example.com",
                type_specific_attributes={
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            )
        )

        # Try to update with invalid date format
        updates_data = [
            MindBulkUpdate(
                uuid=node1.uuid,
                type_specific_attributes={
                    "start_date": "invalid-date"  # Invalid date format
                }
            )
        ]

        # Should raise ValueError due to invalid date
        with pytest.raises(ValueError) as exc_info:
            await service.bulk_update(updates_data)

        assert "Bulk update validation failed" in str(exc_info.value)

    async def test_bulk_update_requires_at_least_one_field(self, clean_database):
        """
        Test that bulk_update requires at least one field to update.
        Validates Requirement 10.1.
        """
        service = MindService()

        # Create initial node
        node1 = await service.create_mind(
            MindCreate(
                mind_type="task",
                title="Task 1",
                creator="user@example.com",
                type_specific_attributes={
                    "priority": "low",
                    "assignee": "dev@example.com"
                }
            )
        )

        # Update with no fields
        updates_data = [
            MindBulkUpdate(uuid=node1.uuid)
        ]

        # Should raise ValueError due to no fields to update
        with pytest.raises(ValueError) as exc_info:
            await service.bulk_update(updates_data)

        assert "No fields to update" in str(exc_info.value)

    async def test_bulk_create_empty_list(self, clean_database):
        """
        Test that bulk_create handles empty list correctly.
        """
        service = MindService()

        minds_data = []
        created_nodes = await service.bulk_create(minds_data)

        assert len(created_nodes) == 0

    async def test_bulk_update_empty_list(self, clean_database):
        """
        Test that bulk_update handles empty list correctly.
        """
        service = MindService()

        updates_data = []
        updated_nodes = await service.bulk_update(updates_data)

        assert len(updated_nodes) == 0
