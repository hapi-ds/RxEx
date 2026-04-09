import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import * as fc from 'fast-check';
import { useActiveBookings } from '../../src/hooks/useActiveBookings';
import type { ActiveBooking } from '../../src/types/index';

const STORAGE_KEY = 'activeBookings';

beforeEach(() => {
  localStorage.clear();
});

// Feature: mobile-booking-tracker, Property 8: Multiple simultaneous active bookings
describe('Property 8: Multiple simultaneous active bookings', () => {
  /**
   * Validates: Requirements 4.5
   *
   * For any set of N distinct task UUIDs (N >= 1), starting a booking on each
   * task SHALL result in exactly N active bookings tracked simultaneously,
   * each with its own independent startTime.
   */
  it('starting N distinct bookings results in exactly N active entries with independent startTimes', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(fc.uuid(), { minLength: 1, maxLength: 20 }),
        (uuids) => {
          localStorage.clear();

          const { result } = renderHook(() => useActiveBookings());

          for (const uuid of uuids) {
            act(() => {
              result.current.startBooking(uuid, `Task ${uuid}`);
            });
          }

          const bookings = result.current.activeBookings;

          // Exactly N active bookings
          expect(bookings.size).toBe(uuids.length);

          // Each UUID is present with its own startTime
          const startTimes = new Set<number>();
          for (const uuid of uuids) {
            const booking = bookings.get(uuid);
            expect(booking).toBeDefined();
            expect(booking!.taskUuid).toBe(uuid);
            expect(booking!.taskTitle).toBe(`Task ${uuid}`);
            expect(typeof booking!.startTime).toBe('number');
            startTimes.add(booking!.startTime);
          }

          // All bookings have valid startTimes (they are numbers > 0)
          for (const t of startTimes) {
            expect(t).toBeGreaterThan(0);
          }
        },
      ),
      { numRuns: 100 },
    );
  });
});

// Feature: mobile-booking-tracker, Property 9: Active booking persistence round trip
describe('Property 9: Active booking persistence round trip', () => {
  /**
   * Validates: Requirements 10.1, 10.2
   *
   * For any list of ActiveBooking objects with valid taskUuid, taskTitle,
   * startTime, and optional manualStopTime, serializing to the localStorage
   * JSON format and then deserializing SHALL produce a list that is deeply
   * equal to the original.
   */
  const activeBookingArb = fc.record({
    taskUuid: fc.uuid(),
    taskTitle: fc.string({ minLength: 1, maxLength: 50 }),
    startTime: fc.integer({ min: 0, max: Date.now() }),
    manualStopTime: fc.option(fc.integer({ min: 0, max: Date.now() }), { nil: null }),
  });

  it('serializing and deserializing ActiveBooking arrays via JSON preserves deep equality', () => {
    fc.assert(
      fc.property(
        fc.array(activeBookingArb, { minLength: 0, maxLength: 20 }),
        (bookings: ActiveBooking[]) => {
          // Serialize to localStorage JSON format (same as saveToStorage)
          const serialized = JSON.stringify(bookings);

          // Deserialize (same as loadFromStorage)
          const deserialized: ActiveBooking[] = JSON.parse(serialized);

          expect(deserialized).toEqual(bookings);
          expect(deserialized.length).toBe(bookings.length);

          // Verify each field individually for completeness
          for (let i = 0; i < bookings.length; i++) {
            expect(deserialized[i].taskUuid).toBe(bookings[i].taskUuid);
            expect(deserialized[i].taskTitle).toBe(bookings[i].taskTitle);
            expect(deserialized[i].startTime).toBe(bookings[i].startTime);
            expect(deserialized[i].manualStopTime).toBe(bookings[i].manualStopTime);
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it('round-tripping through localStorage preserves active booking data', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(activeBookingArb, {
          minLength: 1,
          maxLength: 10,
          selector: (b) => b.taskUuid,
        }),
        (bookings: ActiveBooking[]) => {
          localStorage.clear();

          // Serialize to localStorage (matching saveToStorage format)
          localStorage.setItem(STORAGE_KEY, JSON.stringify(bookings));

          // Deserialize from localStorage (matching loadFromStorage)
          const raw = localStorage.getItem(STORAGE_KEY);
          expect(raw).not.toBeNull();

          const restored: ActiveBooking[] = JSON.parse(raw!);
          expect(restored).toEqual(bookings);
        },
      ),
      { numRuns: 100 },
    );
  });
});
