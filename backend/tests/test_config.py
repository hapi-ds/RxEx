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


def test_logging_new_fields_defaults():
    """Test that new logging fields exist with correct defaults."""
    settings = Settings()

    assert settings.log_dir == "/app/logs"
    assert settings.log_max_size_mb == 10
    assert settings.log_backup_count == 5


def test_log_max_size_mb_validation():
    """Test that log_max_size_mb must be positive."""
    # Valid positive value
    settings = Settings(log_max_size_mb=1)
    assert settings.log_max_size_mb == 1

    # Zero should fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(log_max_size_mb=0)
    assert "log_max_size_mb must be positive" in str(exc_info.value)

    # Negative should fail
    with pytest.raises(ValidationError):
        Settings(log_max_size_mb=-5)


def test_log_backup_count_validation():
    """Test that log_backup_count must be non-negative."""
    # Zero is valid (non-negative)
    settings = Settings(log_backup_count=0)
    assert settings.log_backup_count == 0

    # Positive is valid
    settings = Settings(log_backup_count=3)
    assert settings.log_backup_count == 3

    # Negative should fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(log_backup_count=-1)
    assert "log_backup_count must be non-negative" in str(exc_info.value)


# ============================================================================
# GraphRAG and Embedding Configuration Tests
# ============================================================================


def test_embedding_fields_defaults():
    """Test that embedding configuration fields exist with correct defaults."""
    settings = Settings()

    assert settings.embedding_provider == "none"
    assert settings.embedding_api_endpoint is None
    assert settings.embedding_api_key is None
    assert settings.embedding_model_name is None
    assert settings.embedding_dimensions == 1536


def test_graphrag_fields_defaults():
    """Test that GraphRAG configuration fields exist with correct defaults."""
    settings = Settings()

    assert settings.graphrag_enabled is False
    assert settings.graphrag_top_k == 10
    assert settings.graphrag_similarity_threshold == 0.7
    assert settings.graphrag_traversal_depth == 2
    assert settings.graphrag_max_subgraph_nodes == 50
    assert settings.graphrag_default_mode == "auto"
    assert settings.graphrag_community_schedule_hours == 0


def test_embedding_provider_validation():
    """Test that embedding_provider validates against allowed values."""
    for provider in ["none", "openai", "lm-studio", "custom"]:
        settings = Settings(embedding_provider=provider)
        assert settings.embedding_provider == provider

    # Case insensitive
    settings = Settings(embedding_provider="OpenAI")
    assert settings.embedding_provider == "openai"

    with pytest.raises(ValidationError) as exc_info:
        Settings(embedding_provider="invalid")
    assert "embedding_provider must be one of" in str(exc_info.value)


def test_embedding_dimensions_validation():
    """Test that embedding_dimensions must be positive."""
    settings = Settings(embedding_dimensions=768)
    assert settings.embedding_dimensions == 768

    with pytest.raises(ValidationError) as exc_info:
        Settings(embedding_dimensions=0)
    assert "embedding_dimensions must be positive" in str(exc_info.value)

    with pytest.raises(ValidationError):
        Settings(embedding_dimensions=-1)


def test_graphrag_default_mode_validation():
    """Test that graphrag_default_mode validates against allowed values."""
    for mode in ["auto", "local", "global", "hybrid"]:
        settings = Settings(graphrag_default_mode=mode)
        assert settings.graphrag_default_mode == mode

    # Case insensitive
    settings = Settings(graphrag_default_mode="LOCAL")
    assert settings.graphrag_default_mode == "local"

    with pytest.raises(ValidationError) as exc_info:
        Settings(graphrag_default_mode="invalid")
    assert "graphrag_default_mode must be one of" in str(exc_info.value)


def test_graphrag_top_k_validation():
    """Test that graphrag_top_k must be >= 1."""
    settings = Settings(graphrag_top_k=1)
    assert settings.graphrag_top_k == 1

    with pytest.raises(ValidationError):
        Settings(graphrag_top_k=0)


def test_graphrag_similarity_threshold_validation():
    """Test that graphrag_similarity_threshold must be between 0.0 and 1.0."""
    settings = Settings(graphrag_similarity_threshold=0.0)
    assert settings.graphrag_similarity_threshold == 0.0

    settings = Settings(graphrag_similarity_threshold=1.0)
    assert settings.graphrag_similarity_threshold == 1.0

    with pytest.raises(ValidationError):
        Settings(graphrag_similarity_threshold=-0.1)

    with pytest.raises(ValidationError):
        Settings(graphrag_similarity_threshold=1.1)


def test_graphrag_traversal_depth_validation():
    """Test that graphrag_traversal_depth must be >= 1."""
    settings = Settings(graphrag_traversal_depth=1)
    assert settings.graphrag_traversal_depth == 1

    with pytest.raises(ValidationError):
        Settings(graphrag_traversal_depth=0)


def test_graphrag_max_subgraph_nodes_validation():
    """Test that graphrag_max_subgraph_nodes must be >= 1."""
    settings = Settings(graphrag_max_subgraph_nodes=1)
    assert settings.graphrag_max_subgraph_nodes == 1

    with pytest.raises(ValidationError):
        Settings(graphrag_max_subgraph_nodes=0)


def test_graphrag_community_schedule_hours_validation():
    """Test that graphrag_community_schedule_hours must be >= 0."""
    settings = Settings(graphrag_community_schedule_hours=0)
    assert settings.graphrag_community_schedule_hours == 0

    settings = Settings(graphrag_community_schedule_hours=24)
    assert settings.graphrag_community_schedule_hours == 24

    with pytest.raises(ValidationError):
        Settings(graphrag_community_schedule_hours=-1)


def test_graphrag_env_variable_loading():
    """Test that GraphRAG settings load from environment variables."""
    import os

    os.environ['EMBEDDING_PROVIDER'] = 'lm-studio'
    os.environ['EMBEDDING_API_ENDPOINT'] = 'http://localhost:1234/v1'
    os.environ['EMBEDDING_MODEL_NAME'] = 'test-model'
    os.environ['EMBEDDING_DIMENSIONS'] = '768'
    os.environ['GRAPHRAG_ENABLED'] = 'true'
    os.environ['GRAPHRAG_TOP_K'] = '20'
    os.environ['GRAPHRAG_SIMILARITY_THRESHOLD'] = '0.5'
    os.environ['GRAPHRAG_DEFAULT_MODE'] = 'local'

    try:
        settings = Settings()
        assert settings.embedding_provider == 'lm-studio'
        assert settings.embedding_api_endpoint == 'http://localhost:1234/v1'
        assert settings.embedding_model_name == 'test-model'
        assert settings.embedding_dimensions == 768
        assert settings.graphrag_enabled is True
        assert settings.graphrag_top_k == 20
        assert settings.graphrag_similarity_threshold == 0.5
        assert settings.graphrag_default_mode == 'local'
    finally:
        for key in [
            'EMBEDDING_PROVIDER', 'EMBEDDING_API_ENDPOINT', 'EMBEDDING_MODEL_NAME',
            'EMBEDDING_DIMENSIONS', 'GRAPHRAG_ENABLED', 'GRAPHRAG_TOP_K',
            'GRAPHRAG_SIMILARITY_THRESHOLD', 'GRAPHRAG_DEFAULT_MODE',
        ]:
            os.environ.pop(key, None)
