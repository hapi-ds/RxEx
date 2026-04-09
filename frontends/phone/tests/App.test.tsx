import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '../src/contexts/AuthContext';
import { LoginPage } from '../src/components/LoginPage';

/**
 * We test the routing logic in isolation rather than rendering the full App
 * (which includes BrowserRouter and BookingTracker with API calls).
 * This mirrors the App's ProtectedRoute + routing structure.
 */

function ProtectedRoute({ children }: { children: React.ReactNode }): React.JSX.Element {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function TestApp({ initialRoute = '/' }: { initialRoute?: string }): React.JSX.Element {
  return (
    <AuthProvider>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div data-testid="protected-content">Protected</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

describe('App routing', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('redirects to login when not authenticated', () => {
    render(<TestApp initialRoute="/" />);
    expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('renders login page at /login', () => {
    render(<TestApp initialRoute="/login" />);
    expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
  });

  it('renders protected content when authenticated', () => {
    localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.sig');
    render(<TestApp initialRoute="/" />);
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });
});
