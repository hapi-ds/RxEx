"""
API routes for AI chat integration.

This module defines REST API endpoints for chat operations including
sending messages with streaming responses and retrieving chat configuration.
All endpoints require JWT authentication.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 8.1, 8.4**
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..auth.deps import get_current_user
from ..config.config import settings
from ..models.user import UserNode
from ..schemas.chat import ChatConfigResponse, ChatMessageRequest, ChatStreamEvent
from ..services import AIChatService, KnowledgeStore

logger = logging.getLogger(__name__)

# Create router without prefix (app.py handles the prefix)
router = APIRouter()


async def format_sse_event(event: dict) -> str:
    """
    Format a dictionary as a Server-Sent Event.

    Args:
        event: Event dictionary to format

    Returns:
        Formatted SSE string with "data: {json}\n\n" format
    """
    return f"data: {json.dumps(event)}\n\n"


async def stream_chat_response(
    service: AIChatService,
    user_message: str,
    conversation_history: list[dict],
    user_email: str,
    retrieval_mode: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream chat response as Server-Sent Events.

    Args:
        service: AIChatService instance
        user_message: User's message content
        conversation_history: Previous conversation messages
        user_email: Email of the authenticated user
        retrieval_mode: Optional GraphRAG retrieval mode (local/global/hybrid/auto)

    Yields:
        SSE-formatted strings
    """
    try:
        async for event in service.send_message(
            user_message=user_message,
            conversation_history=conversation_history,
            user_email=user_email,
            retrieval_mode=retrieval_mode,
        ):
            yield await format_sse_event(event)
    except Exception as e:
        logger.error(
            "Error in stream_chat_response",
            extra={
                "error": str(e),
                "user_email": user_email,
                "provider": settings.ai_provider,
                "model": settings.ai_model_name,
            },
            exc_info=True,
        )
        # Yield error event
        error_event = {
            "type": "error",
            "error_message": f"Internal error: {str(e)}",
        }
        yield await format_sse_event(error_event)
        # Yield done event
        done_event = {"type": "done"}
        yield await format_sse_event(done_event)


@router.post("/messages")
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: UserNode = Depends(get_current_user),
) -> StreamingResponse:
    """
    Send a chat message and stream the AI response.

    Requires JWT authentication. Accepts a user message and optional conversation
    history, combines with project context from Neo4j, and streams the AI response
    as Server-Sent Events.

    Args:
        request: ChatMessageRequest with content and conversation_history
        current_user: Authenticated user from JWT token

    Returns:
        StreamingResponse with text/event-stream media type

    Raises:
        HTTPException: 503 if AI provider is not configured

    **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 8.1, 8.4**
    """
    # Check if AI provider is configured
    if settings.ai_provider == "none":
        logger.warning(
            "Chat request with unconfigured AI provider",
            extra={"user_email": current_user.email},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI provider not configured. Please configure AI_PROVIDER in environment variables.",
        )

    # Create service instances
    knowledge_store = KnowledgeStore()
    ai_chat_service = AIChatService(settings=settings, knowledge_store=knowledge_store)

    # Convert ChatMessage objects to dicts for service layer
    conversation_history = [
        {
            "role": msg.role.value,
            "content": msg.content,
        }
        for msg in request.conversation_history
    ]

    logger.info(
        "Chat message request",
        extra={
            "user_email": current_user.email,
            "message_length": len(request.content),
            "history_length": len(conversation_history),
        },
    )

    # Return streaming response
    return StreamingResponse(
        stream_chat_response(
            service=ai_chat_service,
            user_message=request.content,
            conversation_history=conversation_history,
            user_email=current_user.email,
            retrieval_mode=request.retrieval_mode,
        ),
        media_type="text/event-stream",
    )


@router.get("/config")
async def get_chat_config(
    current_user: UserNode = Depends(get_current_user),
) -> ChatConfigResponse:
    """
    Get chat configuration information.

    Returns the configured AI provider type, model name, and capability flags.
    Does NOT expose API keys or other sensitive configuration.

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        ChatConfigResponse with provider info and capabilities

    **Validates: Requirements 4.4, 4.6, 4.7, 4.8**
    """
    is_configured = settings.ai_provider != "none"

    logger.info(
        "Chat config request",
        extra={
            "user_email": current_user.email,
            "provider": settings.ai_provider,
            "model": settings.ai_model_name,
            "is_configured": is_configured,
        },
    )

    return ChatConfigResponse(
        provider=settings.ai_provider,
        model_name=settings.ai_model_name,
        is_configured=is_configured,
        supports_streaming=True,  # All providers support streaming
        supports_function_calling=True,  # All providers support function calling
    )
