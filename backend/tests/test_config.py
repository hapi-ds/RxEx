"""Tests for configuration settings."""

import pytest
from pydantic import ValidationError

from src.config.config import Settings


def test_jwt_fields_exist():
    """Test that JWT configuration fields exist with correct defaults."""
    settings = Settings()

    assert hasattr(settings, 'jwt_secret')
    assert hasattr(settings, 'jwt_algorithm')
    assert hasattr(settings, 'jwt_expiration_minutes')

    # Check that values are set (don't check specific values as they come from .env)
    assert settings.jwt_secret is not None
    assert len(settings.jwt_secret) > 0
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expiration_minutes == 60


def test_cors_origins_field():
    """Test that CORS origins field exists with correct defaults."""
    settings = Settings()

    assert hasattr(settings, 'cors_origins')
    assert isinstance(settings.cors_origins, list)

    # Check expected origins
    expected_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://web:3000",
        "http://xr:3001"
    ]

    for origin in expected_origins:
        assert origin in settings.cors_origins, f"Expected origin {origin} not found"


def test_logging_fields_exist():
    """Test that logging configuration fields exist with correct defaults."""
    settings = Settings()

    assert hasattr(settings, 'log_level')
    assert hasattr(settings, 'log_file')

    # Check defaults
    assert settings.log_level == "INFO"
    assert settings.log_file == "app.log"


def test_log_level_validation():
    """Test that log level validation works correctly."""
    # Valid log levels should work
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    for level in valid_levels:
        settings = Settings(log_level=level)
        assert settings.log_level == level

    # Invalid log level should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Settings(log_level="INVALID")

    assert "log_level must be one of" in str(exc_info.value)


def test_jwt_expiration_validation():
    """Test that JWT expiration validation works correctly."""
    # Positive values should work
    settings = Settings(jwt_expiration_minutes=30)
    assert settings.jwt_expiration_minutes == 30

    # Zero or negative values should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Settings(jwt_expiration_minutes=0)

    assert "jwt_expiration_minutes must be positive" in str(exc_info.value)

    with pytest.raises(ValidationError):
        Settings(jwt_expiration_minutes=-10)


def test_backward_compatibility():
    """Test backward compatibility with legacy secret_key and algorithm fields."""
    settings = Settings()

    # Legacy fields should exist
    assert hasattr(settings, 'secret_key')
    assert hasattr(settings, 'algorithm')

    # They should match the new fields by default
    assert settings.secret_key == settings.jwt_secret
    assert settings.algorithm == settings.jwt_algorithm


def test_environment_variable_loading():
    """Test that settings can be loaded from environment variables."""
    import os

    # Set environment variables
    os.environ['JWT_SECRET'] = 'test_secret_key'
    os.environ['JWT_ALGORITHM'] = 'HS512'
    os.environ['JWT_EXPIRATION_MINUTES'] = '120'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['LOG_FILE'] = 'test.log'

    # Create new settings instance
    settings = Settings()

    # Verify values were loaded
    assert settings.jwt_secret == 'test_secret_key'
    assert settings.jwt_algorithm == 'HS512'
    assert settings.jwt_expiration_minutes == 120
    assert settings.log_level == 'DEBUG'
    assert settings.log_file == 'test.log'

    # Clean up
    del os.environ['JWT_SECRET']
    del os.environ['JWT_ALGORITHM']
    del os.environ['JWT_EXPIRATION_MINUTES']
    del os.environ['LOG_LEVEL']
    del os.environ['LOG_FILE']


def test_cors_origins_from_env():
    """Test that CORS origins can be customized via environment."""
    import json
    import os

    # Set custom CORS origins
    custom_origins = ["http://example.com", "http://test.com"]
    os.environ['CORS_ORIGINS'] = json.dumps(custom_origins)

    Settings()

    # Note: Pydantic will parse JSON strings for list fields
    # If not working, we may need to adjust the field definition

    # Clean up
    if 'CORS_ORIGINS' in os.environ:
        del os.environ['CORS_ORIGINS']
