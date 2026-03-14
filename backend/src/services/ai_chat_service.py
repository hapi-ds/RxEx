"""
AI Chat Service for handling AI provider communication.

This module implements the AIChatService class that orchestrates AI provider
communication with streaming and function calling support. It combines user
messages with project context from KnowledgeStore and validates tool calls
against Neo4j schema.

**Validates: Requirements 3.2, 9.2, 11.1, 11.2, 11.3, 11.12**
"""

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from ..config.config import Settings
from .knowledge_store import KnowledgeStore

logger = logging.getLogger(__name__)


class AIChatService:
    """
    Service class for AI provider communication with streaming and function calling.

    This class handles communication with AI providers (OpenAI, Anthropic, LM-Studio),
    manages conversation context, and validates tool calls for graph operations.

    **Validates: Requirements 3.2, 9.2, 11.1, 11.2, 11.3, 11.12**
    """

    def __init__(self, settings: Settings, knowledge_store: KnowledgeStore):
        """
        Initialize AIChatService with settings and knowledge store.

        Args:
            settings: Application settings containing AI provider configuration
            knowledge_store: KnowledgeStore instance for retrieving project context

        **Validates: Requirement 3.2**
        """
        self.settings = settings
        self.knowledge_store = knowledge_store

        # Valid mind types (lowercase versions of Mind classes)
        self.valid_mind_types = [
            "project",
            "task",
            "company",
            "department",
            "email",
            "knowledge",
            "acceptancecriteria",
            "risk",
            "failure",
            "requirement",
            "resource",
            "journalentry",
            "booking",
            "sprint",
            "account",
            "schedulehistory",
            "scheduledtask",
        ]

    def _build_messages(
        self,
        user_message: str,
        context_prompt: str,
        conversation_history: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """
        Build message array for AI provider.

        Combines system message with context prompt, conversation history
        (limited to ai_max_history_messages), and current user message.

        Args:
            user_message: Current user message content
            context_prompt: Project context from KnowledgeStore
            conversation_history: Previous messages in the conversation

        Returns:
            List of message dictionaries with "role" and "content" keys

        **Validates: Requirements 3.2, 9.2**
        """
        messages = []

        # Add system message with context prompt
        messages.append({"role": "system", "content": context_prompt})

        # Add conversation history (limited to ai_max_history_messages)
        max_history = self.settings.ai_max_history_messages
        if conversation_history:
            # Take the most recent messages up to the limit
            limited_history = conversation_history[-max_history:]
            for msg in limited_history:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    async def _build_tools(self) -> list[dict]:
        """
        Build function/tool definitions for graph operations.

        Dynamically fetches available mind node types and relationship types
        from the KnowledgeStore so the AI knows the full schema.

        Returns:
            List of tool definition dictionaries in OpenAI function calling format

        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        # Fetch available types from Neo4j via KnowledgeStore
        node_types = await self.knowledge_store.get_mind_node_types()
        relationship_types = await self.knowledge_store.get_relationship_types()

        # Normalize to lowercase for the enum values
        node_type_enum = [t.lower() for t in node_types] if node_types else [
            "project", "task", "risk", "knowledge", "requirement", "resource",
        ]
        rel_type_enum = [r.lower() for r in relationship_types] if relationship_types else [
            "contains", "depends_on", "assigned_to", "relates_to", "implements", "mitigates",
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_mind_node",
                    "description": "Create a new Mind node in the project graph",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mind_type": {
                                "type": "string",
                                "enum": node_type_enum,
                                "description": "Type of Mind node to create",
                            },
                            "title": {
                                "type": "string",
                                "description": "Title of the Mind node",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the Mind node",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["draft", "active", "done", "archived", "deleted"],
                                "description": "Status of the Mind node (default: draft)",
                            },
                        },
                        "required": ["mind_type", "title"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_relationship",
                    "description": "Create a relationship between two existing Mind nodes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source_uuid": {
                                "type": "string",
                                "format": "uuid",
                                "description": "UUID of the source Mind node",
                            },
                            "target_uuid": {
                                "type": "string",
                                "format": "uuid",
                                "description": "UUID of the target Mind node",
                            },
                            "relationship_type": {
                                "type": "string",
                                "enum": rel_type_enum,
                                "description": "Type of relationship to create",
                            },
                        },
                        "required": ["source_uuid", "target_uuid", "relationship_type"],
                    },
                },
            },
        ]

        return tools

    async def validate_tool_call(self, tool_name: str, arguments: dict) -> bool:
        """
        Validate proposed node/relationship against Neo4j schema.

        Checks that:
        - For create_mind_node: mind_type is a valid Mind type
        - For create_relationship: relationship_type is a valid relationship type

        Args:
            tool_name: Name of the tool being called
            arguments: Tool call arguments dictionary

        Returns:
            True if valid, False otherwise

        **Validates: Requirements 11.2, 11.3, 11.12**
        """
        if tool_name == "create_mind_node":
            mind_type = arguments.get("mind_type", "").lower()
            return mind_type in self.valid_mind_types

        elif tool_name == "create_relationship":
            relationship_type = arguments.get("relationship_type", "").upper()
            # Get valid relationship types from knowledge store
            valid_relationship_types = await self.knowledge_store.get_relationship_types()
            return relationship_type in valid_relationship_types

        # Unknown tool name
        return False

    async def send_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, Any]],
        user_email: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Send message to AI provider and yield streaming events.

        Combines user message with context from KnowledgeStore and routes to
        the appropriate provider (_call_openai or _call_anthropic). Yields
        ChatStreamEvent dictionaries as they arrive from the provider.

        Args:
            user_message: Current user message content
            conversation_history: Previous messages in the conversation
            user_email: Email of the user making the request (for logging)

        Yields:
            ChatStreamEvent dictionaries with keys:
            - type: "message_chunk", "function_call", "error", or "done"
            - content: Text content (for message_chunk)
            - tool_name: Tool name (for function_call)
            - arguments: Tool arguments dict (for function_call)
            - error_message: Error description (for error)

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**
        """
        logger.info(
            "Chat request",
            extra={
                "user_email": user_email,
                "message_length": len(user_message),
                "provider": self.settings.ai_provider,
                "model": self.settings.ai_model_name,
            },
        )

        try:
            # Invalidate node cache so the AI always sees freshly created nodes
            self.knowledge_store.invalidate_cache("mind_nodes")

            # Get context prompt from knowledge store
            context_prompt = await self.knowledge_store.generate_context_prompt()

            # Build messages array
            messages = self._build_messages(user_message, context_prompt, conversation_history)

            # Build tools array
            tools = await self._build_tools()

            # Route to appropriate provider
            if self.settings.ai_provider in ("openai", "lm-studio", "custom"):
                async for event in self._call_openai(messages, tools):
                    yield event
            elif self.settings.ai_provider == "anthropic":
                async for event in self._call_anthropic(messages, tools):
                    yield event
            else:
                # Provider not configured or unsupported
                logger.error(
                    "Unsupported AI provider",
                    extra={"provider": self.settings.ai_provider},
                )
                yield {
                    "type": "error",
                    "error_message": f"Unsupported AI provider: {self.settings.ai_provider}",
                }
                yield {"type": "done"}

        except Exception as e:
            logger.error(
                "Chat request failed",
                extra={
                    "user_email": user_email,
                    "error": str(e),
                    "provider": self.settings.ai_provider,
                },
                exc_info=True,
            )
            yield {
                "type": "error",
                "error_message": f"Internal error: {str(e)}",
            }
            yield {"type": "done"}

    async def _call_openai(
        self, messages: list[dict[str, str]], tools: list[dict]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Send request to OpenAI-compatible API (OpenAI, LM-Studio, custom).

        Uses httpx to make async HTTP requests with streaming enabled. Parses
        Server-Sent Events (SSE) format and yields ChatStreamEvent dictionaries.

        Args:
            messages: Message array with role and content
            tools: Tool definitions array

        Yields:
            ChatStreamEvent dictionaries

        **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**
        """
        endpoint = self.settings.ai_api_endpoint
        if not endpoint:
            yield {
                "type": "error",
                "error_message": "AI API endpoint not configured",
            }
            yield {"type": "done"}
            return

        # Build request payload
        payload = {
            "model": self.settings.ai_model_name,
            "messages": messages,
            "tools": tools,
            "stream": True,
        }

        # Build headers
        headers = {"Content-Type": "application/json"}
        if self.settings.ai_api_key:
            headers["Authorization"] = f"Bearer {self.settings.ai_api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.settings.ai_request_timeout) as client:
                async with client.stream(
                    "POST",
                    f"{endpoint}/chat/completions",
                    json=payload,
                    headers=headers,
                ) as response:
                    # Check for HTTP errors
                    if response.status_code != 200:
                        error_text = await response.aread()
                        error_msg = self._map_openai_error(response.status_code, error_text.decode())
                        logger.error(
                            "OpenAI API error",
                            extra={
                                "status_code": response.status_code,
                                "error": error_msg,
                            },
                        )
                        yield {"type": "error", "error_message": error_msg}
                        yield {"type": "done"}
                        return

                    # Parse SSE stream
                    # Accumulate tool call data across chunks
                    # (name arrives in first chunk, arguments stream incrementally)
                    pending_tool_calls: dict[int, dict[str, str]] = {}

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if not choices:
                                    continue

                                delta = choices[0].get("delta", {})

                                # Handle content chunks
                                if "content" in delta and delta["content"]:
                                    yield {
                                        "type": "message_chunk",
                                        "content": delta["content"],
                                    }

                                # Accumulate tool call chunks
                                if "tool_calls" in delta:
                                    for tool_call in delta["tool_calls"]:
                                        idx = tool_call.get("index", 0)
                                        if idx not in pending_tool_calls:
                                            pending_tool_calls[idx] = {"name": "", "arguments": ""}
                                        func = tool_call.get("function", {})
                                        if func.get("name"):
                                            pending_tool_calls[idx]["name"] = func["name"]
                                        if func.get("arguments"):
                                            pending_tool_calls[idx]["arguments"] += func["arguments"]

                            except json.JSONDecodeError:
                                logger.warning(
                                    "Failed to parse SSE data",
                                    extra={"data": data_str},
                                )
                                continue

                    # Emit accumulated tool calls after stream completes
                    for _idx, tc in sorted(pending_tool_calls.items()):
                        if tc["name"]:
                            try:
                                arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
                                yield {
                                    "type": "function_call",
                                    "tool_name": tc["name"],
                                    "arguments": arguments,
                                }
                            except json.JSONDecodeError:
                                logger.warning(
                                    "Failed to parse accumulated tool call arguments",
                                    extra={"name": tc["name"], "arguments": tc["arguments"]},
                                )

            yield {"type": "done"}

        except httpx.TimeoutException:
            logger.error("OpenAI API request timed out")
            yield {
                "type": "error",
                "error_message": "Request timed out. Try a shorter message.",
            }
            yield {"type": "done"}

        except httpx.ConnectError as e:
            logger.error("Failed to connect to OpenAI API", extra={"error": str(e)})
            yield {
                "type": "error",
                "error_message": "Failed to connect to AI provider. Check endpoint configuration.",
            }
            yield {"type": "done"}

        except httpx.HTTPStatusError as e:
            logger.error("OpenAI API HTTP error", extra={"error": str(e)})
            error_msg = self._map_openai_error(e.response.status_code, str(e))
            yield {"type": "error", "error_message": error_msg}
            yield {"type": "done"}

        except Exception as e:
            logger.error("Unexpected error in OpenAI call", extra={"error": str(e)}, exc_info=True)
            yield {
                "type": "error",
                "error_message": f"Unexpected error: {str(e)}",
            }
            yield {"type": "done"}

    async def _call_anthropic(
        self, messages: list[dict[str, str]], tools: list[dict]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Send request to Anthropic API.

        Uses httpx to make async HTTP requests with streaming enabled. Parses
        Anthropic's SSE format and yields ChatStreamEvent dictionaries.

        Args:
            messages: Message array with role and content
            tools: Tool definitions array

        Yields:
            ChatStreamEvent dictionaries

        **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**
        """
        endpoint = self.settings.ai_api_endpoint
        if not endpoint:
            yield {
                "type": "error",
                "error_message": "AI API endpoint not configured",
            }
            yield {"type": "done"}
            return

        # Anthropic requires system message to be separate
        system_message = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)

        # Build request payload
        payload = {
            "model": self.settings.ai_model_name,
            "messages": anthropic_messages,
            "tools": tools,
            "stream": True,
            "max_tokens": 4096,
        }
        if system_message:
            payload["system"] = system_message

        # Build headers
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if self.settings.ai_api_key:
            headers["x-api-key"] = self.settings.ai_api_key

        try:
            async with httpx.AsyncClient(timeout=self.settings.ai_request_timeout) as client:
                async with client.stream(
                    "POST",
                    f"{endpoint}/messages",
                    json=payload,
                    headers=headers,
                ) as response:
                    # Check for HTTP errors
                    if response.status_code != 200:
                        error_text = await response.aread()
                        error_msg = self._map_anthropic_error(response.status_code, error_text.decode())
                        logger.error(
                            "Anthropic API error",
                            extra={
                                "status_code": response.status_code,
                                "error": error_msg,
                            },
                        )
                        yield {"type": "error", "error_message": error_msg}
                        yield {"type": "done"}
                        return

                    # Parse SSE stream
                    # Accumulate tool use data across chunks
                    # (name arrives in content_block_start, input streams via input_json_delta)
                    pending_tool_calls: dict[int, dict[str, Any]] = {}

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix

                            try:
                                data = json.loads(data_str)
                                event_type = data.get("type")

                                # Handle content block delta (text chunks)
                                if event_type == "content_block_delta":
                                    delta = data.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        text = delta.get("text", "")
                                        if text:
                                            yield {
                                                "type": "message_chunk",
                                                "content": text,
                                            }
                                    # Accumulate tool input JSON chunks
                                    elif delta.get("type") == "input_json_delta":
                                        idx = data.get("index", 0)
                                        if idx in pending_tool_calls:
                                            pending_tool_calls[idx]["arguments"] += delta.get("partial_json", "")

                                # Handle tool use start (captures name, input arrives later)
                                elif event_type == "content_block_start":
                                    content_block = data.get("content_block", {})
                                    if content_block.get("type") == "tool_use":
                                        idx = data.get("index", 0)
                                        pending_tool_calls[idx] = {
                                            "name": content_block.get("name", ""),
                                            "arguments": "",
                                        }

                                # Emit tool call when its content block stops
                                elif event_type == "content_block_stop":
                                    idx = data.get("index", 0)
                                    if idx in pending_tool_calls:
                                        tc = pending_tool_calls.pop(idx)
                                        if tc["name"]:
                                            try:
                                                arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
                                                yield {
                                                    "type": "function_call",
                                                    "tool_name": tc["name"],
                                                    "arguments": arguments,
                                                }
                                            except json.JSONDecodeError:
                                                logger.warning(
                                                    "Failed to parse Anthropic tool call arguments",
                                                    extra={"name": tc["name"], "arguments": tc["arguments"]},
                                                )

                            except json.JSONDecodeError:
                                logger.warning(
                                    "Failed to parse SSE data",
                                    extra={"data": data_str},
                                )
                                continue

                    # Emit any remaining tool calls
                    for _idx, tc in sorted(pending_tool_calls.items()):
                        if tc["name"]:
                            try:
                                arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
                                yield {
                                    "type": "function_call",
                                    "tool_name": tc["name"],
                                    "arguments": arguments,
                                }
                            except json.JSONDecodeError:
                                logger.warning(
                                    "Failed to parse Anthropic tool call arguments",
                                    extra={"name": tc["name"], "arguments": tc["arguments"]},
                                )

            yield {"type": "done"}

        except httpx.TimeoutException:
            logger.error("Anthropic API request timed out")
            yield {
                "type": "error",
                "error_message": "Request timed out. Try a shorter message.",
            }
            yield {"type": "done"}

        except httpx.ConnectError as e:
            logger.error("Failed to connect to Anthropic API", extra={"error": str(e)})
            yield {
                "type": "error",
                "error_message": "Failed to connect to AI provider. Check endpoint configuration.",
            }
            yield {"type": "done"}

        except httpx.HTTPStatusError as e:
            logger.error("Anthropic API HTTP error", extra={"error": str(e)})
            error_msg = self._map_anthropic_error(e.response.status_code, str(e))
            yield {"type": "error", "error_message": error_msg}
            yield {"type": "done"}

        except Exception as e:
            logger.error("Unexpected error in Anthropic call", extra={"error": str(e)}, exc_info=True)
            yield {
                "type": "error",
                "error_message": f"Unexpected error: {str(e)}",
            }
            yield {"type": "done"}

    def _map_openai_error(self, status_code: int, error_text: str) -> str:
        """Map OpenAI API error codes to user-friendly messages."""
        if status_code == 401:
            return "Invalid API key. Check AI_API_KEY configuration."
        elif status_code == 429:
            return "AI provider rate limit reached. Please wait."
        elif status_code >= 500:
            return "AI provider is experiencing issues. Try again later."
        else:
            return f"AI provider error: {error_text[:200]}"

    def _map_anthropic_error(self, status_code: int, error_text: str) -> str:
        """Map Anthropic API error codes to user-friendly messages."""
        if status_code == 401:
            return "Invalid API key. Check AI_API_KEY configuration."
        elif status_code == 429:
            return "AI provider is overloaded. Please wait."
        elif status_code >= 500:
            return "AI provider is experiencing issues. Try again later."
        else:
            return f"AI provider error: {error_text[:200]}"
