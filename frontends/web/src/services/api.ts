/**
 * API service layer for the FastAPI Neo4j Multi-Frontend System
 * Handles all HTTP requests to the backend with JWT authentication
 */

import axios, { type AxiosInstance } from 'axios';
import { config } from '../config';
import type { LoginCredentials, Token, PostCreate, PostUpdate, Post, Relationship, RelationshipType } from '../types';
import type { Mind } from '../types/generated';
import type { ChatMessage, ChatStreamEvent, ChatConfig } from '../types/chat';

/**
 * Create axios instance with base configuration
 */
const api: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to include JWT token from localStorage
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle 403 errors (invalid/expired tokens)
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 403) {
      // Token is invalid or expired, clear it and redirect to login
      localStorage.removeItem('token');
      // Optionally trigger a redirect to login page
      // This can be handled by the component or a global error handler
      console.warn('Authentication failed. Token cleared.');
    }
    return Promise.reject(error);
  }
);

/**
 * Authentication API methods
 */
export const authAPI = {
  /**
   * Login with email and password
   * @param email - User's email address
   * @param password - User's password
   * @returns Promise with JWT token
   */
  login: async (email: string, password: string): Promise<Token> => {
    // Backend uses OAuth2PasswordRequestForm which expects form-urlencoded data
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post<Token>('/users/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  /**
   * Register a new user
   * @param email - User's email address
   * @param password - User's password
   * @param fullname - User's full name
   * @returns Promise with the created user data
   */
  register: async (email: string, password: string, fullname: string): Promise<void> => {
    await api.post('/users', { email, password, fullname });
  },
};

/**
 * Posts API methods
 */
export const postsAPI = {
  /**
   * Get all posts
   * @returns Promise with array of posts
   */
  list: async (): Promise<Post[]> => {
    const response = await api.get<Post[]>('/posts');
    return response.data;
  },

  /**
   * Create a new post
   * @param data - Post creation data
   * @returns Promise with the created post
   */
  create: async (data: PostCreate): Promise<Post> => {
    const response = await api.post<Post>('/posts', data);
    return response.data;
  },

  /**
   * Update an existing post
   * @param uuid - Post ID
   * @param data - Post update data
   * @returns Promise with the updated post
   */
  update: async (uuid: string, data: PostUpdate): Promise<Post> => {
    const response = await api.put<Post>(`/posts/${uuid}`, data);
    return response.data;
  },

  /**
   * Delete a post
   * @param uuid - Post ID
   * @returns Promise that resolves when deletion is complete
   */
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/posts/${uuid}`);
  },
};

/**
 * Minds API methods
 * **Validates: Requirements 1.1, 1.2, 4.1, 5.1, 6.1**
 */
export const mindsAPI = {
  /**
   * Get all minds
   * @returns Promise with array of minds
   */
  list: async (): Promise<Mind[]> => {
    const response = await api.get<{ items: Mind[]; total: number }>('/api/v1/minds');
    return response.data.items;
  },

  /**
   * Get a specific mind by UUID
   * @param uuid - Mind UUID
   * @returns Promise with the mind data
   */
  get: async (uuid: string): Promise<Mind> => {
    const response = await api.get<Mind>(`/api/v1/minds/${uuid}`);
    return response.data;
  },

  /**
   * Get all versions of a mind
   * @param uuid - Mind UUID
   * @returns Promise with array of all versions of the mind
   */
  getVersions: async (uuid: string): Promise<Mind[]> => {
    const response = await api.get<Mind[]>(`/api/v1/minds/${uuid}/history`);
    return response.data;
  },

  /**
   * Create a new mind
   * @param data - Mind creation data (without uuid, version, timestamps)
   * @returns Promise with the created mind
   */
  create: async (data: Omit<Mind, 'uuid' | 'version' | 'created_at' | 'updated_at'>): Promise<Mind> => {
    const response = await api.post<Mind>('/api/v1/minds', data);
    return response.data;
  },

  /**
   * Update an existing mind (creates a new version)
   * @param uuid - Mind UUID
   * @param data - Mind update data (partial updates allowed)
   * @returns Promise with the updated mind (new version)
   */
  update: async (uuid: string, data: Partial<Omit<Mind, 'uuid' | 'version' | 'created_at' | 'updated_at'>>): Promise<Mind> => {
    const response = await api.put<Mind>(`/api/v1/minds/${uuid}`, data);
    return response.data;
  },

  /**
   * Delete a mind
   * @param uuid - Mind UUID
   * @returns Promise that resolves when deletion is complete
   */
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/api/v1/minds/${uuid}`);
  },
};

/**
 * Relationships API methods
 * **Validates: Requirements 1.2, 5.2, 6.2**
 */
export const relationshipsAPI = {
  /**
   * Get all relationships
   * @returns Promise with array of relationships
   */
  list: async (): Promise<Relationship[]> => {
    const response = await api.get<Array<{
      source_uuid: string;
      target_uuid: string;
      relationship_type: string;
      created_at: string;
      properties?: Record<string, any>;
    }>>('/api/v1/relationships');
    
    // Transform backend format to frontend format
    return response.data.map(rel => ({
      id: `${rel.source_uuid}-${rel.target_uuid}-${rel.relationship_type}`,
      type: rel.relationship_type.toUpperCase() as RelationshipType,
      source: rel.source_uuid,
      target: rel.target_uuid,
      properties: rel.properties || {},
    }));
  },

  /**
   * Create a new relationship
   * @param data - Relationship creation data
   * @returns Promise with the created relationship
   */
  create: async (data: Omit<Relationship, 'id'>): Promise<Relationship> => {
    const response = await api.post<{
      source_uuid: string;
      target_uuid: string;
      relationship_type: string;
      created_at: string;
    }>('/api/v1/relationships', null, {
      params: {
        from_uuid: data.source,
        to_uuid: data.target,
        relationship_type: data.type,
      },
    });
    const rel = response.data;
    return {
      id: `${rel.source_uuid}-${rel.target_uuid}-${rel.relationship_type}`,
      type: rel.relationship_type.toUpperCase() as RelationshipType,
      source: rel.source_uuid,
      target: rel.target_uuid,
      properties: {},
    };
  },

  /**
   * Update an existing relationship
   * @param id - Relationship ID
   * @param data - Relationship update data (partial updates allowed)
   * @returns Promise with the updated relationship
   */
  update: async (id: string, data: Partial<Omit<Relationship, 'id'>>): Promise<Relationship> => {
    const response = await api.put<Relationship>(`/api/v1/relationships/${id}`, data);
    return response.data;
  },

  /**
   * Delete a relationship
   * @param id - Relationship ID
   * @returns Promise that resolves when deletion is complete
   */
  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/relationships/${id}`);
  },
};

/**
 * Chat API methods
 * **Validates: Requirements 4.1, 4.2, 8.2**
 */
export const chatAPI = {
  /**
   * Send a chat message and receive streaming response
   * @param content - User message content
   * @param conversationHistory - Previous messages in the conversation
   * @returns Promise with ReadableStream of ChatStreamEvent objects
   */
  sendMessage: async (
    content: string,
    conversationHistory: ChatMessage[]
  ): Promise<ReadableStream<ChatStreamEvent>> => {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${config.apiUrl}/api/v1/chat/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        conversation_history: conversationHistory,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorMessage;
      } catch {
        // If not JSON, use the text as-is
        errorMessage = errorText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Transform the ReadableStream to parse SSE format
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    return new ReadableStream<ChatStreamEvent>({
      async start(controller) {
        try {
          while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
              controller.close();
              break;
            }

            // Decode the chunk and add to buffer
            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages (format: "data: {json}\n\n")
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const jsonStr = line.slice(6); // Remove "data: " prefix
                if (jsonStr.trim()) {
                  try {
                    const event = JSON.parse(jsonStr) as ChatStreamEvent;
                    controller.enqueue(event);
                  } catch (parseError) {
                    console.error('Failed to parse SSE event:', parseError, jsonStr);
                  }
                }
              }
            }
          }
        } catch (error) {
          controller.error(error);
        }
      },
    });
  },

  /**
   * Get chat configuration from backend
   * @returns Promise with chat configuration
   */
  getConfig: async (): Promise<ChatConfig> => {
    const response = await api.get<ChatConfig>('/api/v1/chat/config');
    return response.data;
  },
};

/**
 * Export the configured axios instance for custom requests
 */
export default api;
