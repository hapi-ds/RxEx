import { useState, useCallback, useEffect } from 'react';
import type { ActiveBooking } from '../types/index';
import { validateStartTime } from '../services/timerService';

const STORAGE_KEY = 'activeBookings';

/** Read persisted bookings from localStorage into a Map. */
function loadFromStorage(): Map<string, ActiveBooking> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return new Map();
    const arr: ActiveBooking[] = JSON.parse(raw);
    if (!Array.isArray(arr)) return new Map();
    return new Map(arr.map((b) => [b.taskUuid, b]));
  } catch {
    return new Map();
  }
}

/** Persist a Map of active bookings to localStorage as a JSON array. */
function saveToStorage(map: Map<string, ActiveBooking>): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(map.values())));
}

export interface UseActiveBookingsReturn {
  activeBookings: Map<string, ActiveBooking>;
  startBooking: (taskUuid: string, taskTitle: string) => void;
  stopBooking: (taskUuid: string) => ActiveBooking | null;
  editStartTime: (taskUuid: string, newStartMs: number) => boolean;
  editStopTime: (taskUuid: string, newStopMs: number) => void;
  clearBooking: (taskUuid: string) => void;
}

export function useActiveBookings(): UseActiveBookingsReturn {
  const [activeBookings, setActiveBookings] = useState<Map<string, ActiveBooking>>(() => loadFromStorage());

  // Restore from localStorage on mount
  useEffect(() => {
    setActiveBookings(loadFromStorage());
  }, []);

  const startBooking = useCallback((taskUuid: string, taskTitle: string): void => {
    setActiveBookings((prev) => {
      const next = new Map(prev);
      next.set(taskUuid, {
        taskUuid,
        taskTitle,
        startTime: Date.now(),
        manualStopTime: null,
      });
      saveToStorage(next);
      return next;
    });
  }, []);

  const stopBooking = useCallback((taskUuid: string): ActiveBooking | null => {
    // Read the booking from the current state synchronously before updating.
    // We can't rely on the setActiveBookings updater to set a closure variable
    // because React batches state updates and the updater may run asynchronously.
    const current = activeBookings.get(taskUuid);
    if (!current) return null;

    const stopped = { ...current };

    setActiveBookings((prev) => {
      const next = new Map(prev);
      next.delete(taskUuid);
      saveToStorage(next);
      return next;
    });

    return stopped;
  }, [activeBookings]);

  const editStartTime = useCallback((taskUuid: string, newStartMs: number): boolean => {
    const nowMs = Date.now();
    if (!validateStartTime(newStartMs, nowMs)) return false;

    let success = false;
    setActiveBookings((prev) => {
      const booking = prev.get(taskUuid);
      if (!booking) return prev;
      success = true;
      const next = new Map(prev);
      next.set(taskUuid, { ...booking, startTime: newStartMs });
      saveToStorage(next);
      return next;
    });
    return success;
  }, []);

  const editStopTime = useCallback((taskUuid: string, newStopMs: number): void => {
    setActiveBookings((prev) => {
      const booking = prev.get(taskUuid);
      if (!booking) return prev;
      const next = new Map(prev);
      next.set(taskUuid, { ...booking, manualStopTime: newStopMs });
      saveToStorage(next);
      return next;
    });
  }, []);

  const clearBooking = useCallback((taskUuid: string): void => {
    setActiveBookings((prev) => {
      if (!prev.has(taskUuid)) return prev;
      const next = new Map(prev);
      next.delete(taskUuid);
      saveToStorage(next);
      return next;
    });
  }, []);

  return {
    activeBookings,
    startBooking,
    stopBooking,
    editStartTime,
    editStopTime,
    clearBooking,
  };
}
