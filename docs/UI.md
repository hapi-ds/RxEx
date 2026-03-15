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
