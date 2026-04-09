/**
 * AuthContext
 * Provides authentication state and functions to the entire app.
 * Extends the web frontend pattern with userEmail extracted from JWT payload.
 */

import React, { createContext, useContext, useState, type ReactNode } from 'react';
import { authAPI } from '../services/api';

/**
 * Decode the payload section of a JWT token (base64url → JSON).
 */
function decodeJwtPayload(token: string): Record<string, unknown> {
  const payload = token.split('.')[1];
  return JSON.parse(atob(payload));
}

/**
 * Extract the email from a JWT token's payload.
 * The backend stores the email in the `email` claim (not `sub`).
 * Returns null if the token is malformed or the claim is missing.
 */
function extractEmailFromToken(token: string): string | null {
  try {
    const payload = decodeJwtPayload(token);
    if (typeof payload.email === 'string') return payload.email;
    if (typeof payload.sub === 'string') return payload.sub;
    return null;
  } catch {
    return null;
  }
}

export interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  userEmail: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }): React.JSX.Element {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => !!localStorage.getItem('token'));
  const [userEmail, setUserEmail] = useState<string | null>(() => {
    const stored = localStorage.getItem('token');
    return stored ? extractEmailFromToken(stored) : null;
  });

  const login = async (email: string, password: string): Promise<void> => {
    try {
      const response = await authAPI.login(email, password);
      const accessToken = response.access_token;

      localStorage.setItem('token', accessToken);
      setToken(accessToken);
      setIsAuthenticated(true);
      setUserEmail(extractEmailFromToken(accessToken));
    } catch (error) {
      localStorage.removeItem('token');
      setToken(null);
      setIsAuthenticated(false);
      setUserEmail(null);
      throw error;
    }
  };

  const logout = (): void => {
    localStorage.removeItem('token');
    setToken(null);
    setIsAuthenticated(false);
    setUserEmail(null);
  };

  return (
    <AuthContext.Provider value={{ token, isAuthenticated, userEmail, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
