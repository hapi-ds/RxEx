/**
 * ChatPanel Component
 * Main chat interface for AI assistant integration
 * 
 * Features:
 * - Message history with auto-scroll
 * - Streaming response handling
 * - Error handling with retry
 * - Tool call confirmation flow
 * - Debounced message submission
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { chatAPI, mindsAPI, relationshipsAPI } from '../../services/api';
import type { ChatMessage as ChatMessageType, ChatStreamEvent, ToolCall, SuggestionLogEntry } from '../../types/chat';
import type { Mind } from '../../types/generated';
import { ChatMessage } from './ChatMessage';
import { ConfirmToolCallDialog } from './ConfirmToolCallDialog';
import './ChatPanel.css';

interface ChatPanelState {
  messages: ChatMessageType[];
  inputValue: string;
  isLoading: boolean;
  error: string | null;
  pendingToolCalls: ToolCall[];
  suggestionLog: SuggestionLogEntry[];
}

export function ChatPanel() {
  const { logout } = useAuth();
  const [state, setState] = useState<ChatPanelState>({
    messages: [],
    inputValue: '',
    isLoading: false,
    error: null,
    pendingToolCalls: [],
    suggestionLog: [],
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<number | null>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  // Handle sending a message
  const handleSendMessage = useCallback(async (messageContent?: string) => {
    const content = messageContent || state.inputValue.trim();
    
    if (!content || state.isLoading) {
      return;
    }

    // Clear debounce timer if exists
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }

    // Add user message to history
    const userMessage: ChatMessageType = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      inputValue: '',
      isLoading: true,
      error: null,
    }));

    try {
      // Call chat API with streaming
      const stream = await chatAPI.sendMessage(content, state.messages);
      const reader = stream.getReader();

      // Initialize assistant message
      let assistantContent = '';
      const assistantMessage: ChatMessageType = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Read stream events
      let result;
      while (!(result = await reader.read()).done) {
        const event: ChatStreamEvent = result.value;

        switch (event.type) {
          case 'message_chunk':
            if (event.content) {
              assistantContent += event.content;
              setState(prev => ({
                ...prev,
                messages: prev.messages.map((msg, idx) =>
                  idx === prev.messages.length - 1
                    ? { ...msg, content: assistantContent }
                    : msg
                ),
              }));
            }
            break;

          case 'function_call':
            if (event.tool_name && event.arguments) {
              setState(prev => ({
                ...prev,
                pendingToolCalls: [
                  ...prev.pendingToolCalls,
                  {
                    tool_name: event.tool_name!,
                    arguments: event.arguments!,
                  },
                ],
              }));
            }
            break;

          case 'error':
            setState(prev => ({
              ...prev,
              error: event.error_message || 'An error occurred',
              isLoading: false,
            }));
            
            // Add error as system message
            const errorMessage: ChatMessageType = {
              role: 'system',
              content: `Error: ${event.error_message || 'An error occurred'}`,
              timestamp: new Date().toISOString(),
            };
            setState(prev => ({
              ...prev,
              messages: [...prev.messages, errorMessage],
            }));
            return;

          case 'done':
            setState(prev => ({
              ...prev,
              isLoading: false,
            }));
            break;
        }
      }

      setState(prev => ({
        ...prev,
        isLoading: false,
      }));

    } catch (error: any) {
      console.error('Chat error:', error);

      // Handle 401 errors by logging out
      if (error.message?.includes('401') || error.message?.includes('Not authenticated')) {
        logout();
        return;
      }

      // Determine error message based on error type
      let errorMessage = 'An unexpected error occurred';
      
      if (error.message?.includes('503')) {
        errorMessage = 'AI provider is currently unavailable. Please try again later.';
      } else if (error.message?.includes('504')) {
        errorMessage = 'Request timed out. Please try a shorter message.';
      } else if (error.message?.includes('not configured')) {
        errorMessage = 'AI provider is not configured. Please contact your administrator.';
      } else if (error.message) {
        errorMessage = error.message;
      }

      setState(prev => ({
        ...prev,
        error: errorMessage,
        isLoading: false,
      }));

      // Add error as system message
      const errorMsg: ChatMessageType = {
        role: 'system',
        content: `Error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMsg],
      }));
    }
  }, [state.inputValue, state.isLoading, state.messages, logout]);

  // Execute a single tool call (used by confirm and confirm-all)
  const executeToolCall = useCallback(async (toolCall: ToolCall): Promise<boolean> => {
    try {
      if (toolCall.tool_name === 'create_mind_node') {
        const { mind_type, title, description, status } = toolCall.arguments;
        
        let creator = 'ai-chat';
        try {
          const token = localStorage.getItem('token');
          if (token) {
            const payload = JSON.parse(atob(token.split('.')[1]));
            creator = payload.sub || payload.email || 'ai-chat';
          }
        } catch {
          // fallback to default
        }
        
        const createPayload: Record<string, unknown> = {
          mind_type: (mind_type as string).toLowerCase(),
          title: title as string,
          creator,
        };
        
        if (description) {
          createPayload.description = description as string;
        }
        
        if (status) {
          createPayload.status = (status as string).toLowerCase();
        }
        
        const createdMind = await mindsAPI.create(createPayload as Omit<Mind, 'uuid' | 'version' | 'created_at' | 'updated_at'>);

        const successMessage: ChatMessageType = {
          role: 'system',
          content: `✓ Successfully created ${mind_type} node: "${title}" (uuid: ${createdMind.uuid})`,
          timestamp: new Date().toISOString(),
        };

        setState(prev => ({
          ...prev,
          messages: [...prev.messages, successMessage],
        }));

        window.dispatchEvent(new CustomEvent('graph-refresh'));
        return true;

      } else if (toolCall.tool_name === 'create_relationship') {
        const { source_uuid, target_uuid, relationship_type } = toolCall.arguments;
        await relationshipsAPI.create({
          source: source_uuid as string,
          target: target_uuid as string,
          type: (relationship_type as string).toUpperCase() as any,
          properties: {},
        });

        const successMessage: ChatMessageType = {
          role: 'system',
          content: `✓ Successfully created ${relationship_type} relationship`,
          timestamp: new Date().toISOString(),
        };

        setState(prev => ({
          ...prev,
          messages: [...prev.messages, successMessage],
        }));

        window.dispatchEvent(new CustomEvent('graph-refresh'));
        return true;
      }
      return false;
    } catch (error: any) {
      console.error('Tool call execution error:', error);

      const errorMessage: ChatMessageType = {
        role: 'system',
        content: `✗ Failed to execute action: ${error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
      }));
      return false;
    }
  }, []);

  // Handle confirming a single tool call (first in queue)
  const handleConfirmToolCall = useCallback(async (editedToolCall?: ToolCall) => {
    const currentToolCall = state.pendingToolCalls[0];
    const toolCall = editedToolCall || currentToolCall;
    if (!toolCall) {
      return;
    }

    const logEntry: SuggestionLogEntry = {
      timestamp: new Date().toISOString(),
      tool_call: toolCall,
      action: 'confirmed',
    };

    // Remove first item from queue
    setState(prev => ({
      ...prev,
      suggestionLog: [...prev.suggestionLog, logEntry],
      pendingToolCalls: prev.pendingToolCalls.slice(1),
      isLoading: true,
    }));

    await executeToolCall(toolCall);

    setState(prev => ({
      ...prev,
      isLoading: false,
    }));
  }, [state.pendingToolCalls, executeToolCall]);

  // Handle confirming all pending tool calls at once
  const handleConfirmAllToolCalls = useCallback(async () => {
    if (state.pendingToolCalls.length === 0) {
      return;
    }

    const allCalls = [...state.pendingToolCalls];

    // Log all as confirmed and clear queue
    const logEntries: SuggestionLogEntry[] = allCalls.map(tc => ({
      timestamp: new Date().toISOString(),
      tool_call: tc,
      action: 'confirmed' as const,
    }));

    setState(prev => ({
      ...prev,
      suggestionLog: [...prev.suggestionLog, ...logEntries],
      pendingToolCalls: [],
      isLoading: true,
    }));

    // Execute all sequentially
    for (const toolCall of allCalls) {
      await executeToolCall(toolCall);
    }

    setState(prev => ({
      ...prev,
      isLoading: false,
    }));
  }, [state.pendingToolCalls, executeToolCall]);

  // Handle canceling the current tool call (first in queue)
  const handleCancelToolCall = useCallback(() => {
    const currentToolCall = state.pendingToolCalls[0];
    if (!currentToolCall) {
      return;
    }

    const logEntry: SuggestionLogEntry = {
      timestamp: new Date().toISOString(),
      tool_call: currentToolCall,
      action: 'rejected',
    };

    setState(prev => ({
      ...prev,
      suggestionLog: [...prev.suggestionLog, logEntry],
      pendingToolCalls: prev.pendingToolCalls.slice(1),
    }));

    const cancelMessage: ChatMessageType = {
      role: 'system',
      content: 'Action cancelled by user',
      timestamp: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, cancelMessage],
    }));
  }, [state.pendingToolCalls]);

  // Handle canceling all pending tool calls
  const handleCancelAllToolCalls = useCallback(() => {
    if (state.pendingToolCalls.length === 0) {
      return;
    }

    const logEntries: SuggestionLogEntry[] = state.pendingToolCalls.map(tc => ({
      timestamp: new Date().toISOString(),
      tool_call: tc,
      action: 'rejected' as const,
    }));

    const count = state.pendingToolCalls.length;

    setState(prev => ({
      ...prev,
      suggestionLog: [...prev.suggestionLog, ...logEntries],
      pendingToolCalls: [],
    }));

    const cancelMessage: ChatMessageType = {
      role: 'system',
      content: `Cancelled ${count} pending action${count > 1 ? 's' : ''}`,
      timestamp: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, cancelMessage],
    }));
  }, [state.pendingToolCalls]);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setState(prev => ({
      ...prev,
      inputValue: e.target.value,
    }));
  };

  // Handle input key down (Enter to send, Shift+Enter for new line)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      
      // Debounce rapid submissions (300ms)
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(() => {
        handleSendMessage();
        debounceTimerRef.current = null;
      }, 300);
    }
  };

  // Handle retry button click
  const handleRetry = () => {
    if (state.error && state.messages.length > 0) {
      // Find the last user message
      const lastUserMessage = [...state.messages]
        .reverse()
        .find(msg => msg.role === 'user');
      
      if (lastUserMessage) {
        handleSendMessage(lastUserMessage.content);
      }
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-panel__messages">
        {state.messages.map((message, index) => (
          <ChatMessage
            key={`${message.timestamp}-${index}`}
            message={message}
            role={message.role}
          />
        ))}
        
        {state.isLoading && (
          <div className="chat-panel__loading">
            <div className="loading-spinner" />
            <span>AI is thinking...</span>
          </div>
        )}

        {state.error && (
          <div className="chat-panel__error">
            <button
              className="retry-button"
              onClick={handleRetry}
              disabled={state.isLoading}
            >
              Retry
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-panel__input-area">
        <textarea
          className="chat-panel__input"
          value={state.inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask me about your project..."
          disabled={state.isLoading}
          rows={3}
        />
        <button
          className="chat-panel__send-button"
          onClick={() => handleSendMessage()}
          disabled={state.isLoading || !state.inputValue.trim()}
        >
          Send
        </button>
      </div>

      {state.pendingToolCalls.length > 0 && (
        <ConfirmToolCallDialog
          toolCall={state.pendingToolCalls[0]}
          totalCount={state.pendingToolCalls.length}
          currentIndex={0}
          onConfirm={handleConfirmToolCall}
          onCancel={handleCancelToolCall}
          onConfirmAll={state.pendingToolCalls.length > 1 ? handleConfirmAllToolCalls : undefined}
          onCancelAll={state.pendingToolCalls.length > 1 ? handleCancelAllToolCalls : undefined}
        />
      )}
    </div>
  );
}
