# RxD3 — Mindmap-driven Requirements, Risk, and Project Management with Document-Grade Outputs

**RxD3** is a practical, "do-it-all-with-mindmaps" system for organizing and executing engineering work—covering **requirements**, **risk management**, **project management**, and mybe more in one coherent workflow.

### Meaning of the name

- **R**: *Requirements* management.
- **x**: The “multiplier” for *project execution* (planning, tracking, ..), *risk managment*, and others.
- **D**: *Documents*—the primary output. RxD3 is designed to generate **real, deliverable artifacts** (e.g., **PDF/DOCX/XLSX**) that can be reviewed, approved, signed, and archived—especially relevant for regulated industries (even when these features are somewhen implemented in RxDx - the goal is to "integrate" in other QM systemes - or to enable work with structure even in an unstructured world).
- **3**: The **third iteration**, incorporating the lessons learned from earlier attempts and focusing on operational usability.

### Core idea: Mindmaps as the single source of truth
RxD3 uses mindmaps as a structured interface to capture intent and relationships early, then progressively refines that structure into controlled engineering deliverables. The objective is to reduce friction between “thinking” and “documenting” by making the mindmap the primary model—while keeping outputs compatible with established quality and compliance workflows.

### Designed for regulated reality—without enterprise overhead
RxD3 targets **small companies, startups, and individual engineers** who need disciplined development practices without the cost and complexity of heavy enterprise tooling. It supports a “first step” into digital design control: start simple, stay structured, and still produce artifacts that auditors, customers, and internal stakeholders can accept.

### What RxD3 produces
RxD3 is optimized for generating consistent, traceable documentation sets such as:
- Requirements specifications and trace matrices
- Risk analyses and risk control documentation
- Project plans, milestone reports, action lists, and change logs
- Review-ready document packages for approval and release


## Highlights

- **Graph Database** — Neo4j for rich relationship modeling (Mind nodes, skills, posts)
- **Dual Frontends** — React 18 web app (:3000) + WebXR 3D interface (:3001)
- **AI Skills** — Teachable knowledge units with CRUD API and toggle support
- **Dashboard** — Central hub for Save/Read/Clear project data, skill management, graph editor access
- **Real-Time** — WebSocket messaging between all connected clients
- **Auth** — JWT-based authentication for REST and WebSocket
- **Schema Generation** — Data model-first approach with auto-generated Pydantic schemas
- **Docker** — Single `docker compose up` to run everything

## Quick Start

```bash
cp .env.example .env        # configure secrets
docker compose up            # start all services
```

| Service         | URL                        |
|-----------------|----------------------------|
| Web Frontend    | http://localhost:3000       |
| XR Frontend     | http://localhost:3001       |
| Backend API     | http://localhost:8080       |
| API Docs        | http://localhost:8080/docs  |
| Neo4j Browser   | http://localhost:7474       |

Default login: `test@example.com` / `password123`

## Project Layout

```
backend/          FastAPI service (src/ layout, uv managed)
frontends/web/    React + TypeScript + Vite
frontends/xr/     WebXR + React Three Fiber
scripts/          Helper scripts (setup, test, logs, backup/restore)
docs/             Full documentation
```

## Scripts

```bash
./scripts/test.sh                              # run all tests
./scripts/logs.sh [service]                    # view logs
cd backend && uv run python scripts/backup_users_skills.py   # backup users & skills
cd backend && uv run python scripts/restore_users_skills.py  # restore users & skills
./seed_data_complete_fixed.sh                  # seed sample data
```

## Documentation

See [`docs/`](docs/) for detailed docs:

- [Full README](docs/README_FULL.md) — architecture, API examples, dev workflows, security
- [UI Overview](docs/UI.md) — pages, screenshots, navigation
- [AI Features](docs/AI.md) — skill system, AI chat, provider configuration
- [PM Features](docs/PM.md) — Task scheduling, Gantt, Burn-Down, PDF Project Report, Bookings, Sprints

## Next/Planned

- Requirment Managment: Output of URS, Trace-Matrix, ...
- Risk Management: Output of a p/dFMEA in XLSX format
- Adapted skills to be (more) usefull

### Enhancements

- Project Managment: Booking app for phone, easy create relations (better sprint planning)

## Tech Stack

| Layer    | Tech                                          |
|----------|-----------------------------------------------|
| Backend  | Python 3.13, FastAPI, Neo4j, neontology, uv   |
| Web UI   | React 18, TypeScript, Vite, Axios             |
| XR UI    | React Three Fiber, @react-three/xr            |
| Infra    | Docker Compose, multi-stage builds            |
| Testing  | pytest, Hypothesis (PBT), React Testing Lib   |

## License

Apache 2.0 — see [LICENSE](LICENSE)
