"""
Minimal smoke tests for Mind API CRUD operations.

Fast-forward approach: Only test basic create, read, update, delete operations.
"""

import pytest
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


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
            "due_date": "2024-02-01"
        },
    }


pytestmark = pytest.mark.usefixtures("clean_database")


def test_create_mind(sample_task_data):
    """Test creating a Mind node via API."""
    response = client.post("/api/v1/minds", json=sample_task_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["mind_type"] == "task"


def test_get_mind(sample_task_data):
    """Test retrieving a Mind node via API."""
    # Create
    create_response = client.post("/api/v1/minds", json=sample_task_data)
    uuid = create_response.json()["uuid"]
    
    # Read
    response = client.get(f"/api/v1/minds/{uuid}")
    assert response.status_code == 200
    assert response.json()["uuid"] == uuid


def test_update_mind(sample_task_data):
    """Test updating a Mind node via API."""
    # Create
    create_response = client.post("/api/v1/minds", json=sample_task_data)
    uuid = create_response.json()["uuid"]
    
    # Update
    update_data = {"title": "Updated Task"}
    response = client.put(f"/api/v1/minds/{uuid}", json=update_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Task"


def test_delete_mind(sample_task_data):
    """Test deleting a Mind node via API."""
    # Create
    create_response = client.post("/api/v1/minds", json=sample_task_data)
    uuid = create_response.json()["uuid"]
    
    # Delete
    response = client.delete(f"/api/v1/minds/{uuid}")
    assert response.status_code == 204  # No Content is correct for successful delete
