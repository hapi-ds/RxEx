/**
 * API service layer for the FastAPI Neo4j Multi-Frontend System
 * Handles all HTTP requests to the backend with JWT authentication
 */

import axios, { type AxiosInstance } from 'axios';
import { config } from '../config';
import type { LoginCredentials, Token, PostCreate, PostUpdate, Post, Relationship } from '../types';
import type { Mind } from '../types/generated';

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
    const response = await api.post<Relationship>('/api/v1/relationships', data);
    return response.data;
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
 * Export the configured axios instance for custom requests
 */
export default api;
