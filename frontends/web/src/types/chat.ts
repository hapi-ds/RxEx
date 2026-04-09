/**
 * TypeScript type definitions for AI Chat Integration
 * These types match the backend Pydantic models in backend/src/schemas/chat.py
 */

/**
 * Message role in a conversation
 */
export type MessageRole = 'user' | 'assistant' | 'system';

/**
 * Individual message in a chat conversation
 */
export interface ChatMessage {
  role: MessageRole;
  content: string;
  timestamp: string;
}

/**
 * Server-sent event for streaming chat responses
 */
export interface ChatStreamEvent {
  type: 'message_chunk' | 'function_call' | 'error' | 'done';
  content?: string;
  tool_name?: string;
  arguments?: Record<string, unknown>;
  error_message?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Chat configuration response from backend
 */
export interface ChatConfig {
  provider: string;
  model_name: string | null;
  is_configured: boolean;
  supports_streaming: boolean;
  supports_function_calling: boolean;
}

/**
 * Tool call proposal from AI assistant
 */
export interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
}

/**
 * Result of executing a confirmed tool call via executeToolCall.
 * Provides type-safe access to the outcome including any created entity's UUID.
 */
export interface ToolExecutionResult {
  success: boolean;
  uuid?: string;
  title?: string;
  toolName: string;
  error?: string;
}

/**
 * Log entry for AI suggestions (confirmed or rejected)
 */
export interface SuggestionLogEntry {
  timestamp: string;
  tool_call: ToolCall;
  action: 'confirmed' | 'rejected';
}
