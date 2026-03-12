"""Smoke tests for creating each Mind type via API.

Tests basic creation functionality for all Mind types to verify the system works.
"""

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def client(clean_database, setup_schema):
    """Create FastAPI test client."""
    return TestClient(app)


def test_create_task(client):
    """Verify Task can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "task",
            "title": "Test Task",
            "creator": "test_creator",
            "type_specific_attributes": {
                "task_type": "TASK",
                "priority": "medium",
                "assignee": "test_user",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["type_specific_attributes"]["task_type"] == "TASK"
    assert data["type_specific_attributes"]["priority"] == "medium"


def test_create_project(client):
    """Verify Project can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "project",
            "title": "Test Project",
            "creator": "test_creator",
            "type_specific_attributes": {
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "budget": 100000.0,
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["type_specific_attributes"]["budget"] == 100000.0


def test_create_requirement(client):
    """Verify Requirement can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "requirement",
            "title": "Test Requirement",
            "creator": "test_creator",
            "type_specific_attributes": {
                "requirement_type": "USER_STORY",
                "content": "As a user, I want to test the system",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Requirement"
    assert data["type_specific_attributes"]["requirement_type"] == "USER_STORY"


def test_create_resource(client):
    """Verify Resource can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "resource",
            "title": "Test Resource",
            "creator": "test_creator",
            "type_specific_attributes": {
                "resource_type": "PERSON",
                "email": "test@example.com",
                "efficiency": 1.0,
                "hourly_rate": 500.0,
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Resource"
    assert data["type_specific_attributes"]["resource_type"] == "PERSON"


def test_create_risk(client):
    """Verify Risk can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "risk",
            "title": "Test Risk",
            "creator": "test_creator",
            "type_specific_attributes": {
                "severity": "high",
                "probability": "likely",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Risk"
    assert data["type_specific_attributes"]["severity"] == "high"
    assert data["type_specific_attributes"]["probability"] == "likely"


def test_create_knowledge(client):
    """Verify Knowledge can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "knowledge",
            "title": "Test Knowledge",
            "creator": "test_creator",
            "type_specific_attributes": {
                "category": "technical",
                "tags": ["testing", "smoke"],
                "content": "This is test knowledge content",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Knowledge"
    assert data["type_specific_attributes"]["category"] == "technical"


def test_create_account(client):
    """Verify Account can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "account",
            "title": "Test Account",
            "creator": "test_creator",
            "type_specific_attributes": {
                "account_type": "COST",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Account"
    assert data["type_specific_attributes"]["account_type"] == "COST"


def test_create_company(client):
    """Verify Company can be created via API."""
    response = client.post(
        "/api/v1/minds",
        json={
            "mind_type": "company",
            "title": "Test Company",
            "creator": "test_creator",
            "type_specific_attributes": {
                "industry": "Technology",
                "size": 100,
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Company"
    assert data["type_specific_attributes"]["industry"] == "Technology"
