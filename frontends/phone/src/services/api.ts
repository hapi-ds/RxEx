/**
 * API service layer for the Phone Frontend
 * Axios instance with JWT authentication interceptors
 */

import axios, { type AxiosInstance } from 'axios';
import { config } from '../config';

/** JWT token response from the login endpoint */
export interface Token {
  access_token: string;
  token_type: string;
}

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
  (reqConfig) => {
    const token = localStorage.getItem('token');
    if (token) {
      reqConfig.headers.Authorization = `Bearer ${token}`;
    }
    return reqConfig;
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
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post<Token>('/users/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
};

export default api;
