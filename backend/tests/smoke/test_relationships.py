"""Smoke tests for creating relationships between Mind nodes.

Tests basic relationship creation and retrieval to verify the system works.
"""

import pytest
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def client(clean_database, setup_schema):
    """Create FastAPI test client."""
    return TestClient(app)


def test_create_task_relationship(client):
    """Test creating a relationship between two tasks."""
    # Create first task
    task1_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Task 1",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "medium",
                "assignee": "test_user",
            },
        },
    )
    assert task1_response.status_code == 201
    task1_uuid = task1_response.json()["uuid"]

    # Create second task
    task2_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Task 2",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "medium",
                "assignee": "test_user",
            },
        },
    )
    assert task2_response.status_code == 201
    task2_uuid = task2_response.json()["uuid"]

    # Create relationship (Task 1 -> Task 2)
    rel_response = client.post(
        f"/api/v1/minds/{task1_uuid}/relationships?target_uuid={task2_uuid}&relationship_type=depends_on"
    )
    if rel_response.status_code != 201:
        print(f"Relationship creation failed: {rel_response.json()}")
    assert rel_response.status_code == 201
    rel_data = rel_response.json()
    assert rel_data["source_uuid"] == task1_uuid
    assert rel_data["target_uuid"] == task2_uuid
    assert rel_data["relationship_type"] == "depends_on"


def test_get_relationships(client):
    """Test retrieving relationships for a Mind node."""
    # Create three tasks
    task1_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Task 1",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "medium",
                "assignee": "test_user",
            },
        },
    )
    task1_uuid = task1_response.json()["uuid"]

    task2_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Task 2",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "medium",
                "assignee": "test_user",
            },
        },
    )
    task2_uuid = task2_response.json()["uuid"]

    task3_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Task 3",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "medium",
                "assignee": "test_user",
            },
        },
    )
    task3_uuid = task3_response.json()["uuid"]

    # Create relationships
    client.post(
        f"/api/v1/minds/{task1_uuid}/relationships?target_uuid={task2_uuid}&relationship_type=depends_on"
    )
    client.post(
        f"/api/v1/minds/{task2_uuid}/relationships?target_uuid={task3_uuid}&relationship_type=depends_on"
    )

    # Get relationships for task1
    rels_response = client.get(f"/api/v1/minds/{task1_uuid}/relationships")
    assert rels_response.status_code == 200
    rels_data = rels_response.json()
    assert len(rels_data) >= 1
    assert any(rel["target_uuid"] == task2_uuid for rel in rels_data)


def test_project_task_relationship(client):
    """Test creating a relationship between a Project and Task."""
    # Create project
    project_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "project",
            "title": "Test Project",
            "creator": "test_creator",
            "type_specific_attributes": {
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        },
    )
    project_uuid = project_response.json()["uuid"]

    # Create task
    task_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Project Task",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "high",
                "assignee": "test_user",
            },
        },
    )
    task_uuid = task_response.json()["uuid"]

    # Create relationship (Project contains Task)
    rel_response = client.post(
        f"/api/v1/minds/{project_uuid}/relationships?target_uuid={task_uuid}&relationship_type=contains"
    )
    assert rel_response.status_code == 201
    rel_data = rel_response.json()
    assert rel_data["relationship_type"] == "contains"


def test_requirement_task_relationship(client):
    """Test creating a relationship between a Requirement and Task."""
    # Create requirement
    req_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "requirement",
            "title": "Test Requirement",
            "creator": "test_creator",
            "type_specific_attributes": {
                "requirement_type": "USER_STORY",
                "content": "As a user, I want to test relationships",
            },
        },
    )
    req_uuid = req_response.json()["uuid"]

    # Create task
    task_response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Implementation Task",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "medium",
                "assignee": "test_user",
            },
        },
    )
    task_uuid = task_response.json()["uuid"]

    # Create relationship (Requirement -> Task)
    rel_response = client.post(
        f"/api/v1/minds/{req_uuid}/relationships?target_uuid={task_uuid}&relationship_type=implements"
    )
    assert rel_response.status_code == 201
