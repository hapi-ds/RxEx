# Project Management

The project management module provides CPM-based scheduling, Gantt chart visualization, agile sprint tracking, and PDF report generation. All project data lives in the Neo4j graph as Mind nodes connected by typed relationships.

## Pages

| Route                            | Purpose                                                        |
|----------------------------------|----------------------------------------------------------------|
| `/project-classic/:projectUuid`  | Classic view — Gantt chart, schedule history, PDF download     |
| `/project-agile/:projectUuid`    | Agile view — burn-down chart, sprint task lists, backlog       |

Both views include a project selector when no `projectUuid` is provided in the URL.

## Classic Project View

The Classic View renders a read-only SVG Gantt chart from persisted schedule data. It includes:

- Version selector to switch between schedule history versions
- Time scale selector (weeks / months / quarters / years)
- Hierarchy depth control to filter visible task levels
- "Run Scheduler" button to trigger CPM computation
- "Download Report" button to generate a PDF

Tasks are displayed as horizontal bars on a time axis. Critical path tasks are colored red, non-critical blue. Progress fill shows booked hours vs. planned effort. Dependency connectors are drawn as SVG paths between predecessor/successor bars.

![Classic Project View](pictures/Screenshot%20From%202026-03-16%2019-13-21.png)

## Agile Project View

The Agile View shows sprint-based task organization with a burn-down chart. It includes:

- Burn-down chart (SVG) plotting ideal vs. actual remaining effort
- Scope selector for project-level, individual sprint, or backlog burn-down
- Three task list sections: Backlog, Current Sprint, Next Sprint
- Each task shows title, status, priority, assigned resources, and effort
- Resource assignment resolves up the CONTAINS hierarchy when no direct ASSIGNED_TO exists

Sprints are Mind nodes linked to Tasks via CONTAINS relationships — no separate kanban data structure.

![Agile Project View](pictures/Screenshot%20From%202026-03-16%2019-11-48.png)

## PDF Report

Downloadable from the Classic View. Generated server-side using ReportLab. The report contains:

- Cover page with project title, schedule version, and generation timestamp
- Gantt chart table (task name, type, start/end dates, duration, critical flag, progress)
- Booking summary table (task, resource, hours, rate, cost) with totals
- Journal entries ordered by date (severity, title, description)




## Scheduling API

All endpoints are under `/api/v1/schedules`.

| Method | Endpoint                                          | Description                                      |
|--------|---------------------------------------------------|--------------------------------------------------|
| POST   | `/project/{project_uuid}`                         | Run CPM scheduler, create new schedule version   |
| GET    | `/project/{project_uuid}/history`                 | List schedule versions (ordered by version desc) |
| GET    | `/project/{project_uuid}/tasks?version={v}`       | Get enriched ScheduledTasks for a version        |
| GET    | `/project/{project_uuid}/tasks`                   | Get ScheduledTasks for the latest version        |
| GET    | `/project/{project_uuid}/critical-path?version={v}` | Get critical path tasks (zero slack)          |
| GET    | `/project/{project_uuid}/versions`                | List all available versions with metadata        |

The `/tasks` endpoint returns enriched data including the original Task title, task_type, hierarchy level, predecessor UUIDs, and progress (booked hours / effort ratio).

## Report API

| Method | Endpoint                                          | Description                                      |
|--------|---------------------------------------------------|--------------------------------------------------|
| GET    | `/api/v1/reports/project/{project_uuid}/pdf?version={v}` | Generate and download PDF report         |

Returns `application/pdf` with a `Content-Disposition` header. If no version is specified, uses the latest. Returns 400 if the project has no schedule history.

## Scheduler Service

The `SchedulerService` implements the Critical Path Method algorithm with these capabilities:

- **Recursive CONTAINS traversal** — discovers tasks nested under Phases and Work Packages at any depth
- **Cycle detection** — DFS-based check on the PREDATES dependency graph before scheduling
- **Forward/backward pass** — computes earliest and latest start/end dates for each task
- **Critical path identification** — marks tasks with zero slack as critical
- **Resource cost calculation** — uses ASSIGNED_TO relationships to compute `base_cost = duration × Σ(hourly_rate × effort_allocation)`
- **Version management** — auto-increments version numbers, creates HAS_SCHEDULED relationships from Project to ScheduleHistory
- **ScheduledTask creation** — persists one ScheduledTask per Task with SCHEDULED relationships carrying version and timestamp

Default duration for tasks without explicit effort: 1 business day. Business hours: 8:00–17:00, Monday–Friday.

## Graph Relationships

```
Project ──HAS_SCHEDULED──▶ ScheduleHistory
Project ──CONTAINS──▶ Phase ──CONTAINS──▶ WorkPackage ──CONTAINS──▶ Task
Task ──SCHEDULED──▶ ScheduledTask
Task ──PREDATES──▶ Task
Sprint ──CONTAINS──▶ Task
Resource ──ASSIGNED_TO──▶ Task
Booking ──TO──▶ Task
Booking ──FOR──▶ Resource
```

## Frontend Components

### Classic View (`components/project-classic/`)

| Component              | Purpose                                                    |
|------------------------|------------------------------------------------------------|
| `ClassicProjectView`   | Page component — fetches data, composes sub-components     |
| `GanttChart`           | SVG Gantt rendering (task bars, connectors, critical path) |
| `TaskListTable`        | Task list with hierarchy indentation                       |
| `ScheduleControls`     | Version, time scale, and depth selectors                   |

### Agile View (`components/project-agile/`)

| Component              | Purpose                                                    |
|------------------------|------------------------------------------------------------|
| `AgileProjectView`     | Page component — fetches sprints, tasks, bookings          |
| `BurnDownChart`        | SVG burn-down chart (ideal vs. actual effort lines)        |
| `SprintTaskList`       | Backlog / Current Sprint / Next Sprint task sections       |
