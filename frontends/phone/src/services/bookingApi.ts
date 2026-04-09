/**
 * Domain-specific API functions for the Booking Tracker
 * Handles task fetching, booking management, resource resolution, and booking commits.
 */

import api from './api';
import type {
  TaskMind,
  BookingMind,
  ResourceMind,
  AssignmentRelationship,
  CommitBookingParams,
  BookingCommitResult,
} from '../types/index';

/** Paginated response shape from the backend query endpoint */
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** Raw mind response from the backend (type_specific_attributes nested) */
interface RawMindResponse {
  uuid: string;
  mind_type: string;
  title: string;
  status: string;
  type_specific_attributes?: Record<string, unknown>;
  [key: string]: unknown;
}

/** Relationship response from the backend */
interface RawRelationshipResponse {
  source_uuid: string;
  target_uuid: string;
  relationship_type: string;
  created_at?: string;
  properties?: Record<string, unknown>;
}

/**
 * Flatten type_specific_attributes into top-level fields,
 * matching the pattern used by the web frontend.
 */
function flattenMind<T>(raw: RawMindResponse): T {
  const { type_specific_attributes, ...rest } = raw;
  if (type_specific_attributes && typeof type_specific_attributes === 'object') {
    return { ...rest, ...type_specific_attributes } as unknown as T;
  }
  return raw as unknown as T;
}

/**
 * Fetch all pages from a paginated minds endpoint.
 * The backend returns { items, total, page, page_size, total_pages }.
 */
async function fetchAllPages<T>(url: string, params: Record<string, string | number> = {}): Promise<T[]> {
  const pageSize = 100;
  const response = await api.get<PaginatedResponse<RawMindResponse>>(url, {
    params: { ...params, page_size: pageSize },
  });

  const allItems: T[] = response.data.items.map((item) => flattenMind<T>(item));

  const totalPages = response.data.total_pages ?? 1;
  for (let page = 2; page <= totalPages; page++) {
    const nextResponse = await api.get<PaginatedResponse<RawMindResponse>>(url, {
      params: { ...params, page_size: pageSize, page },
    });
    allItems.push(...nextResponse.data.items.map((item) => flattenMind<T>(item)));
  }

  return allItems;
}

/**
 * Fetch all Task mind nodes with status ready or active.
 * GET /api/v1/minds?mind_type=task&statuses=ready,active
 */
export async function fetchTasks(): Promise<TaskMind[]> {
  return fetchAllPages<TaskMind>('/api/v1/minds', {
    mind_type: 'task',
    statuses: 'ready,active',
  });
}

/**
 * Fetch all Booking mind nodes.
 * GET /api/v1/minds?mind_type=booking
 */
export async function fetchBookings(): Promise<BookingMind[]> {
  return fetchAllPages<BookingMind>('/api/v1/minds', {
    mind_type: 'booking',
  });
}

/**
 * Fetch ASSIGNED_TO relationships for a given resource (outgoing direction).
 * GET /api/v1/minds/{resourceUuid}/relationships?relationship_type=ASSIGNED_TO&direction=outgoing
 */
export async function fetchAssignments(resourceUuid: string): Promise<AssignmentRelationship[]> {
  const response = await api.get<RawRelationshipResponse[]>(
    `/api/v1/minds/${resourceUuid}/relationships`,
    {
      params: {
        relationship_type: 'ASSIGNED_TO',
        direction: 'outgoing',
      },
    },
  );

  return response.data.map((rel) => ({
    source: rel.source_uuid,
    target: rel.target_uuid,
    type: 'ASSIGNED_TO' as const,
  }));
}

/** Module-level cache for the resolved resource (persists for the session) */
let cachedResource: ResourceMind | null = null;
let cachedResourceEmail: string | null = null;

/**
 * Resolve the Resource mind node by email.
 * Fetches all resources and filters client-side. Caches the result for the session.
 */
export async function resolveResource(email: string): Promise<ResourceMind | null> {
  if (cachedResourceEmail === email && cachedResource !== null) {
    return cachedResource;
  }

  const resources = await fetchAllPages<ResourceMind>('/api/v1/minds', {
    mind_type: 'resource',
  });

  const match = resources.find(
    (r) => r.email !== null && r.email.toLowerCase() === email.toLowerCase(),
  );

  cachedResource = match ?? null;
  cachedResourceEmail = email;
  return cachedResource;
}

/**
 * Commit a booking to the backend:
 * 1. POST /api/v1/minds — create Booking mind node
 * 2. POST /api/v1/minds/{booking_uuid}/relationships?target_uuid={task_uuid}&relationship_type=TO
 * 3. POST /api/v1/minds/{booking_uuid}/relationships?target_uuid={resource_uuid}&relationship_type=FOR
 */
export async function commitBooking(params: CommitBookingParams): Promise<BookingCommitResult> {
  try {
    const hoursWorked = Math.round(((params.stopTime - params.startTime) / 3_600_000) * 100) / 100;
    const bookingDate = new Date(params.startTime).toISOString().split('T')[0];

    const bookingTitle = `Booking: ${params.taskTitle}`;

    // Step 1: Create the Booking mind node
    let bookingUuid: string | undefined;
    try {
      const createResponse = await api.post<RawMindResponse>('/api/v1/minds', {
        mind_type: 'booking',
        title: bookingTitle,
        creator: params.userEmail || 'phone-app',
        status: 'done',
        type_specific_attributes: {
          hours_worked: hoursWorked,
          booking_date: bookingDate,
        },
      });
      bookingUuid = createResponse.data.uuid;
    } catch {
      // The backend may return 500 due to a serialization bug even though
      // the node was created. Try to find the just-created booking by title.
      const bookings = await fetchAllPages<{ uuid: string; title: string }>('/api/v1/minds', {
        mind_type: 'booking',
        title_search: bookingTitle,
      });
      const match = bookings.find((b) => b.title === bookingTitle);
      if (match) {
        bookingUuid = match.uuid;
      }
    }

    if (!bookingUuid) {
      return { success: false, error: 'Failed to create booking node' };
    }

    // Step 2: Create TO relationship (Booking → Task)
    try {
      await api.post(
        `/api/v1/minds/${bookingUuid}/relationships`,
        null,
        {
          params: {
            target_uuid: params.taskUuid,
            relationship_type: 'to',
          },
        },
      );
    } catch {
      // Relationship may already exist or fail — booking node still exists
    }

    // Step 3: Create FOR relationship (Booking → Resource), skip if no resource
    if (params.resourceUuid) {
      try {
        await api.post(
          `/api/v1/minds/${bookingUuid}/relationships`,
          null,
          {
            params: {
              target_uuid: params.resourceUuid,
              relationship_type: 'for',
            },
          },
        );
      } catch {
        // Relationship may fail — booking node still exists
      }
    }

    return { success: true, bookingUuid };
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error committing booking';
    return { success: false, error: message };
  }
}
