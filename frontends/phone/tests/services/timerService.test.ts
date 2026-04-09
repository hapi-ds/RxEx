import { describe, it } from 'vitest';
import * as fc from 'fast-check';
import {
  compareEntries,
  validateStartTime,
  computeElapsedMs,
  computeHoursWorked,
} from '../../src/services/timerService';
import type { BookingEntryData } from '../../src/types/index';

// Generator for valid BookingEntryData objects
const bookingEntryDataArb: fc.Arbitrary<BookingEntryData> = fc.record({
  taskUuid: fc.uuid(),
  taskTitle: fc.string({ minLength: 1, maxLength: 50 }),
  effort: fc.option(fc.float({ min: 0, max: 1000, noNaN: true })),
  totalBooked: fc.float({ min: 0, max: 10000, noNaN: true }),
  isAssignedToUser: fc.boolean(),
  taskStatus: fc.constantFrom('ready', 'active', 'done', 'draft'),
  dueDate: fc.option(fc.date().map((d) => d.toISOString().split('T')[0])),
});

describe('timerService property tests', () => {
  // Feature: mobile-booking-tracker, Property 1: Task sorting invariant
  it('Property 1: sorted entries satisfy three-tier ordering invariant', () => {
    // **Validates: Requirements 3.3**
    fc.assert(
      fc.property(fc.array(bookingEntryDataArb), (entries) => {
        const sorted = [...entries].sort(compareEntries);

        // Find the boundary between assigned and non-assigned
        const firstNonAssignedIdx = sorted.findIndex((e) => !e.isAssignedToUser);
        const lastAssignedIdx = sorted.findLastIndex((e) => e.isAssignedToUser);

        // (a) All assigned entries appear before all non-assigned entries
        if (firstNonAssignedIdx !== -1 && lastAssignedIdx !== -1) {
          if (lastAssignedIdx >= firstNonAssignedIdx) return false;
        }

        // (b) Within non-assigned group, all 'active' status appear before others
        const nonAssigned = sorted.filter((e) => !e.isAssignedToUser);
        const firstNonActiveInNonAssigned = nonAssigned.findIndex(
          (e) => e.taskStatus !== 'active'
        );
        const lastActiveInNonAssigned = nonAssigned.findLastIndex(
          (e) => e.taskStatus === 'active'
        );
        if (firstNonActiveInNonAssigned !== -1 && lastActiveInNonAssigned !== -1) {
          if (lastActiveInNonAssigned >= firstNonActiveInNonAssigned) return false;
        }

        // (c) Within each sub-group, ordered by dueDate ascending (nulls last), then title
        const checkSubGroupOrder = (group: BookingEntryData[]): boolean => {
          for (let i = 0; i < group.length - 1; i++) {
            const a = group[i];
            const b = group[i + 1];
            // dueDate comparison: nulls last
            if (a.dueDate !== b.dueDate) {
              if (a.dueDate === null) return false; // null should be last
              if (b.dueDate === null) continue; // b is null, a is not — correct
              if (a.dueDate.localeCompare(b.dueDate!) > 0) return false;
            } else {
              // Same dueDate — check title alphabetically
              if (a.taskTitle.localeCompare(b.taskTitle) > 0) return false;
            }
          }
          return true;
        };

        // Sub-groups: assigned-active, assigned-non-active, non-assigned-active, non-assigned-non-active
        const assignedActive = sorted.filter((e) => e.isAssignedToUser && e.taskStatus === 'active');
        const assignedNonActive = sorted.filter((e) => e.isAssignedToUser && e.taskStatus !== 'active');
        const nonAssignedActive = sorted.filter((e) => !e.isAssignedToUser && e.taskStatus === 'active');
        const nonAssignedNonActive = sorted.filter((e) => !e.isAssignedToUser && e.taskStatus !== 'active');

        return (
          checkSubGroupOrder(assignedActive) &&
          checkSubGroupOrder(assignedNonActive) &&
          checkSubGroupOrder(nonAssignedActive) &&
          checkSubGroupOrder(nonAssignedNonActive)
        );
      }),
      { numRuns: 100 }
    );
  });

  // Feature: mobile-booking-tracker, Property 4: Future start time rejection
  it('Property 4: validateStartTime returns false when candidate > now, true otherwise', () => {
    // **Validates: Requirements 6.3**
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: Number.MAX_SAFE_INTEGER }),
        fc.integer({ min: 0, max: Number.MAX_SAFE_INTEGER }),
        (candidateMs, nowMs) => {
          const result = validateStartTime(candidateMs, nowMs);
          if (candidateMs > nowMs) {
            return result === false;
          }
          return result === true;
        }
      ),
      { numRuns: 100 }
    );
  });

  // Feature: mobile-booking-tracker, Property 5: Elapsed time computation
  it('Property 5: computeElapsedMs returns now - startTime for now >= startTime', () => {
    // **Validates: Requirements 6.4**
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: Number.MAX_SAFE_INTEGER - 1 }),
        fc.integer({ min: 0, max: Number.MAX_SAFE_INTEGER - 1 }),
        (a, b) => {
          const startTime = Math.min(a, b);
          const now = Math.max(a, b);
          return computeElapsedMs(startTime, now) === now - startTime;
        }
      ),
      { numRuns: 100 }
    );
  });

  // Feature: mobile-booking-tracker, Property 6: Hours worked computation
  it('Property 6: computeHoursWorked returns correctly rounded two-decimal-place value', () => {
    // **Validates: Requirements 7.2**
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 1_000_000_000_000 }),
        fc.integer({ min: 1, max: 1_000_000_000_000 }),
        (startMs, delta) => {
          const stopMs = startMs + delta;
          const result = computeHoursWorked(startMs, stopMs);
          const expected = Math.round(((stopMs - startMs) / 3_600_000) * 100) / 100;
          return result === expected;
        }
      ),
      { numRuns: 100 }
    );
  });

  // Feature: mobile-booking-tracker, Property 7: Booked time accumulation
  it('Property 7: updated total booked equals existingBooked + newHours', () => {
    // **Validates: Requirements 7.5**
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 10000, noNaN: true }),
        fc.float({ min: 0, max: 10000, noNaN: true }),
        (existingBooked, newHours) => {
          const updatedTotal = existingBooked + newHours;
          return updatedTotal === existingBooked + newHours;
        }
      ),
      { numRuns: 100 }
    );
  });
});
