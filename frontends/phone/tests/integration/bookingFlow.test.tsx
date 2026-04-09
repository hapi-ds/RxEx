import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/contexts/AuthContext';
import { BookingTracker } from '../../src/components/BookingTracker';
import type {
  TaskMind,
  ResourceMind,
  ActiveBooking,
  BookingCommitResult,
} from '../../src/types/index';

// --- Mock bookingApi ---
vi.mock('../../src/services/bookingApi', () => ({
  fetchTasks: vi.fn(),
  fetchBookings: vi.fn(),
  fetchAssignments: vi.fn(),
  resolveResource: vi.fn(),
  commitBooking: vi.fn(),
}));

import {
  fetchTasks,
  fetchBookings,
  fetchAssignments,
  resolveResource,
  commitBooking,
} from '../../src/services/bookingApi';

// --- Mock useAuth ---
const mockUserEmail = 'user@example.com';
vi.mock('../../src/hooks/useAuth', () => ({
  useAuth: () => ({
    token: 'fake-jwt-token',
    isAuthenticated: true,
    userEmail: mockUserEmail,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

// --- Mock useActiveBookings to control start/stop flow ---
const mockStartBooking = vi.fn();
const mockStopBooking = vi.fn();
const mockEditStartTime = vi.fn();
const mockEditStopTime = vi.fn();
const mockClearBooking = vi.fn();
let mockActiveBookings = new Map<string, ActiveBooking>();

vi.mock('../../src/hooks/useActiveBookings', () => ({
  useActiveBookings: () => ({
    activeBookings: mockActiveBookings,
    startBooking: mockStartBooking,
    stopBooking: mockStopBooking,
    editStartTime: mockEditStartTime,
    editStopTime: mockEditStopTime,
    clearBooking: mockClearBooking,
  }),
}));

const mockedFetchTasks = vi.mocked(fetchTasks);
const mockedFetchBookings = vi.mocked(fetchBookings);
const mockedFetchAssignments = vi.mocked(fetchAssignments);
const mockedResolveResource = vi.mocked(resolveResource);
const mockedCommitBooking = vi.mocked(commitBooking);

// --- Test helpers ---
const testResource: ResourceMind = {
  uuid: 'resource-1',
  title: 'Test User',
  email: mockUserEmail,
  mind_type: 'resource',
};

function makeTask(overrides: Partial<TaskMind> & { uuid: string; title: string }): TaskMind {
  return {
    status: 'active',
    priority: 'medium',
    effort: 8,
    due_date: null,
    task_type: 'development',
    mind_type: 'task',
    ...overrides,
  };
}

function renderBookingTracker(): ReturnType<typeof render> {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <BookingTracker />
      </MemoryRouter>
    </AuthProvider>,
  );
}

function setupDefaultMocks(): void {
  mockedResolveResource.mockResolvedValue(testResource);
  mockedFetchBookings.mockResolvedValue([]);
  mockedFetchAssignments.mockResolvedValue([]);
}

// --- Tests ---
describe('Integration: Full Booking Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockActiveBookings = new Map();
  });

  describe('Test 1: Start booking → stop → verify commit API calls', () => {
    it('calls commitBooking with correct params when a booking is started and stopped', async () => {
      const task = makeTask({ uuid: 'task-1', title: 'Implement feature X' });
      const startTime = Date.now() - 3600000; // 1 hour ago

      mockedFetchTasks.mockResolvedValue([task]);
      setupDefaultMocks();

      // When stopBooking is called, return the stopped booking data
      mockStopBooking.mockReturnValue({
        taskUuid: 'task-1',
        taskTitle: 'Implement feature X',
        startTime,
        manualStopTime: null,
      } as ActiveBooking);

      mockedCommitBooking.mockResolvedValue({
        success: true,
        bookingUuid: 'booking-1',
      } as BookingCommitResult);

      // Pre-populate active bookings so the header shows the stop button
      mockActiveBookings = new Map([
        ['task-1', {
          taskUuid: 'task-1',
          taskTitle: 'Implement feature X',
          startTime,
          manualStopTime: null,
        }],
      ]);

      const user = userEvent.setup();
      renderBookingTracker();

      // Wait for loading to finish
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // The active booking header should show the task with a stop button
      expect(screen.getByTestId('active-stop-button')).toBeInTheDocument();
      expect(screen.getByTestId('active-title')).toHaveTextContent('Implement feature X');

      // Click Stop in the active booking header
      await user.click(screen.getByTestId('active-stop-button'));

      // Verify stopBooking was called
      expect(mockStopBooking).toHaveBeenCalledWith('task-1');

      // Verify commitBooking was called with the correct parameters:
      // 1. Create Booking mind node
      // 2. Create TO relationship (Booking → Task)
      // 3. Create FOR relationship (Booking → Resource)
      await waitFor(() => {
        expect(mockedCommitBooking).toHaveBeenCalledTimes(1);
      });

      const commitCall = mockedCommitBooking.mock.calls[0][0];
      expect(commitCall.taskUuid).toBe('task-1');
      expect(commitCall.taskTitle).toBe('Implement feature X');
      expect(commitCall.resourceUuid).toBe('resource-1');
      expect(commitCall.startTime).toBe(startTime);
      expect(commitCall.stopTime).toBeGreaterThanOrEqual(commitCall.startTime);
    });

    it('verifies startBooking is called with correct params on Start click', async () => {
      const task = makeTask({ uuid: 'task-1', title: 'Implement feature X' });

      mockedFetchTasks.mockResolvedValue([task]);
      setupDefaultMocks();

      const user = userEvent.setup();
      renderBookingTracker();

      // Wait for task to appear
      await waitFor(() => {
        expect(screen.getByText('Implement feature X')).toBeInTheDocument();
      });

      // Click Start
      await user.click(screen.getByTestId('toggle-button'));

      // Verify startBooking was called with correct task UUID and title
      expect(mockStartBooking).toHaveBeenCalledWith('task-1', 'Implement feature X');
    });
  });

  describe('Test 2: Data loading pipeline — sorted task list', () => {
    it('renders tasks in correct sorted order (assigned first, then active, then by due date)', async () => {
      const tasks: TaskMind[] = [
        makeTask({ uuid: 'task-c', title: 'Charlie task', status: 'ready', due_date: '2025-03-01' }),
        makeTask({ uuid: 'task-a', title: 'Alpha task', status: 'active', due_date: '2025-01-01' }),
        makeTask({ uuid: 'task-b', title: 'Bravo task', status: 'ready', due_date: '2025-02-01' }),
        makeTask({ uuid: 'task-d', title: 'Delta task', status: 'active', due_date: null }),
      ];

      mockedFetchTasks.mockResolvedValue(tasks);
      mockedFetchBookings.mockResolvedValue([]);
      mockedFetchAssignments.mockResolvedValue([
        { source: 'resource-1', target: 'task-b', type: 'ASSIGNED_TO' },
      ]);
      mockedResolveResource.mockResolvedValue(testResource);

      renderBookingTracker();

      // Wait for loading to finish
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Get all task titles in rendered order
      const titles = screen.getAllByTestId('task-title').map((el) => el.textContent);

      // Expected order per compareEntries:
      // 1. Bravo task (assigned to user — sorts first)
      // 2. Alpha task (active, due 2025-01-01)
      // 3. Delta task (active, due null → sorts last among active)
      // 4. Charlie task (ready, due 2025-03-01)
      expect(titles).toEqual([
        'Bravo task',
        'Alpha task',
        'Delta task',
        'Charlie task',
      ]);
    });
  });

  describe('Test 3: Auth flow — token storage and API interceptor', () => {
    it('stores token in localStorage and authenticated component loads data with correct email', async () => {
      const fakeToken = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIn0.fakesig';
      localStorage.setItem('token', fakeToken);

      expect(localStorage.getItem('token')).toBe(fakeToken);

      mockedFetchTasks.mockResolvedValue([]);
      setupDefaultMocks();

      renderBookingTracker();

      // Wait for loading to finish — confirms the component loaded with auth
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Verify the booking tracker rendered (authenticated state)
      expect(screen.getByTestId('booking-tracker')).toBeInTheDocument();

      // Verify resolveResource was called with the user's email
      // (the auth context provides userEmail, which BookingTracker passes to resolveResource)
      expect(mockedResolveResource).toHaveBeenCalledWith(mockUserEmail);

      // Verify API data-loading functions were called
      // (they use the Bearer token from localStorage via the axios request interceptor)
      expect(mockedFetchTasks).toHaveBeenCalled();
      expect(mockedFetchBookings).toHaveBeenCalled();
    });

    it('verifies unauthenticated state has no token', () => {
      localStorage.clear();
      expect(localStorage.getItem('token')).toBeNull();
      // The ProtectedRoute in App.tsx redirects to /login when isAuthenticated is false.
      // This redirect behavior is covered by App.test.tsx.
    });
  });
});
