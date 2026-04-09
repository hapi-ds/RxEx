import { useState, useEffect, useCallback } from 'react';
import type { ActiveBooking } from '../types/index';
import { formatElapsed, computeElapsedMs } from '../services/timerService';
import styles from './ActiveBookingHeader.module.css';

interface ActiveBookingHeaderProps {
  activeBookings: ActiveBooking[];
  onStop: (taskUuid: string) => void;
  onEditStartTime?: (taskUuid: string, newStartMs: number) => void;
  onEditStopTime?: (taskUuid: string, newStopMs: number) => void;
}

/** Convert a Date to a string suitable for datetime-local input (YYYY-MM-DDTHH:MM) */
function toDatetimeLocalString(d: Date): string {
  const pad = (n: number): string => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function ActiveBookingRow({
  booking,
  now,
  onStop,
  onEditStartTime,
  onEditStopTime,
}: {
  booking: ActiveBooking;
  now: number;
  onStop: (taskUuid: string) => void;
  onEditStartTime?: (taskUuid: string, newStartMs: number) => void;
  onEditStopTime?: (taskUuid: string, newStopMs: number) => void;
}): React.JSX.Element {
  const [editingStart, setEditingStart] = useState(false);
  const [editingStop, setEditingStop] = useState(false);

  const elapsed = computeElapsedMs(booking.startTime, now);

  const handleStartTimeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      const value = e.target.value;
      if (!value || !onEditStartTime) return;
      const ms = new Date(value).getTime();
      if (!Number.isNaN(ms)) {
        onEditStartTime(booking.taskUuid, ms);
      }
    },
    [booking.taskUuid, onEditStartTime],
  );

  const handleStopTimeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      const value = e.target.value;
      if (!value || !onEditStopTime) return;
      const ms = new Date(value).getTime();
      if (!Number.isNaN(ms)) {
        onEditStopTime(booking.taskUuid, ms);
        setEditingStop(false);
      }
    },
    [booking.taskUuid, onEditStopTime],
  );

  const startTimeValue = toDatetimeLocalString(new Date(booking.startTime));

  return (
    <div className={styles.row}>
      <div className={styles.info}>
        <span className={styles.title} data-testid="active-title">
          {booking.taskTitle}
        </span>
        <div className={styles.meta}>
          {editingStart ? (
            <input
              type="datetime-local"
              className={styles.timeInput}
              value={startTimeValue}
              onChange={handleStartTimeChange}
              onBlur={() => setEditingStart(false)}
              aria-label="Edit start time"
              autoFocus
              data-testid="active-start-time"
            />
          ) : (
            <span
              data-testid="active-start-time"
              className={styles.tappableTime}
              onClick={() => setEditingStart(true)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') setEditingStart(true); }}
            >
              {new Date(booking.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}

          {editingStop || booking.manualStopTime ? (
            <input
              type="datetime-local"
              className={styles.timeInput}
              value={booking.manualStopTime ? toDatetimeLocalString(new Date(booking.manualStopTime)) : ''}
              onChange={handleStopTimeChange}
              onBlur={() => { if (!booking.manualStopTime) setEditingStop(false); }}
              aria-label="Edit stop time"
              autoFocus={editingStop}
              data-testid="active-elapsed"
            />
          ) : (
            <span
              data-testid="active-elapsed"
              className={styles.tappableTime}
              onClick={() => setEditingStop(true)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') setEditingStop(true); }}
            >
              {formatElapsed(elapsed)}
            </span>
          )}
        </div>
      </div>
      <button
        data-testid="active-stop-button"
        className={styles.stopButton}
        onClick={() => onStop(booking.taskUuid)}
        type="button"
      >
        Stop
      </button>
    </div>
  );
}

export function ActiveBookingHeader({
  activeBookings,
  onStop,
  onEditStartTime,
  onEditStopTime,
}: ActiveBookingHeaderProps): React.JSX.Element {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (activeBookings.length === 0) return;

    const id = setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => clearInterval(id);
  }, [activeBookings.length]);

  const isEmpty = activeBookings.length === 0;

  return (
    <div
      className={`${styles.header} ${isEmpty ? styles.headerEmpty : styles.headerActive}`}
      data-testid="active-booking-header"
    >
      {activeBookings.map((booking) => (
        <ActiveBookingRow
          key={booking.taskUuid}
          booking={booking}
          now={now}
          onStop={onStop}
          onEditStartTime={onEditStartTime}
          onEditStopTime={onEditStopTime}
        />
      ))}
    </div>
  );
}
