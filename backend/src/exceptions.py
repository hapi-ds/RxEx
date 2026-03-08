"""
Custom exceptions for the Mind-Based Data Model System.

This module defines custom exception classes for handling various error
conditions in the Mind system, including validation errors, not found errors,
database errors, and relationship errors.

**Validates: Requirements 12.1-12.6**
"""


class MindError(Exception):
    """Base exception for Mind system errors."""

    pass


class MindNotFoundError(MindError):
    """Raised when a Mind node is not found by UUID."""

    def __init__(self, uuid: str):
        """
        Initialize MindNotFoundError with UUID.

        Args:
            uuid: The UUID that was not found
        """
        self.uuid = uuid
        super().__init__(f"Mind node not found: {uuid}")


class MindValidationError(MindError):
    """Raised when Mind node validation fails."""

    pass


class MindDatabaseError(MindError):
    """Raised when a database operation fails."""

    pass


class MindRelationshipError(MindError):
    """Raised when a relationship operation fails."""

    pass


class RateLimitError(MindError):
    """Raised when rate limits are exceeded."""

    pass
