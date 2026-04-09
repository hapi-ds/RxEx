/** Task mind node (subset of fields relevant to phone frontend) */
export interface TaskMind {
  uuid: string;
  title: string;
  status:
    | 'ready'
    | 'active'
    | 'done'
    | 'draft'
    | 'frozen'
    | 'accepted'
    | 'archived'
    | 'obsolet'
    | 'deleted';
  priority: 'low' | 'medium' | 'high' | 'critical';
  effort: number | null;
  due_date: string | null;
  task_type: string;
  mind_type: string;
}

/** Booking mind node */
export interface BookingMind {
  uuid: string;
  title: string;
  hours_worked: number;
  booking_date: string | null;
  status: string;
  mind_type: string;
}

/** Resource mind node */
export interface ResourceMind {
  uuid: string;
  title: string;
  email: string | null;
  mind_type: string;
}

/** Relationship from API — Resource assigned to Task */
export interface AssignmentRelationship {
  source: string;
  target: string;
  type: 'ASSIGNED_TO';
}

/** Booking-to-Task relationship */
export interface BookingToTaskRelationship {
  source: string;
  target: string;
  type: 'TO';
}

/** Active booking tracked in client state */
export interface ActiveBooking {
  taskUuid: string;
  taskTitle: string;
  startTime: number;
  manualStopTime: number | null;
}

/** Persisted to localStorage for offline resilience */
export interface PersistedActiveBookings {
  bookings: ActiveBooking[];
  resourceUuid: string;
}

/** Row data for the TaskList */
export interface BookingEntryData {
  taskUuid: string;
  taskTitle: string;
  effort: number | null;
  totalBooked: number;
  isAssignedToUser: boolean;
  taskStatus: string;
  dueDate: string | null;
}

/** Parameters for committing a booking to the backend */
export interface CommitBookingParams {
  taskUuid: string;
  taskTitle: string;
  resourceUuid: string;
  userEmail: string;
  startTime: number;
  stopTime: number;
}

/** Result of a booking commit */
export interface BookingCommitResult {
  success: boolean;
  bookingUuid?: string;
  error?: string;
}
