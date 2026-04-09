"""
Pydantic schemas for AI chat integration.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessageRequest(BaseModel):
    """Request payload for sending a chat message."""

    content: str = Field(..., min_length=1, max_length=10000)
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    retrieval_mode: str | None = Field(
        default=None, pattern="^(local|global|hybrid|auto)$"
    )


class ChatStreamEvent(BaseModel):
    """Server-sent event for streaming responses."""

    type: str  # "message_chunk", "function_call", "error", "done"
    content: Optional[str] = None
    tool_name: Optional[str] = None
    arguments: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] | None = None


class ChatConfigResponse(BaseModel):
    """Response for chat configuration endpoint."""

    provider: str
    model_name: Optional[str] = None
    is_configured: bool
    supports_streaming: bool
    supports_function_calling: bool


class ToolCallResult(BaseModel):
    """Result of executing a tool call."""

    success: bool
    message: str
    data: Optional[dict[str, Any]] = None
