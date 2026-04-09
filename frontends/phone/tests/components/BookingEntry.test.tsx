import { describe, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import fc from 'fast-check';
import { BookingEntry } from '../../src/components/BookingEntry';
import type { BookingEntryData } from '../../src/types/index';

// Feature: mobile-booking-tracker, Property 2: BookingEntry renders all required fields
// Validates: Requirements 3.4

const bookingEntryDataArb = fc.record({
  taskUuid: fc.uuid(),
  taskTitle: fc.string({ minLength: 1, maxLength: 50 }),
  effort: fc.option(fc.float({ min: 0, max: 1000, noNaN: true })),
  totalBooked: fc.float({ min: 0, max: 10000, noNaN: true }),
  isAssignedToUser: fc.boolean(),
  taskStatus: fc.constantFrom('ready', 'active', 'done', 'draft'),
  dueDate: fc.option(fc.date().map(d => d.toISOString().split('T')[0])),
});

describe('BookingEntry — Property 2: renders all required fields', () => {
  it('should render all 6 required DOM elements for any valid BookingEntryData', () => {
    fc.assert(
      fc.property(bookingEntryDataArb, (data) => {
        const entry: BookingEntryData = {
          taskUuid: data.taskUuid,
          taskTitle: data.taskTitle,
          effort: data.effort,
          totalBooked: data.totalBooked,
          isAssignedToUser: data.isAssignedToUser,
          taskStatus: data.taskStatus,
          dueDate: data.dueDate,
        };

        const onStart = vi.fn();
        const onStop = vi.fn();

        const { unmount } = render(
          <BookingEntry
            entry={entry}
            isActive={false}
            onStart={onStart}
            onStop={onStop}
          />
        );

        // 1. task-title contains taskTitle text
        const titleEl = screen.getByTestId('task-title');
        if (!titleEl.textContent?.includes(entry.taskTitle)) {
          unmount();
          return false;
        }

        // 2. effort contains effort value or "—" when null
        const effortEl = screen.getByTestId('effort');
        if (entry.effort !== null) {
          if (!effortEl.textContent?.includes(String(entry.effort))) {
            unmount();
            return false;
          }
        } else {
          if (!effortEl.textContent?.includes('—')) {
            unmount();
            return false;
          }
        }

        // 3. total-booked contains totalBooked value
        const bookedEl = screen.getByTestId('total-booked');
        if (!bookedEl.textContent?.includes(String(entry.totalBooked))) {
          unmount();
          return false;
        }

        // 4. toggle-button present and shows "Start" for idle mode
        const toggleBtn = screen.getByTestId('toggle-button');
        if (toggleBtn.textContent !== 'Start') {
          unmount();
          return false;
        }

        // 5. start-time present
        const startTimeEl = screen.getByTestId('start-time');
        if (!startTimeEl) {
          unmount();
          return false;
        }

        // 6. stop-time present
        const stopTimeEl = screen.getByTestId('stop-time');
        if (!stopTimeEl) {
          unmount();
          return false;
        }

        unmount();
        return true;
      }),
      { numRuns: 100 },
    );
  });
});
