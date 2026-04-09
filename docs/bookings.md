# Mobile Booking Tracker

The phone frontend is a React 19 + TypeScript SPA served at `http://localhost:3002`, purpose-built for smartphone screens. It lets authenticated users (Resources) start/stop time-tracking against existing Tasks and commit the resulting Booking mind nodes to the backend.

## Architecture

The phone frontend follows the same patterns as the web (:3000) and XR (:3001) frontends: Vite, Axios with JWT interceptor, CSS modules, and Docker Compose integration. It communicates exclusively with the FastAPI backend over HTTP — no new backend endpoints were added, only CORS origins for `localhost:3002` and `phone:3002`.

```
┌──────────────────────────────────────────────────────────┐
│                  Docker Compose Network                   │
│                                                           │
│  ┌──────────┐      ┌──────────┐     ┌────────────────┐  │
│  │  Neo4j   │◄─────┤  FastAPI │◄────┤  Phone         │  │
│  │  :7687   │      │  :8080   │     │  Frontend      │  │
│  └──────────┘      └──────────┘     │  :3002         │  │
│                                      └────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Pages

| Route    | Purpose                                                    |
|----------|------------------------------------------------------------|
| `/login` | Email + password authentication (same JWT flow as web)     |
| `/`      | Booking Tracker — task list with inline time tracking      |

## How It Works

1. On login, the JWT token is stored in `localStorage` and the user's email is extracted from the `sub` claim.
2. The Booking Tracker page fetches tasks (status `ready` or `active`), existing bookings, and the user's ASSIGNED_TO relationships in parallel.
3. Tasks are sorted client-side: assigned-to-user first, then active status, then by due date (nulls last), then title alphabetically.
4. Tapping **Start** on a task records the current time and moves the entry into the fixed Active Booking Header at the top of the screen.
5. Multiple bookings can run simultaneously — each with its own independent timer.
6. Tapping **Stop** commits the booking to the backend as three API calls:
   - `POST /api/v1/minds` — creates a Booking mind node with `hours_worked`, `booking_date`, and status `done`
   - `POST /api/v1/minds/{booking}/relationships?target_uuid={task}&relationship_type=TO`
   - `POST /api/v1/minds/{booking}/relationships?target_uuid={resource}&relationship_type=FOR`
7. Active booking state is persisted to `localStorage`, so timers survive page refreshes.

## Key Components

| Component              | Responsibility                                                |
|------------------------|---------------------------------------------------------------|
| `BookingTracker`       | Page orchestrator — data fetching, sorting, start/stop/commit |
| `ActiveBookingHeader`  | Fixed header showing running bookings with stop buttons       |
| `TaskList`             | Scrollable sorted list of idle tasks                          |
| `BookingEntry`         | Single task row — title, effort, booked time, start/stop      |
| `LoginPage`            | Email/password form with error handling                       |

## Service Layer

| Module              | Responsibility                                              |
|---------------------|-------------------------------------------------------------|
| `services/api.ts`        | Axios instance with JWT request/response interceptors  |
| `services/bookingApi.ts` | Domain API: fetchTasks, fetchBookings, commitBooking, resolveResource |
| `services/timerService.ts` | Pure functions: elapsed time, hours worked, sorting comparator, time validation |

## Editable Time Fields

While a booking is active, the start and stop times are editable via datetime-local inputs. Editing the start time to a future value is rejected. Editing the stop time sets a manual override while the elapsed display continues from the edited start.

## Offline Resilience

Active bookings (task UUID, title, start time, manual stop time) are persisted to `localStorage` under the key `activeBookings`. On page load, any persisted bookings are restored and timers resume from the original start times. Entries are removed from storage only after a successful backend commit.

## Running Locally

```bash
# Via Docker Compose (recommended)
docker compose up

# Or standalone for development
cd frontends/phone
npm install
npm run dev
```

Access at `http://localhost:3002`.

## Tests

```bash
cd frontends/phone
npx vitest run
```

The test suite includes property-based tests (fast-check, 100 runs each) covering sorting invariants, time computation, persistence round-trips, and component rendering contracts, plus unit and integration tests for auth, components, and the full booking commit flow.

## Mobile Design

- Viewport range: 320px–480px
- All interactive elements have 44×44px minimum touch targets
- Fixed Active Booking Header with smooth collapse when empty
- Touch-based scrolling, no horizontal overflow
- CSS modules for all component styling
