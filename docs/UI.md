# UI Overview

The web frontend is a React 18 + TypeScript SPA served at `http://localhost:3000`.

## Pages

| Route            | Purpose                                              |
|------------------|------------------------------------------------------|
| `/login`         | Authentication (email + password)                    |
| `/dashboard`     | Central hub — Save/Read/Clear data, skills summary, quick links |
| `/skills`        | Manage AI skills (create, edit, toggle, delete)      |
| `/graph-editor`  | Interactive graph visualization of Mind nodes         |
| `/posts`         | List and manage posts                                |
| `/create`        | Create new posts                                     |
| `/edit`          | Edit existing posts                                  |
| `/chat`          | AI chat interface                                    |

## Screenshots

### Dashboard

The dashboard provides action cards for project data management (Save/Read/Clear), a skills overview with enabled count, and quick navigation to the graph editor. Others will come soon.

![Dashboard](pictures/Screenshot%20From%202026-03-15%2022-05-57.png)

### Graph Editor

The graph editor renders Mind nodes and their relationships as an interactive node graph. Nodes are color-coded by type and can be dragged, selected, and inspected.

![Graph Editor](pictures/Screenshot%20From%202026-03-15%2022-04-50.png)

## Navigation

All protected pages share a sidebar/nav layout. After login, the user lands on `/dashboard`. The JWT token is stored in `localStorage` and attached to every API request automatically.

## Fast Add Mode

Right-click any node to instantly create a new connected mind — no forms or modals needed. Pre-select mind type, relationship type, and direction in the filter panel, then right-click to build the graph rapidly. Left-click behavior (select/edit) is unchanged. A visual indicator on the canvas confirms the mode is active.

## Focus Mode

Shift-click any node to enter focus mode — the graph narrows to that node and its neighborhood. The proximity slider (0–10 hops) controls how far out the neighborhood extends. Combine with relationship type and direction filters to trace specific paths (e.g. only incoming LEAD_TO edges up to 5 hops). Shift-click the focused node again to exit. A badge at the top of the canvas shows the focused node's name.

## Collapsible Filter Panel

The filter panel collapses to a thin toggle strip, giving the graph canvas full width when filters aren't needed.

## Relationship & Direction Filters

Filter visible edges by relationship type (multi-select) and direction (incoming/outgoing/both) relative to the focused node. Proximity level supports up to 10 hops. Orphaned nodes are automatically hidden when direction or relationship type filters are active.

## Editable Relationship Properties

Selecting a relationship shows its properties in the attribute editor. All expected fields (e.g. Occurrence Probability, Detectability Probability for LEAD_TO; P1, P2 for CAN_OCCUR) are always visible — even when empty — and editable inline with a Save button.

## Click-to-Select in Relationship Editor

When creating a relationship, click "Pick from graph" next to the source or target field, then click a node on the canvas to populate it. Press Escape to cancel pick mode.
