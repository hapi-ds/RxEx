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
import { chatAPI, graphragAPI, mindsAPI, relationshipsAPI } from '../../services/api';
import type { ChatMessage as ChatMessageType, ChatStreamEvent, ToolCall, SuggestionLogEntry, ToolExecutionResult } from '../../types/chat';
import type { RetrievalMode } from '../../types/graphrag';
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
  isAutoAccept: boolean;
}

const CHAT_HISTORY_KEY = 'rxd3-chat-history';

export function ChatPanel() {
  const { logout } = useAuth();
  const [state, setState] = useState<ChatPanelState>(() => {
    let initialMessages: ChatMessageType[] = [];
    try {
      const stored = localStorage.getItem(CHAT_HISTORY_KEY);
      if (stored) {
        initialMessages = JSON.parse(stored);
      }
    } catch {
      localStorage.removeItem(CHAT_HISTORY_KEY);
    }
    return {
      messages: initialMessages,
      inputValue: '',
      isLoading: false,
      error: null,
      pendingToolCalls: [],
      suggestionLog: [],
      isAutoAccept: false,
    };
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<number | null>(null);

  // GraphRAG retrieval mode state (separate from main state to minimize changes)
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>('auto');
  const [graphragEnabled, setGraphragEnabled] = useState<boolean>(false);
  const [activeRetrievalMode, setActiveRetrievalMode] = useState<string | null>(null);

  // Check if GraphRAG is enabled on mount
  useEffect(() => {
    graphragAPI.getStatus()
      .then(status => setGraphragEnabled(status.graphrag_enabled))
      .catch(() => setGraphragEnabled(false));
  }, []);

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(state.messages));
    } catch {
      // Silently fail if localStorage is full or unavailable
    }
  }, [state.messages]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  // Auto-execute pending tool calls if Auto-Accept is enabled and stream finished
  useEffect(() => {
    if (!state.isLoading && state.pendingToolCalls.length > 0 && state.isAutoAccept) {
      // Small timeout to allow state settling
      setTimeout(() => {
        handleConfirmAllToolCalls();
      }, 50);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.isLoading, state.isAutoAccept]);

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
      const stream = await chatAPI.sendMessage(content, state.messages, retrievalMode);
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
            if (event.metadata?.retrieval_mode) {
              setActiveRetrievalMode(event.metadata.retrieval_mode as string);
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
            if (event.metadata?.retrieval_mode) {
              setActiveRetrievalMode(event.metadata.retrieval_mode as string);
            }
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
  }, [state.inputValue, state.isLoading, state.messages, retrievalMode, logout]);

  // Execute a single tool call (used by confirm and confirm-all)
  const executeToolCall = useCallback(async (toolCall: ToolCall): Promise<ToolExecutionResult> => {
    const toolName = toolCall.tool_name;
    try {
      if (toolName === 'create_mind_node') {
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

        window.dispatchEvent(new CustomEvent('graph-refresh'));
        return { success: true, uuid: createdMind.uuid, title: title as string, toolName };

      } else if (toolName === 'create_relationship') {
        const { source_uuid, target_uuid, relationship_type } = toolCall.arguments;
        await relationshipsAPI.create({
          source: source_uuid as string,
          target: target_uuid as string,
          type: (relationship_type as string).toUpperCase() as any,
          properties: {},
        });

        window.dispatchEvent(new CustomEvent('graph-refresh'));
        return { success: true, toolName };
      }
      return { success: false, toolName };
    } catch (error: any) {
      console.error('Tool call execution error:', error);

      const errorMessage: ChatMessageType = {
        role: 'user',
        content: `System: Failed to execute action: ${error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
      }));
      return { success: false, toolName, error: error.message || 'Unknown error' };
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

    const result = await executeToolCall(toolCall);

    setState(prev => ({
      ...prev,
      isLoading: false,
    }));

    let feedbackMessage: string;
    if (result.success) {
      if (result.toolName === 'create_mind_node') {
        feedbackMessage = `[Tool Result] create_mind_node succeeded. Created node: '${result.title}' (uuid: ${result.uuid})`;
      } else if (result.toolName === 'create_relationship') {
        const { relationship_type, source_uuid, target_uuid } = toolCall.arguments;
        feedbackMessage = `[Tool Result] create_relationship succeeded. Created ${relationship_type} relationship between ${source_uuid} and ${target_uuid}`;
      } else {
        feedbackMessage = `[Tool Result] ${result.toolName} succeeded.`;
      }
    } else {
      feedbackMessage = `[Tool Result] ${result.toolName} failed: ${result.error || 'Unknown error'}. Please suggest an alternative.`;
    }

    setTimeout(() => {
      handleSendMessage(feedbackMessage);
    }, 100);
  }, [state.pendingToolCalls, executeToolCall, handleSendMessage]);

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

    // Execute all sequentially, collecting results with UUIDs
    const results: { result: ToolExecutionResult; toolCall: ToolCall }[] = [];
    for (const toolCall of allCalls) {
      const result = await executeToolCall(toolCall);
      results.push({ result, toolCall });
    }

    setState(prev => ({
      ...prev,
      isLoading: false,
    }));

    // Build consolidated batch feedback with UUIDs
    const lines = results.map(({ result, toolCall }, idx) => {
      const num = idx + 1;
      if (result.success) {
        if (result.toolName === 'create_mind_node') {
          return `${num}. create_mind_node succeeded — Created '${result.title}' (uuid: ${result.uuid})`;
        } else if (result.toolName === 'create_relationship') {
          const { relationship_type, source_uuid, target_uuid } = toolCall.arguments;
          return `${num}. create_relationship succeeded — Created ${relationship_type} relationship between ${source_uuid} and ${target_uuid}`;
        }
        return `${num}. ${result.toolName} succeeded`;
      }
      return `${num}. ${result.toolName} failed: ${result.error || 'Unknown error'}`;
    });

    const batchFeedback = `[Tool Result] Batch execution complete:\n${lines.join('\n')}`;

    setTimeout(() => {
      handleSendMessage(batchFeedback);
    }, 100);
  }, [state.pendingToolCalls, executeToolCall, handleSendMessage]);

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
      role: 'user',
      content: 'System: Action cancelled by user',
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
      role: 'user',
      content: `System: Cancelled ${count} pending action${count > 1 ? 's' : ''}`,
      timestamp: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, cancelMessage],
    }));
  }, [state.pendingToolCalls]);

  // Clear conversation history
  const handleClearHistory = useCallback(() => {
    localStorage.removeItem(CHAT_HISTORY_KEY);
    setState(prev => ({ ...prev, messages: [] }));
  }, []);

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
        <div className="chat-panel__controls">
          <label className="auto-accept-toggle" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '0.85rem', color: '#64748b', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={state.isAutoAccept}
              onChange={(e) => setState(prev => ({ ...prev, isAutoAccept: e.target.checked }))}
              style={{ cursor: 'pointer' }}
            />
            <span>Auto-Accept Generated Nodes & Continue</span>
          </label>
          {graphragEnabled && (
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '0.85rem', color: '#64748b' }}>
              <span>Retrieval:</span>
              <select
                value={retrievalMode}
                onChange={(e) => setRetrievalMode(e.target.value as RetrievalMode)}
                style={{ fontSize: '0.85rem', padding: '2px 4px' }}
              >
                <option value="auto">Auto</option>
                <option value="local">Local</option>
                <option value="global">Global</option>
                <option value="hybrid">Hybrid</option>
              </select>
              {activeRetrievalMode && (
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic' }}>
                  (active: {activeRetrievalMode})
                </span>
              )}
            </label>
          )}
          <button
            className="chat-panel__clear-history"
            onClick={handleClearHistory}
            style={{ fontSize: '0.85rem', padding: '2px 8px', color: '#64748b', background: 'none', border: '1px solid #e2e8f0', borderRadius: '4px', cursor: 'pointer' }}
          >
            Clear History
          </button>
        </div>
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
