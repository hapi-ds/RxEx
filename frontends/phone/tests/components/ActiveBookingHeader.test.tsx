import { describe, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import fc from 'fast-check';
import { ActiveBookingHeader } from '../../src/components/ActiveBookingHeader';

// Feature: mobile-booking-tracker, Property 3: ActiveBookingHeader renders all required fields per entry
// Validates: Requirements 5.2

const activeBookingArb = fc.record({
  taskUuid: fc.uuid(),
  taskTitle: fc.string({ minLength: 1, maxLength: 50 }),
  startTime: fc.integer({ min: 1000000000000, max: Date.now() }),
  manualStopTime: fc.constant(null),
});

describe('ActiveBookingHeader — Property 3: renders all required fields per entry', () => {
  it('should render title, start time, elapsed time, and stop button for each active booking', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(activeBookingArb, { minLength: 1, maxLength: 10, selector: (b) => b.taskUuid }),
        (bookings) => {
          const onStop = vi.fn();

          const { unmount } = render(
            <ActiveBookingHeader activeBookings={bookings} onStop={onStop} />,
          );

          const titles = screen.getAllByTestId('active-title');
          const startTimes = screen.getAllByTestId('active-start-time');
          const elapsedTimes = screen.getAllByTestId('active-elapsed');
          const stopButtons = screen.getAllByTestId('active-stop-button');

          const expected = bookings.length;

          if (titles.length !== expected) { unmount(); return false; }
          if (startTimes.length !== expected) { unmount(); return false; }
          if (elapsedTimes.length !== expected) { unmount(); return false; }
          if (stopButtons.length !== expected) { unmount(); return false; }

          unmount();
          return true;
        },
      ),
      { numRuns: 100 },
    );
  });
});
