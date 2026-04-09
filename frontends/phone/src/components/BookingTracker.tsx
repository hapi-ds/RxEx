import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useActiveBookings } from '../hooks/useActiveBookings';
import {
  fetchTasks,
  fetchBookings,
  fetchAssignments,
  resolveResource,
  commitBooking,
} from '../services/bookingApi';
import { compareEntries, computeHoursWorked } from '../services/timerService';
import { ActiveBookingHeader } from './ActiveBookingHeader';
import { TaskList } from './TaskList';
import type { TaskMind, BookingEntryData } from '../types/index';
import styles from './BookingTracker.module.css';

export function BookingTracker(): React.JSX.Element {
  const { userEmail } = useAuth();

  const {
    activeBookings,
    startBooking,
    stopBooking,
    editStartTime,
    editStopTime,
    clearBooking,
  } = useActiveBookings();

  const [tasks, setTasks] = useState<TaskMind[]>([]);
  const [assignedTaskUuids, setAssignedTaskUuids] = useState<Set<string>>(new Set());
  const [bookedByTask, setBookedByTask] = useState<Map<string, number>>(new Map());
  const [resourceUuid, setResourceUuid] = useState<string | null>(null);
  const [noResource, setNoResource] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [commitError, setCommitError] = useState<{
    taskUuid: string;
    message: string;
  } | null>(null);

  // --- Data loading on mount ---
  const loadData = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      // Resolve resource first — we need the UUID for assignments
      let resUuid: string | null = null;
      if (userEmail) {
        const resource = await resolveResource(userEmail);
        if (resource) {
          resUuid = resource.uuid;
          setResourceUuid(resUuid);
          setNoResource(false);
        } else {
          setNoResource(true);
        }
      }

      // Fetch tasks, bookings, and assignments in parallel
      const [fetchedTasks, fetchedBookings, assignments] = await Promise.all([
        fetchTasks(),
        fetchBookings().catch(() => []),
        resUuid
          ? fetchAssignments(resUuid).catch(() => [])
          : Promise.resolve([]),
      ]);

      setTasks(fetchedTasks);

      // Build assigned-task set
      const assigned = new Set<string>(assignments.map((a) => a.target));
      setAssignedTaskUuids(assigned);

      // Build booked-by-task map
      // TODO: Mapping bookings to tasks requires relationship data (Booking→Task TO).
      // A bulk endpoint or client-side relationship resolution is needed.
      // For now, totalBooked is set to 0 for all tasks.
      const booked = new Map<string, number>();
      for (const _task of fetchedTasks) {
        booked.set(_task.uuid, 0);
      }
      // We still store fetchedBookings count for future use
      void fetchedBookings;
      setBookedByTask(booked);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to load data';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [userEmail]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // --- Compute sorted entries ---
  const entries: BookingEntryData[] = tasks
    .map((task) => ({
      taskUuid: task.uuid,
      taskTitle: task.title,
      effort: task.effort,
      totalBooked: bookedByTask.get(task.uuid) ?? 0,
      isAssignedToUser: assignedTaskUuids.has(task.uuid),
      taskStatus: task.status,
      dueDate: task.due_date,
    }))
    .sort(compareEntries);

  // --- Handlers ---
  const handleStart = useCallback(
    (taskUuid: string): void => {
      const task = tasks.find((t) => t.uuid === taskUuid);
      if (!task) return;
      startBooking(taskUuid, task.title);
    },
    [tasks, startBooking],
  );

  const handleStop = useCallback(
    async (taskUuid: string): Promise<void> => {
      const booking = stopBooking(taskUuid);
      if (!booking) return;

      const stopTime = booking.manualStopTime ?? Date.now();
      const result = await commitBooking({
        taskUuid,
        taskTitle: booking.taskTitle,
        resourceUuid: resourceUuid ?? '',
        userEmail: userEmail ?? '',
        startTime: booking.startTime,
        stopTime,
      });

      if (result.success) {
        clearBooking(taskUuid);
        const hours = computeHoursWorked(booking.startTime, stopTime);
        setBookedByTask((prev) => {
          const next = new Map(prev);
          next.set(taskUuid, (next.get(taskUuid) ?? 0) + hours);
          return next;
        });
      } else {
        setCommitError({
          taskUuid,
          message: result.error ?? 'Failed to save booking',
        });
      }
    },
    [stopBooking, resourceUuid, userEmail, clearBooking],
  );

  const handleRetryCommit = useCallback(async (): Promise<void> => {
    if (!commitError) return;
    // Clear the error and let the user try stopping again
    setCommitError(null);
  }, [commitError]);

  // --- Active bookings as array for the header ---
  const activeBookingsList = Array.from(activeBookings.values());

  // --- Render ---
  if (loading) {
    return (
      <div className={styles.loadingContainer} data-testid="loading">
        <div className={styles.spinner} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorBanner} data-testid="error-banner">
        <span>{error}</span>
        <button
          className={styles.retryButton}
          onClick={() => void loadData()}
          type="button"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={styles.container} data-testid="booking-tracker">
      {noResource && (
        <div className={styles.noResourceBanner} data-testid="no-resource-banner">
          No Resource profile found for your account. Bookings will not be linked to a resource.
        </div>
      )}

      <ActiveBookingHeader
        activeBookings={activeBookingsList}
        onStop={(taskUuid) => void handleStop(taskUuid)}
        onEditStartTime={editStartTime}
        onEditStopTime={editStopTime}
      />

      <div className={styles.content}>
        <TaskList
          entries={entries}
          activeBookings={activeBookings}
          onStart={handleStart}
          onStop={(taskUuid) => void handleStop(taskUuid)}
          onEditStartTime={editStartTime}
          onEditStopTime={editStopTime}
          disabled={false}
        />
      </div>

      {commitError && (
        <div className={styles.commitToast} data-testid="commit-error-toast">
          <span>{commitError.message}</span>
          <button
            className={styles.commitToastRetry}
            onClick={() => void handleRetryCommit()}
            type="button"
          >
            Retry
          </button>
          <button
            className={styles.commitToastDismiss}
            onClick={() => setCommitError(null)}
            type="button"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
