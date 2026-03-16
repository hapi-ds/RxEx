from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable validation."""

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_username: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="password", description="Neo4j password")

    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: str = Field(default="6379", description="Redis port")

    # JWT Configuration
    jwt_secret: str = Field(default="secret", description="JWT secret key for token signing")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(default=60, description="JWT token expiration time in minutes")

    # Legacy JWT fields for backward compatibility
    secret_key: str = Field(default="secret", description="Legacy JWT secret key (use jwt_secret)")
    algorithm: str = Field(default="HS256", description="Legacy JWT algorithm (use jwt_algorithm)")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://web:3000",
            "http://xr:3001"
        ],
        description="Allowed CORS origins for multiple frontends"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_file: str = Field(default="app.log", description="Log file path")
    log_dir: str = Field(default="/app/logs", description="Directory for log files")
    log_max_size_mb: int = Field(default=10, description="Maximum log file size in MB before rotation")
    log_backup_count: int = Field(default=5, description="Number of rotated log file backups to retain")

    # AI Provider Configuration
    ai_provider: str = Field(default="none", description="AI provider type (none, openai, anthropic, lm-studio, custom)")
    ai_api_endpoint: Optional[str] = Field(default=None, description="AI provider API endpoint URL")
    ai_api_key: Optional[str] = Field(default=None, description="AI provider API key (optional for local providers)")
    ai_model_name: Optional[str] = Field(default=None, description="AI model name")
    ai_request_timeout: int = Field(default=60, description="AI provider request timeout in seconds")
    ai_max_context_tokens: int = Field(default=8000, description="Maximum context tokens for AI prompts")
    ai_max_history_messages: int = Field(default=20, description="Maximum conversation history messages sent to AI")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard Python logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {v}")
        return v_upper

    @field_validator("log_max_size_mb")
    @classmethod
    def validate_log_max_size_mb(cls, v: int) -> int:
        """Validate log max size is positive."""
        if v <= 0:
            raise ValueError("log_max_size_mb must be positive")
        return v

    @field_validator("log_backup_count")
    @classmethod
    def validate_log_backup_count(cls, v: int) -> int:
        """Validate log backup count is non-negative."""
        if v < 0:
            raise ValueError("log_backup_count must be non-negative")
        return v

    @field_validator("jwt_expiration_minutes")
    @classmethod
    def validate_jwt_expiration(cls, v: int) -> int:
        """Validate JWT expiration is positive."""
        if v <= 0:
            raise ValueError("jwt_expiration_minutes must be positive")
        return v

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Validate AI provider is a supported type."""
        valid_providers = ["none", "openai", "anthropic", "lm-studio", "custom"]
        v_lower = v.lower()
        if v_lower not in valid_providers:
            raise ValueError(f"ai_provider must be one of {valid_providers}, got {v}")
        return v_lower

    @field_validator("ai_request_timeout")
    @classmethod
    def validate_ai_request_timeout(cls, v: int) -> int:
        """Validate AI request timeout is positive."""
        if v <= 0:
            raise ValueError("ai_request_timeout must be positive")
        return v

    @field_validator("ai_max_context_tokens")
    @classmethod
    def validate_ai_max_context_tokens(cls, v: int) -> int:
        """Validate AI max context tokens is positive."""
        if v <= 0:
            raise ValueError("ai_max_context_tokens must be positive")
        return v

    @model_validator(mode="after")
    def validate_ai_config(self) -> "Settings":
        """Validate cross-field AI configuration requirements."""
        if self.ai_provider != "none":
            if not self.ai_api_endpoint:
                raise ValueError(
                    f"ai_api_endpoint is required when ai_provider is '{self.ai_provider}'"
                )
            if not self.ai_model_name:
                raise ValueError(
                    f"ai_model_name is required when ai_provider is '{self.ai_provider}'"
                )
            if self.ai_provider in ("openai", "anthropic") and not self.ai_api_key:
                raise ValueError(
                    f"ai_api_key is required when ai_provider is '{self.ai_provider}'"
                )
        return self

    def __init__(self, **kwargs):
        """Initialize settings and sync legacy fields with new JWT fields."""
        super().__init__(**kwargs)
        # Sync legacy fields with new fields for backward compatibility
        if self.jwt_secret != "secret":
            self.secret_key = self.jwt_secret
        elif self.secret_key != "secret":
            self.jwt_secret = self.secret_key

        if self.jwt_algorithm != "HS256":
            self.algorithm = self.jwt_algorithm
        elif self.algorithm != "HS256":
            self.jwt_algorithm = self.algorithm


settings = Settings()
