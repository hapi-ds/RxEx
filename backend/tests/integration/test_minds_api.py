"""
Integration tests for Mind API routes.

This module tests the complete API flows for Mind node operations including
CRUD operations, version history, relationships, bulk operations, and queries.
These tests validate the integration between API routes, service layer, and
database.

**Validates: Requirements 3.1-3.7, 4.1-4.5, 5.1-5.8, 6.1-6.6, 7.1-7.6,
8.1-8.6, 10.1-10.5, 11.1-11.7, 12.1-12.6**
"""

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.models.enums import StatusEnum

# Create test client
client = TestClient(app)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_project_data():
    """Sample project Mind creation data."""
    return {
        "mind_type": "project",
        "title": "Test Project",
        "description": "A test project for integration testing",
        "creator": "test@example.com",
        "type_specific_attributes": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 50000.0,
        },
    }


@pytest.fixture
def sample_task_data():
    """Sample task Mind creation data."""
    return {
        "mind_type": "task",
        "title": "Test Task",
        "description": "A test task",
        "creator": "dev@example.com",
        "type_specific_attributes": {
            "priority": "high",
            "assignee": "dev@example.com",
            "due_date": "2024-02-01",
            "estimated_hours": 8.0,
        },
    }


# Mark all tests to use clean_database fixture
pytestmark = pytest.mark.usefixtures("clean_database")



# ============================================================================
# Test: Create Mind Node (13.1)
# ============================================================================


def test_create_mind_success(sample_project_data):
    """
    Test successful Mind node creation.
    Validates: Requirements 3.1, 3.7
    """
    response = client.post("/api/v1/minds", json=sample_project_data)

    assert response.status_code == 201
    data = response.json()

    # Verify all required fields are present
    assert "uuid" in data
    assert data["mind_type"] == "project"
    assert data["title"] == "Test Project"
    assert data["version"] == 1
    assert data["creator"] == "test@example.com"
    assert data["status"] in [e.value for e in StatusEnum]
    assert "updated_at" in data
    assert data["type_specific_attributes"]["budget"] == 50000.0


def test_create_mind_invalid_type():
    """
    Test Mind creation with invalid mind_type.
    Validates: Requirements 3.6, 12.1
    """
    invalid_data = {
        "mind_type": "invalid_type",
        "title": "Test",
        "creator": "test@example.com",
        "type_specific_attributes": {},
    }

    response = client.post("/api/v1/minds", json=invalid_data)

    # FastAPI returns 422 for Pydantic validation errors
    assert response.status_code == 422


def test_create_mind_missing_required_fields():
    """
    Test Mind creation with missing required fields.
    Validates: Requirements 3.6, 12.1
    """
    invalid_data = {
        "mind_type": "project",
        "title": "Test Project",
        # Missing creator
        "type_specific_attributes": {},
    }

    response = client.post("/api/v1/minds", json=invalid_data)

    assert response.status_code == 422  # FastAPI validation error


# ============================================================================
# Test: Retrieve Mind Node (13.2)
# ============================================================================


def test_get_mind_success(sample_project_data):
    """
    Test successful Mind node retrieval.
    Validates: Requirements 4.1, 4.2
    """
    # Create a Mind node first
    create_response = client.post("/api/v1/minds", json=sample_project_data)
    assert create_response.status_code == 201
    created_uuid = create_response.json()["uuid"]

    # Retrieve the Mind node
    response = client.get(f"/api/v1/minds/{created_uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == created_uuid
    assert data["title"] == "Test Project"


def test_get_mind_not_found():
    """
    Test Mind retrieval with non-existent UUID.
    Validates: Requirements 4.3, 12.2
    """
    non_existent_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/minds/{non_existent_uuid}")

    assert response.status_code == 404
    data = response.json()
    assert data["error_type"] == "NotFoundError"
    assert non_existent_uuid in data["message"]
    assert "request_id" in data



# ============================================================================
# Test: Update Mind Node (13.3)
# ============================================================================


def test_update_mind_success(sample_project_data):
    """
    Test successful Mind node update.
    Validates: Requirements 5.1-5.8
    """
    # Create a Mind node
    create_response = client.post("/api/v1/minds", json=sample_project_data)
    created_uuid = create_response.json()["uuid"]
    original_version = create_response.json()["version"]

    # Update the Mind node
    update_data = {
        "title": "Updated Test Project",
        "type_specific_attributes": {"budget": 75000.0},
    }
    response = client.put(f"/api/v1/minds/{created_uuid}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == created_uuid
    assert data["title"] == "Updated Test Project"
    assert data["version"] == original_version + 1
    assert data["type_specific_attributes"]["budget"] == 75000.0


def test_update_mind_not_found():
    """
    Test Mind update with non-existent UUID.
    Validates: Requirements 5.8, 12.2
    """
    non_existent_uuid = str(uuid.uuid4())
    update_data = {"title": "Updated Title"}

    response = client.put(f"/api/v1/minds/{non_existent_uuid}", json=update_data)

    assert response.status_code == 404
    data = response.json()
    assert data["error_type"] == "NotFoundError"


# ============================================================================
# Test: Delete Mind Node (13.4)
# ============================================================================


def test_delete_mind_soft_delete(sample_project_data):
    """
    Test soft delete of Mind node.
    Validates: Requirements 7.1, 7.2
    """
    # Create a Mind node
    create_response = client.post("/api/v1/minds", json=sample_project_data)
    created_uuid = create_response.json()["uuid"]

    # Soft delete
    response = client.delete(f"/api/v1/minds/{created_uuid}")

    assert response.status_code == 204


def test_delete_mind_hard_delete(sample_project_data):
    """
    Test hard delete of Mind node.
    Validates: Requirements 7.3, 7.4, 7.6
    """
    # Create a Mind node
    create_response = client.post("/api/v1/minds", json=sample_project_data)
    created_uuid = create_response.json()["uuid"]

    # Hard delete
    response = client.delete(f"/api/v1/minds/{created_uuid}?hard=true")

    assert response.status_code == 204

    # Verify node is gone
    get_response = client.get(f"/api/v1/minds/{created_uuid}")
    assert get_response.status_code == 404


def test_delete_mind_not_found():
    """
    Test delete with non-existent UUID.
    Validates: Requirements 7.5, 12.2
    """
    non_existent_uuid = str(uuid.uuid4())
    response = client.delete(f"/api/v1/minds/{non_existent_uuid}")

    assert response.status_code == 404



# ============================================================================
# Test: Version History (13.5)
# ============================================================================


def test_get_version_history(sample_project_data):
    """
    Test version history retrieval.
    Validates: Requirements 6.1-6.6
    """
    # Create a Mind node
    create_response = client.post("/api/v1/minds", json=sample_project_data)
    created_uuid = create_response.json()["uuid"]

    # Update it twice to create version history
    client.put(f"/api/v1/minds/{created_uuid}", json={"title": "Version 2"})
    client.put(f"/api/v1/minds/{created_uuid}", json={"title": "Version 3"})

    # Get version history
    response = client.get(f"/api/v1/minds/{created_uuid}/history")

    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    assert len(history) >= 3  # At least 3 versions

    # Verify ordering (newest to oldest)
    versions = [item["version"] for item in history]
    assert versions == sorted(versions, reverse=True)


def test_get_version_history_pagination(sample_project_data):
    """
    Test version history pagination.
    Validates: Requirements 6.6
    """
    # Create a Mind node
    create_response = client.post("/api/v1/minds", json=sample_project_data)
    created_uuid = create_response.json()["uuid"]

    # Get version history with pagination
    response = client.get(f"/api/v1/minds/{created_uuid}/history?page=1&page_size=10")

    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)


# ============================================================================
# Test: Query Minds (13.6)
# ============================================================================


def test_query_minds_no_filters():
    """
    Test querying all Mind nodes without filters.
    Validates: Requirements 11.7
    """
    response = client.get("/api/v1/minds")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data


def test_query_minds_by_type(sample_project_data, sample_task_data):
    """
    Test querying Mind nodes by type.
    Validates: Requirements 4.4, 11.1
    """
    # Create different types
    client.post("/api/v1/minds", json=sample_project_data)
    client.post("/api/v1/minds", json=sample_task_data)

    # Query by type
    response = client.get("/api/v1/minds?mind_type=project")

    assert response.status_code == 200
    data = response.json()
    # All returned items should be projects
    for item in data["items"]:
        assert item["mind_type"] == "project"


def test_query_minds_by_creator(sample_project_data):
    """
    Test querying Mind nodes by creator.
    Validates: Requirements 11.3
    """
    # Create a Mind node
    client.post("/api/v1/minds", json=sample_project_data)

    # Query by creator
    response = client.get("/api/v1/minds?creator=test@example.com")

    assert response.status_code == 200
    data = response.json()
    # All returned items should have the specified creator
    for item in data["items"]:
        assert item["creator"] == "test@example.com"


def test_query_minds_pagination():
    """
    Test query pagination.
    Validates: Requirements 11.7
    """
    response = client.get("/api/v1/minds?page=1&page_size=5")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5



# ============================================================================
# Test: Create Relationship (13.7)
# ============================================================================


def test_create_relationship_success(sample_project_data, sample_task_data):
    """
    Test successful relationship creation.
    Validates: Requirements 8.1-8.6
    """
    # Create two Mind nodes
    project_response = client.post("/api/v1/minds", json=sample_project_data)
    project_uuid = project_response.json()["uuid"]

    task_response = client.post("/api/v1/minds", json=sample_task_data)
    task_uuid = task_response.json()["uuid"]

    # Create relationship
    response = client.post(
        f"/api/v1/minds/{project_uuid}/relationships?target_uuid={task_uuid}&relationship_type=contains"
    )

    assert response.status_code == 201
    data = response.json()
    assert data["relationship_type"] == "contains"
    assert data["source_uuid"] == project_uuid
    assert data["target_uuid"] == task_uuid
    assert "created_at" in data


def test_create_relationship_invalid_type(sample_project_data, sample_task_data):
    """
    Test relationship creation with invalid type.
    Validates: Requirements 8.2, 12.1
    """
    # Create two Mind nodes
    project_response = client.post("/api/v1/minds", json=sample_project_data)
    project_uuid = project_response.json()["uuid"]

    task_response = client.post("/api/v1/minds", json=sample_task_data)
    task_uuid = task_response.json()["uuid"]

    # Try to create relationship with invalid type
    response = client.post(
        f"/api/v1/minds/{project_uuid}/relationships?target_uuid={task_uuid}&relationship_type=invalid_type"
    )

    # Should return 400 or 422 for validation error
    assert response.status_code in [400, 422]


def test_create_relationship_nonexistent_target(sample_project_data):
    """
    Test relationship creation with non-existent target.
    Validates: Requirements 8.3
    """
    # Create source Mind node
    project_response = client.post("/api/v1/minds", json=sample_project_data)
    project_uuid = project_response.json()["uuid"]

    # Try to create relationship with non-existent target
    non_existent_uuid = str(uuid.uuid4())
    response = client.post(
        f"/api/v1/minds/{project_uuid}/relationships?target_uuid={non_existent_uuid}&relationship_type=contains"
    )

    assert response.status_code == 404


# ============================================================================
# Test: Get Relationships (13.8)
# ============================================================================


def test_get_relationships(sample_project_data, sample_task_data):
    """
    Test retrieving relationships for a Mind node.
    Validates: Requirements 8.5
    """
    # Create two Mind nodes and a relationship
    project_response = client.post("/api/v1/minds", json=sample_project_data)
    project_uuid = project_response.json()["uuid"]

    task_response = client.post("/api/v1/minds", json=sample_task_data)
    task_uuid = task_response.json()["uuid"]

    client.post(
        f"/api/v1/minds/{project_uuid}/relationships?target_uuid={task_uuid}&relationship_type=contains"
    )

    # Get relationships
    response = client.get(f"/api/v1/minds/{project_uuid}/relationships")

    assert response.status_code == 200
    relationships = response.json()
    assert isinstance(relationships, list)
    assert len(relationships) > 0


def test_get_relationships_filtered_by_type(sample_project_data, sample_task_data):
    """
    Test retrieving relationships filtered by type.
    Validates: Requirements 8.5
    """
    # Create two Mind nodes and a relationship
    project_response = client.post("/api/v1/minds", json=sample_project_data)
    project_uuid = project_response.json()["uuid"]

    task_response = client.post("/api/v1/minds", json=sample_task_data)
    task_uuid = task_response.json()["uuid"]

    client.post(
        f"/api/v1/minds/{project_uuid}/relationships?target_uuid={task_uuid}&relationship_type=contains"
    )

    # Get relationships filtered by type
    response = client.get(f"/api/v1/minds/{project_uuid}/relationships?relationship_type=contains")

    assert response.status_code == 200
    relationships = response.json()
    for rel in relationships:
        assert rel["relationship_type"] == "contains"



# ============================================================================
# Test: Bulk Create (13.9)
# ============================================================================


def test_bulk_create_success():
    """
    Test successful bulk creation.
    Validates: Requirements 10.1, 10.3, 10.4, 10.5
    """
    bulk_data = [
        {
            "mind_type": "project",
            "title": f"Project {i}",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        }
        for i in range(5)
    ]

    response = client.post("/api/v1/minds/bulk", json=bulk_data)

    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5
    # Verify all have unique UUIDs
    uuids = [item["uuid"] for item in data]
    assert len(uuids) == len(set(uuids))


def test_bulk_create_exceeds_limit():
    """
    Test bulk creation exceeding 100 item limit.
    Validates: Requirements 10.1
    """
    bulk_data = [
        {
            "mind_type": "project",
            "title": f"Project {i}",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        }
        for i in range(101)
    ]

    response = client.post("/api/v1/minds/bulk", json=bulk_data)

    assert response.status_code == 400


def test_bulk_create_validation_failure():
    """
    Test bulk creation with validation failure.
    Validates: Requirements 10.3, 10.4
    """
    bulk_data = [
        {
            "mind_type": "project",
            "title": "Valid Project",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        },
        {
            "mind_type": "invalid_type",  # Invalid
            "title": "Invalid Project",
            "creator": "test@example.com",
            "type_specific_attributes": {},
        },
    ]

    response = client.post("/api/v1/minds/bulk", json=bulk_data)

    # Should fail validation (422 for Pydantic validation)
    assert response.status_code == 422


# ============================================================================
# Test: Bulk Update (13.10)
# ============================================================================


def test_bulk_update_success(sample_project_data):
    """
    Test successful bulk update.
    Validates: Requirements 10.2, 10.3, 10.4, 10.5
    """
    # Create some Mind nodes
    created_uuids = []
    for i in range(3):
        data = sample_project_data.copy()
        data["title"] = f"Project {i}"
        response = client.post("/api/v1/minds", json=data)
        created_uuids.append(response.json()["uuid"])

    # Bulk update
    bulk_updates = [
        {"uuid": uuid_str, "title": f"Updated Project {i}"}
        for i, uuid_str in enumerate(created_uuids)
    ]

    response = client.put("/api/v1/minds/bulk", json=bulk_updates)

    # Debug: print response if it fails
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    # Verify titles were updated
    for i, item in enumerate(data):
        assert item["title"] == f"Updated Project {i}"


def test_bulk_update_exceeds_limit():
    """
    Test bulk update exceeding 100 item limit.
    Validates: Requirements 10.2
    """
    bulk_updates = [
        {"uuid": str(uuid.uuid4()), "title": f"Project {i}"} for i in range(101)
    ]

    response = client.put("/api/v1/minds/bulk", json=bulk_updates)

    assert response.status_code == 400


def test_bulk_update_nonexistent_uuid():
    """
    Test bulk update with non-existent UUID.
    Validates: Requirements 10.3, 10.4
    """
    bulk_updates = [{"uuid": str(uuid.uuid4()), "title": "Updated Title"}]

    response = client.put("/api/v1/minds/bulk", json=bulk_updates)

    # Should fail because UUID doesn't exist (could be 400 or 404 depending on implementation)
    assert response.status_code in [400, 404]


# ============================================================================
# Test: Error Handling (13.11)
# ============================================================================


def test_error_response_format():
    """
    Test that error responses follow the standard format.
    Validates: Requirements 12.1, 12.6
    """
    # Trigger a 404 error
    non_existent_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/minds/{non_existent_uuid}")

    assert response.status_code == 404
    data = response.json()

    # Verify error response structure
    assert "request_id" in data
    assert "error_type" in data
    assert "message" in data
    assert "details" in data
    assert "timestamp" in data

    # Verify request_id format
    assert data["request_id"].startswith("req_")


def test_validation_error_format():
    """
    Test validation error response format.
    Validates: Requirements 12.1
    """
    invalid_data = {
        "mind_type": "invalid_type",
        "title": "Test",
        "creator": "test@example.com",
        "type_specific_attributes": {},
    }

    response = client.post("/api/v1/minds", json=invalid_data)

    # FastAPI returns 422 for Pydantic validation errors
    assert response.status_code == 422
