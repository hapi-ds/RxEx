/**
 * API service layer for the FastAPI Neo4j Multi-Frontend System
 * Handles all HTTP requests to the backend with JWT authentication
 */

import axios, { type AxiosInstance } from 'axios';
import { config } from '../config';
import type { LoginCredentials, Token, PostCreate, PostUpdate, Post, Relationship, RelationshipType, SaveFileData, ReadResponse, ClearResponse, Skill, SkillDetail, SkillCreate, SkillUpdate, ScheduleHistory, ScheduledTaskEnriched, ScheduleCreateResponse } from '../types';
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
 * Response interceptor to handle 401/403 errors (invalid/expired tokens)
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Token is invalid or expired, clear it and redirect to login
      localStorage.removeItem('token');
      console.warn('Authentication failed. Token cleared.');
      window.location.href = '/login';
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
 * Flatten type_specific_attributes from backend MindResponse into top-level Mind fields.
 * The backend returns type-specific fields (e.g., department_code) nested inside
 * type_specific_attributes, but the frontend Mind types expect them as flat fields.
 */
function flattenMind(raw: Record<string, unknown>): Mind {
  const { type_specific_attributes, ...rest } = raw;
  if (type_specific_attributes && typeof type_specific_attributes === 'object') {
    return { ...rest, ...(type_specific_attributes as Record<string, unknown>) } as unknown as Mind;
  }
  return raw as unknown as Mind;
}

/**
 * Minds API methods
 * **Validates: Requirements 1.1, 1.2, 4.1, 5.1, 6.1**
 */
export const mindsAPI = {
  /**
   * Get all minds (fetches all pages)
   * @returns Promise with array of all minds
   */
  list: async (): Promise<Mind[]> => {
    const pageSize = 100;
    const response = await api.get<{ items: Record<string, unknown>[]; total: number; total_pages: number }>('/api/v1/minds', {
      params: { page_size: pageSize },
    });
    const allMinds = response.data.items.map(flattenMind);
    
    // Fetch remaining pages if total exceeds first page
    const totalPages = response.data.total_pages ?? 1;
    for (let page = 2; page <= totalPages; page++) {
      const nextResponse = await api.get<{ items: Record<string, unknown>[]; total: number }>('/api/v1/minds', {
        params: { page_size: pageSize, page },
      });
      allMinds.push(...nextResponse.data.items.map(flattenMind));
    }
    
    return allMinds;
  },

  /**
   * Get a specific mind by UUID
   * @param uuid - Mind UUID
   * @returns Promise with the mind data
   */
  get: async (uuid: string): Promise<Mind> => {
    const response = await api.get<Record<string, unknown>>(`/api/v1/minds/${uuid}`);
    return flattenMind(response.data);
  },

  /**
   * Get all versions of a mind
   * @param uuid - Mind UUID
   * @returns Promise with array of all versions of the mind
   */
  getVersions: async (uuid: string): Promise<Mind[]> => {
    const response = await api.get<Record<string, unknown>[]>(`/api/v1/minds/${uuid}/history`);
    return response.data.map(flattenMind);
  },

  /**
   * Create a new mind
   * @param data - Mind creation data (without uuid, version, timestamps)
   * @returns Promise with the created mind
   */
  create: async (data: Omit<Mind, 'uuid' | 'version' | 'created_at' | 'updated_at'>): Promise<Mind> => {
    const response = await api.post<Record<string, unknown>>('/api/v1/minds', data);
    return flattenMind(response.data);
  },

  /**
   * Update an existing mind (creates a new version)
   * @param uuid - Mind UUID
   * @param data - Mind update data (partial updates allowed)
   * @returns Promise with the updated mind (new version)
   */
  update: async (uuid: string, data: Partial<Omit<Mind, 'uuid' | 'version' | 'created_at' | 'updated_at'>>): Promise<Mind> => {
    const response = await api.put<Record<string, unknown>>(`/api/v1/minds/${uuid}`, data);
    return flattenMind(response.data);
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
    // Build request body; include properties for CAN_OCCUR / LEAD_TO
    const body: Record<string, unknown> = {
      from_uuid: data.source,
      to_uuid: data.target,
      relationship_type: data.type,
    };

    if (
      (data.type === 'CAN_OCCUR' || data.type === 'LEAD_TO') &&
      data.properties &&
      Object.keys(data.properties).length > 0
    ) {
      body.properties = data.properties;
    }

    const response = await api.post<{
      source_uuid: string;
      target_uuid: string;
      relationship_type: string;
      created_at: string;
      properties?: Record<string, any>;
    }>('/api/v1/relationships', body);
    const rel = response.data;
    return {
      id: `${rel.source_uuid}-${rel.target_uuid}-${rel.relationship_type}`,
      type: rel.relationship_type.toUpperCase() as RelationshipType,
      source: rel.source_uuid,
      target: rel.target_uuid,
      properties: rel.properties || {},
    };
  },

  /**
   * Update an existing relationship
   * @param id - Relationship ID
   * @param data - Relationship update data (partial updates allowed)
   * @returns Promise with the updated relationship
   */
  update: async (id: string, data: Partial<Omit<Relationship, 'id'>>): Promise<Relationship> => {
    const response = await api.put(`/api/v1/relationships/${id}`, data);
    const rel = response.data;
    return {
      id: `${rel.source_uuid}-${rel.target_uuid}-${rel.relationship_type}`,
      type: rel.relationship_type.toUpperCase() as RelationshipType,
      source: rel.source_uuid,
      target: rel.target_uuid,
      properties: rel.properties || {},
    };
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
 * Data API methods (Save/Read/Clear Generated_Data)
 */
export const dataAPI = {
  /** Save all Generated_Data as JSON */
  save: async (): Promise<SaveFileData> => {
    const response = await api.get<SaveFileData>('/api/v1/save');
    return response.data;
  },

  /** Read Generated_Data from a save file */
  read: async (data: SaveFileData): Promise<ReadResponse> => {
    const response = await api.post<ReadResponse>('/api/v1/read', data);
    return response.data;
  },

  /** Clear all Generated_Data from the database */
  clear: async (): Promise<ClearResponse> => {
    const response = await api.delete<ClearResponse>('/api/v1/clear');
    return response.data;
  },
};

/**
 * Skills API methods (CRUD + toggle)
 */
export const skillsAPI = {
  /** List all skills (without content) */
  list: async (): Promise<Skill[]> => {
    const response = await api.get<Skill[]>('/api/v1/skills');
    return response.data;
  },

  /** Get a single skill with full content */
  get: async (uuid: string): Promise<SkillDetail> => {
    const response = await api.get<SkillDetail>(`/api/v1/skills/${uuid}`);
    return response.data;
  },

  /** Create a new skill */
  create: async (data: SkillCreate): Promise<SkillDetail> => {
    const response = await api.post<SkillDetail>('/api/v1/skills', data);
    return response.data;
  },

  /** Update an existing skill */
  update: async (uuid: string, data: SkillUpdate): Promise<SkillDetail> => {
    const response = await api.put<SkillDetail>(`/api/v1/skills/${uuid}`, data);
    return response.data;
  },

  /** Toggle skill enabled/disabled status */
  toggle: async (uuid: string): Promise<{ enabled: boolean }> => {
    const response = await api.patch<{ enabled: boolean }>(`/api/v1/skills/${uuid}/toggle`);
    return response.data;
  },

  /** Delete a skill */
  delete: async (uuid: string): Promise<void> => {
    await api.delete(`/api/v1/skills/${uuid}`);
  },
};

/**
 * Schedules API methods
 */
export const schedulesAPI = {
  /** Trigger schedule computation for a project */
  createSchedule: async (projectUuid: string): Promise<ScheduleCreateResponse> => {
    const response = await api.post<ScheduleCreateResponse>(
      `/api/v1/schedules/project/${projectUuid}`
    );
    return response.data;
  },

  /** Get schedule history for a project (ordered by version descending) */
  getHistory: async (projectUuid: string): Promise<ScheduleHistory[]> => {
    const response = await api.get<ScheduleHistory[]>(
      `/api/v1/schedules/project/${projectUuid}/history`
    );
    return response.data;
  },

  /** Get enriched scheduled tasks for a project (latest or specified version) */
  getTasks: async (projectUuid: string, version?: number): Promise<ScheduledTaskEnriched[]> => {
    const params = version !== undefined ? { version } : {};
    const response = await api.get<ScheduledTaskEnriched[]>(
      `/api/v1/schedules/project/${projectUuid}/tasks`,
      { params }
    );
    return response.data;
  },
};

/**
 * Reports API methods
 */
export const reportsAPI = {
  /** Download PDF project report as Blob */
  downloadPDF: async (projectUuid: string, version?: number, timeScale?: string): Promise<Blob> => {
    const params: Record<string, string | number> = {};
    if (version !== undefined) params.version = version;
    if (timeScale) params.time_scale = timeScale;
    const response = await api.get(
      `/api/v1/reports/project/${projectUuid}/pdf`,
      { params, responseType: 'blob' }
    );
    return response.data;
  },
};

/**
 * FMEA API methods
 */
export const fmeaAPI = {
  /**
   * Download FMEA XLSX report as Blob
   * @param fmeaType - FMEA report type: "design", "process", "iso14971", or "general"
   * @returns Promise with the XLSX file as a Blob
   */
  downloadReport: async (fmeaType: string): Promise<Blob> => {
    const response = await api.get(
      `/api/v1/fmea/report/${fmeaType}`,
      { responseType: 'blob' }
    );
    return response.data;
  },
};

/**
 * Export the configured axios instance for custom requests
 */
export default api;
