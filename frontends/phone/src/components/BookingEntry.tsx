import { useState, useEffect, useCallback } from 'react';
import type { BookingEntryData, ActiveBooking } from '../types/index';
import { formatElapsed, computeElapsedMs } from '../services/timerService';
import styles from './BookingEntry.module.css';

interface BookingEntryProps {
  entry: BookingEntryData;
  isActive: boolean;
  activeBooking?: ActiveBooking;
  onStart: (taskUuid: string) => void;
  onStop: (taskUuid: string) => void;
  onEditStartTime?: (taskUuid: string, newStartMs: number) => void;
  onEditStopTime?: (taskUuid: string, newStopMs: number) => void;
}

export function BookingEntry({
  entry,
  isActive,
  activeBooking,
  onStart,
  onStop,
  onEditStartTime,
  onEditStopTime,
}: BookingEntryProps): React.JSX.Element {
  const [elapsed, setElapsed] = useState('00:00:00');
  const [editingStop, setEditingStop] = useState(false);

  useEffect(() => {
    if (!isActive || !activeBooking) {
      setElapsed('00:00:00');
      return;
    }

    const tick = (): void => {
      const ms = computeElapsedMs(activeBooking.startTime, Date.now());
      setElapsed(formatElapsed(ms));
    };

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [isActive, activeBooking]);

  const handleToggle = useCallback((): void => {
    if (isActive) {
      onStop(entry.taskUuid);
    } else {
      onStart(entry.taskUuid);
    }
  }, [isActive, entry.taskUuid, onStart, onStop]);

  const handleStartTimeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      const value = e.target.value;
      if (!value || !onEditStartTime) return;
      const ms = new Date(value).getTime();
      if (!Number.isNaN(ms)) {
        onEditStartTime(entry.taskUuid, ms);
      }
    },
    [entry.taskUuid, onEditStartTime],
  );

  const handleStopTimeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      const value = e.target.value;
      if (!value || !onEditStopTime) return;
      const ms = new Date(value).getTime();
      if (!Number.isNaN(ms)) {
        onEditStopTime(entry.taskUuid, ms);
      }
    },
    [entry.taskUuid, onEditStopTime],
  );

  const formatStartTimeValue = (): string => {
    if (!isActive || !activeBooking) return '';
    const d = new Date(activeBooking.startTime);
    return toDatetimeLocalString(d);
  };

  const formatStopTimeValue = (): string => {
    if (!isActive || !activeBooking || !activeBooking.manualStopTime) return '';
    const d = new Date(activeBooking.manualStopTime);
    return toDatetimeLocalString(d);
  };

  return (
    <div className={styles.entry}>
      <div className={styles.topRow}>
        <span className={styles.taskTitle} data-testid="task-title">
          {entry.taskTitle}
        </span>
        <button
          data-testid="toggle-button"
          className={`${styles.toggleButton} ${isActive ? styles.stopButton : styles.startButton}`}
          onClick={handleToggle}
          type="button"
        >
          {isActive ? 'Stop' : 'Start'}
        </button>
      </div>

      <div className={styles.bottomRow}>
        <span className={styles.field}>
          <span className={styles.fieldLabel}>Effort:</span>
          <span data-testid="effort">{entry.effort !== null ? entry.effort : '—'}</span>
        </span>

        <span className={styles.field}>
          <span className={styles.fieldLabel}>Booked:</span>
          <span data-testid="total-booked">{entry.totalBooked}h</span>
        </span>

        <span className={styles.field} data-testid="start-time">
          {isActive && activeBooking ? (
            <input
              type="datetime-local"
              className={styles.timeInput}
              value={formatStartTimeValue()}
              onChange={handleStartTimeChange}
              aria-label="Edit start time"
            />
          ) : (
            <span>—</span>
          )}
        </span>

        <span className={styles.field} data-testid="stop-time">
          {isActive && activeBooking ? (
            editingStop || activeBooking.manualStopTime ? (
              <input
                type="datetime-local"
                className={styles.timeInput}
                value={formatStopTimeValue()}
                onChange={handleStopTimeChange}
                onBlur={() => { if (!activeBooking.manualStopTime) setEditingStop(false); }}
                aria-label="Edit stop time"
                autoFocus={editingStop}
              />
            ) : (
              <span
                className={styles.tappableTime}
                onClick={() => setEditingStop(true)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter') setEditingStop(true); }}
              >
                {elapsed}
              </span>
            )
          ) : (
            <span>—</span>
          )}
        </span>
      </div>
    </div>
  );
}

/** Convert a Date to a string suitable for datetime-local input (YYYY-MM-DDTHH:MM) */
function toDatetimeLocalString(d: Date): string {
  const pad = (n: number): string => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
