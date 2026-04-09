import type { BookingEntryData, ActiveBooking } from '../types/index';
import { BookingEntry } from './BookingEntry';
import styles from './TaskList.module.css';

interface TaskListProps {
  entries: BookingEntryData[];
  activeBookings: Map<string, ActiveBooking>;
  onStart: (taskUuid: string) => void;
  onStop: (taskUuid: string) => void;
  onEditStartTime?: (taskUuid: string, newStartMs: number) => void;
  onEditStopTime?: (taskUuid: string, newStopMs: number) => void;
  disabled?: boolean;
}

export function TaskList({
  entries,
  activeBookings,
  onStart,
  onStop,
  onEditStartTime,
  onEditStopTime,
  disabled,
}: TaskListProps): React.JSX.Element {
  const visibleEntries = entries.filter(
    (entry) => !activeBookings.has(entry.taskUuid),
  );

  if (visibleEntries.length === 0) {
    return (
      <div className={styles.container}>
        <p className={styles.emptyState}>No tasks to display</p>
      </div>
    );
  }

  return (
    <div className={styles.container} data-testid="task-list">
      {visibleEntries.map((entry) => (
        <BookingEntry
          key={entry.taskUuid}
          entry={entry}
          isActive={false}
          onStart={disabled ? () => {} : onStart}
          onStop={onStop}
          onEditStartTime={onEditStartTime}
          onEditStopTime={onEditStopTime}
        />
      ))}
    </div>
  );
}
