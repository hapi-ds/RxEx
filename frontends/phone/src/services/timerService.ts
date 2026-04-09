import type { BookingEntryData } from '../types/index';

/**
 * Returns the elapsed milliseconds between startTime and now.
 */
export function computeElapsedMs(startTime: number, now: number): number {
  return now - startTime;
}

/**
 * Returns hours worked between two timestamps, rounded to two decimal places.
 */
export function computeHoursWorked(startMs: number, stopMs: number): number {
  return Math.round(((stopMs - startMs) / 3_600_000) * 100) / 100;
}

/**
 * Formats milliseconds as "HH:MM:SS". Negative or zero ms returns "00:00:00".
 */
export function formatElapsed(ms: number): string {
  if (ms <= 0) return '00:00:00';

  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const hh = String(hours).padStart(2, '0');
  const mm = String(minutes).padStart(2, '0');
  const ss = String(seconds).padStart(2, '0');

  return `${hh}:${mm}:${ss}`;
}

/**
 * Returns true if candidateMs is not in the future relative to nowMs.
 */
export function validateStartTime(candidateMs: number, nowMs: number): boolean {
  return candidateMs <= nowMs;
}

/**
 * Three-tier sort comparator for BookingEntryData:
 * 1. isAssignedToUser === true sorts first
 * 2. Among non-assigned, taskStatus === 'active' sorts before others
 * 3. dueDate ascending (nulls last), then taskTitle alphabetically
 */
export function compareEntries(a: BookingEntryData, b: BookingEntryData): number {
  if (a.isAssignedToUser !== b.isAssignedToUser) {
    return a.isAssignedToUser ? -1 : 1;
  }
  if (a.taskStatus !== b.taskStatus) {
    if (a.taskStatus === 'active') return -1;
    if (b.taskStatus === 'active') return 1;
  }
  if (a.dueDate !== b.dueDate) {
    if (a.dueDate === null) return 1;
    if (b.dueDate === null) return -1;
    return a.dueDate.localeCompare(b.dueDate);
  }
  return a.taskTitle.localeCompare(b.taskTitle);
}
