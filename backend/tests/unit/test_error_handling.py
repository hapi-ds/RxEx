"""
Unit tests for error handling in the Mind-Based Data Model System.

This module contains unit tests for error conditions including database
connection failures, internal errors, and rate limit errors.

**Validates: Requirements 12.3, 12.4, 12.5**
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.app import app
from src.exceptions import MindDatabaseError, MindError, RateLimitError
from src.schemas.minds import MindCreate


class TestDatabaseErrorHandling:
    """Test suite for database connection failure error handling."""

    @pytest.mark.asyncio
    async def test_database_connection_failure_returns_503(self):
        """
        Test that database connection failures return HTTP 503.

        When a database operation fails due to connection issues, the API
        should return HTTP 503 Service Unavailable with a retry-after header.

        **Validates: Requirement 12.3**
        """
        client = TestClient(app)

        # Mock the MindService.create_mind to raise MindDatabaseError
        with patch("src.routes.minds.mind_service.create_mind") as mock_create:
            mock_create.side_effect = MindDatabaseError("Connection to Neo4j failed")

            # Attempt to create a Mind node
            mind_data = {
                "mind_type": "project",
                "title": "Test Project",
                "description": "Test description",
                "creator": "test@example.com",
                "type_specific_attributes": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            }

            response = client.post("/api/v1/minds", json=mind_data)

            # Verify HTTP 503 status code (Requirement 12.3)
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            # Verify error response structure
            error_data = response.json()
            assert "request_id" in error_data
            assert error_data["error_type"] == "DatabaseError"
            assert "Database operation failed" in error_data["message"]
            assert "retry_after" in error_data["details"]
            assert error_data["details"]["retry_after"] == 30
            assert "timestamp" in error_data

            # Verify retry-after header is present (Requirement 12.3)
            assert "retry-after" in response.headers
            assert response.headers["retry-after"] == "30"

    @pytest.mark.asyncio
    async def test_database_error_on_get_returns_503(self):
        """
        Test that database errors during retrieval return HTTP 503.

        **Validates: Requirement 12.3**
        """
        client = TestClient(app)

        # Mock the MindService.get_mind to raise MindDatabaseError
        with patch("src.routes.minds.mind_service.get_mind") as mock_get:
            mock_get.side_effect = MindDatabaseError("Database query timeout")

            test_uuid = str(uuid4())
            response = client.get(f"/api/v1/minds/{test_uuid}")

            # Verify HTTP 503 status code
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            # Verify error response structure
            error_data = response.json()
            assert error_data["error_type"] == "DatabaseError"
            assert "retry_after" in error_data["details"]

    @pytest.mark.asyncio
    async def test_database_error_on_update_returns_503(self):
        """
        Test that database errors during update return HTTP 503.

        **Validates: Requirement 12.3**
        """
        client = TestClient(app)

        # Mock the MindService.update_mind to raise MindDatabaseError
        with patch("src.routes.minds.mind_service.update_mind") as mock_update:
            mock_update.side_effect = MindDatabaseError("Database write failed")

            test_uuid = str(uuid4())
            update_data = {"title": "Updated Title"}

            response = client.put(f"/api/v1/minds/{test_uuid}", json=update_data)

            # Verify HTTP 503 status code
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            # Verify error response structure
            error_data = response.json()
            assert error_data["error_type"] == "DatabaseError"


class TestInternalErrorHandling:
    """Test suite for internal error handling."""

    @pytest.mark.asyncio
    async def test_internal_error_returns_500(self):
        """
        Test that internal errors return HTTP 500.

        When an unexpected internal error occurs, the API should return
        HTTP 500 Internal Server Error with appropriate error details.

        **Validates: Requirement 12.4**
        """
        client = TestClient(app)

        # Mock the MindService.create_mind to raise a generic MindError
        with patch("src.routes.minds.mind_service.create_mind") as mock_create:
            mock_create.side_effect = MindError("Unexpected internal error occurred")

            # Attempt to create a Mind node
            mind_data = {
                "mind_type": "task",
                "title": "Test Task",
                "description": "Test description",
                "creator": "test@example.com",
                "type_specific_attributes": {
                    "priority": "high",
                    "assignee": "dev@example.com",
                },
            }

            response = client.post("/api/v1/minds", json=mind_data)

            # Verify HTTP 500 status code (Requirement 12.4)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            # Verify error response structure
            error_data = response.json()
            assert "request_id" in error_data
            assert error_data["error_type"] == "InternalError"
            assert "unexpected error occurred" in error_data["message"].lower()
            assert "timestamp" in error_data

    @pytest.mark.asyncio
    async def test_unexpected_exception_returns_500(self):
        """
        Test that unexpected exceptions return HTTP 500.

        When an unexpected exception (not a MindError subclass) occurs,
        the API should return HTTP 500 with a generic error message.

        **Validates: Requirement 12.4**
        """
        client = TestClient(app, raise_server_exceptions=False)

        # Mock the MindService.create_mind to raise a generic Exception
        with patch("src.routes.minds.mind_service.create_mind") as mock_create:
            mock_create.side_effect = Exception("Unexpected system error")

            # Attempt to create a Mind node
            mind_data = {
                "mind_type": "project",
                "title": "Test Project",
                "description": "Test description",
                "creator": "test@example.com",
                "type_specific_attributes": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            }

            response = client.post("/api/v1/minds", json=mind_data)

            # Verify HTTP 500 status code
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            # Verify error response structure
            error_data = response.json()
            assert error_data["error_type"] == "InternalError"
            assert "unexpected error occurred" in error_data["message"].lower()

    @pytest.mark.asyncio
    async def test_internal_error_on_query_returns_500(self):
        """
        Test that internal errors during query operations return HTTP 500.

        **Validates: Requirement 12.4**
        """
        client = TestClient(app)

        # Mock the MindService.query_minds to raise MindError
        with patch("src.routes.minds.mind_service.query_minds") as mock_query:
            mock_query.side_effect = MindError("Query processing failed")

            response = client.get("/api/v1/minds?mind_type=project")

            # Verify HTTP 500 status code
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            # Verify error response structure
            error_data = response.json()
            assert error_data["error_type"] == "InternalError"


class TestRateLimitErrorHandling:
    """Test suite for rate limit error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_returns_429(self):
        """
        Test that rate limit errors return HTTP 429.

        When rate limits are exceeded, the API should return HTTP 429
        Too Many Requests with a retry-after header indicating when
        the client can retry.

        **Validates: Requirement 12.5**
        """
        client = TestClient(app)

        # Mock the MindService.create_mind to raise RateLimitError
        with patch("src.routes.minds.mind_service.create_mind") as mock_create:
            mock_create.side_effect = RateLimitError("Rate limit exceeded")

            # Attempt to create a Mind node
            mind_data = {
                "mind_type": "project",
                "title": "Test Project",
                "description": "Test description",
                "creator": "test@example.com",
                "type_specific_attributes": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            }

            response = client.post("/api/v1/minds", json=mind_data)

            # Verify HTTP 429 status code (Requirement 12.5)
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

            # Verify error response structure
            error_data = response.json()
            assert "request_id" in error_data
            assert error_data["error_type"] == "RateLimitError"
            assert "rate limit exceeded" in error_data["message"].lower()
            assert "retry_after" in error_data["details"]
            assert error_data["details"]["retry_after"] == 60
            assert "limit" in error_data["details"]
            assert "window" in error_data["details"]
            assert "timestamp" in error_data

            # Verify retry-after header is present (Requirement 12.5)
            assert "retry-after" in response.headers
            assert response.headers["retry-after"] == "60"

    @pytest.mark.asyncio
    async def test_rate_limit_error_on_bulk_operations(self):
        """
        Test that rate limit errors on bulk operations return HTTP 429.

        **Validates: Requirement 12.5**
        """
        client = TestClient(app)

        # Mock the MindService.bulk_create to raise RateLimitError
        with patch("src.routes.minds.mind_service.bulk_create") as mock_bulk:
            mock_bulk.side_effect = RateLimitError("Bulk operation rate limit exceeded")

            # Attempt bulk create
            bulk_data = [
                {
                    "mind_type": "task",
                    "title": f"Task {i}",
                    "description": "Test task",
                    "creator": "test@example.com",
                    "type_specific_attributes": {
                        "priority": "medium",
                        "assignee": "dev@example.com",
                    },
                }
                for i in range(10)
            ]

            response = client.post("/api/v1/minds/bulk", json=bulk_data)

            # Verify HTTP 429 status code
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

            # Verify error response structure
            error_data = response.json()
            assert error_data["error_type"] == "RateLimitError"
            assert "retry_after" in error_data["details"]


class TestErrorResponseConsistency:
    """Test suite for error response format consistency."""

    @pytest.mark.asyncio
    async def test_all_errors_include_request_id(self):
        """
        Test that all error responses include a unique request_id.

        This ensures consistent error tracking across all error types.

        **Validates: Requirement 12.1, 12.6**
        """
        client = TestClient(app)

        # Test with a database error (not a Pydantic validation error)
        with patch("src.routes.minds.mind_service.create_mind") as mock_create:
            mock_create.side_effect = MindDatabaseError("Database connection failed")

            mind_data = {
                "mind_type": "project",
                "title": "Test",
                "description": "Test",
                "creator": "test@example.com",
                "type_specific_attributes": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            }

            response = client.post("/api/v1/minds", json=mind_data)

            # Verify request_id is present
            error_data = response.json()
            assert "request_id" in error_data
            assert error_data["request_id"].startswith("req_")
            assert len(error_data["request_id"]) > 4  # req_ + at least some ID

    @pytest.mark.asyncio
    async def test_all_errors_include_timestamp(self):
        """
        Test that all error responses include a timestamp.

        **Validates: Requirement 12.1, 12.6**
        """
        client = TestClient(app)

        # Test with a database error
        with patch("src.routes.minds.mind_service.get_mind") as mock_get:
            mock_get.side_effect = MindDatabaseError("Database query timeout")

            test_uuid = str(uuid4())
            response = client.get(f"/api/v1/minds/{test_uuid}")

            # Verify timestamp is present and valid
            error_data = response.json()
            assert "timestamp" in error_data
            # Verify it's a valid ISO format timestamp
            timestamp = datetime.fromisoformat(error_data["timestamp"].replace("Z", "+00:00"))
            assert isinstance(timestamp, datetime)

    @pytest.mark.asyncio
    async def test_all_errors_include_error_type(self):
        """
        Test that all error responses include an error_type field.

        **Validates: Requirement 12.1, 12.6**
        """
        client = TestClient(app)

        # Test with an internal error
        with patch("src.routes.minds.mind_service.create_mind") as mock_create:
            mock_create.side_effect = MindError("Internal processing error")

            mind_data = {
                "mind_type": "project",
                "title": "Test",
                "description": "Test",
                "creator": "test@example.com",
                "type_specific_attributes": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            }

            response = client.post("/api/v1/minds", json=mind_data)

            # Verify error_type is present
            error_data = response.json()
            assert "error_type" in error_data
            assert error_data["error_type"] in [
                "ValidationError",
                "NotFoundError",
                "DatabaseError",
                "InternalError",
                "RateLimitError",
            ]

    @pytest.mark.asyncio
    async def test_error_response_has_consistent_structure(self):
        """
        Test that error responses have a consistent structure across all error types.

        All errors should include: request_id, error_type, message, details, timestamp

        **Validates: Requirement 12.1, 12.6**
        """
        client = TestClient(app)

        # Mock database error
        with patch("src.routes.minds.mind_service.create_mind") as mock_create:
            mock_create.side_effect = MindDatabaseError("Database error")

            mind_data = {
                "mind_type": "project",
                "title": "Test",
                "description": "Test",
                "creator": "test@example.com",
                "type_specific_attributes": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            }

            response = client.post("/api/v1/minds", json=mind_data)

            # Verify all required fields are present
            error_data = response.json()
            required_fields = ["request_id", "error_type", "message", "details", "timestamp"]
            for field in required_fields:
                assert field in error_data, f"Missing required field: {field}"

            # Verify field types
            assert isinstance(error_data["request_id"], str)
            assert isinstance(error_data["error_type"], str)
            assert isinstance(error_data["message"], str)
            assert isinstance(error_data["details"], dict)
            assert isinstance(error_data["timestamp"], str)
