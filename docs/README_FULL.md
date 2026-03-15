# FastAPI Neo4j Multi-Frontend System

A production-ready multi-frontend architecture featuring a FastAPI backend with Neo4j graph database, JWT authentication, WebSocket real-time communication, and dual frontends: a React web application and a WebXR immersive interface.

## Overview

This system provides a scalable foundation for building modern web applications with real-time collaboration features and immersive XR experiences. The architecture separates concerns cleanly between backend services and multiple frontend clients, enabling rapid development and easy deployment.

### Key Features

- **FastAPI Backend**: High-performance async REST API with automatic OpenAPI documentation
- **Neo4j Graph Database**: Powerful graph database for complex relationship modeling
- **JWT Authentication**: Secure token-based authentication for REST and WebSocket endpoints
- **Real-Time Communication**: WebSocket support for instant bidirectional messaging
- **React Web Frontend**: Modern browser interface built with React 18, TypeScript, and Vite
- **WebXR Frontend**: Immersive VR/AR interface using React Three Fiber and WebXR
- **Docker Orchestration**: One-command setup with Docker Compose for all services
- **Hot-Reload Development**: Automatic code reloading for rapid iteration
- **Type Safety**: Python type hints and TypeScript strict mode throughout
- **Comprehensive Testing**: Unit tests, integration tests, and property-based tests

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
│                                                              │
│  ┌──────────┐      ┌──────────┐      ┌──────────────────┐  │
│  │   Neo4j  │◄─────┤  FastAPI │◄─────┤  React Web       │  │
│  │ Database │      │  Backend │      │  Frontend :3000  │  │
│  │ :7687    │      │  :8080   │      └──────────────────┘  │
│  └──────────┘      │          │                             │
│                    │ WebSocket│      ┌──────────────────┐  │
│                    │  Support │◄─────┤  WebXR           │  │
│                    └──────────┘      │  Frontend :3001  │  │
│                                      └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- FastAPI 0.115+ (async web framework)
- Neo4j 5.15+ (graph database)
- neontology 2.1+ (Neo4j OGM)
- PyJWT 2.10+ (JWT tokens)
- uvicorn 0.34+ (ASGI server)
- Python 3.13 with uv package manager

**Web Frontend:**
- React 18+ with TypeScript 5+
- Vite 5+ (build tool and dev server)
- Axios (HTTP client)
- Native WebSocket API

**XR Frontend:**
- React Three Fiber (Three.js React renderer)
- @react-three/drei (R3F helpers)
- @react-three/xr (WebXR support)
- TypeScript 5+

## Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fastapi-neo4j-multi-frontend-system
```

2. Create environment configuration:
```bash
cp .env.example .env
# Edit .env and update JWT_SECRET and NEO4J_PASSWORD
```

3. Start all services:
```bash
docker compose up
```

Or use the setup script:
```bash
./scripts/setup.sh
```

### Access the Services

Once all services are running, access them at:

- **Web Frontend**: http://localhost:3000
- **XR Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Neo4j Browser**: http://localhost:7474

### Default Credentials

- **Neo4j**: Username `neo4j`, Password `password` (change in production!)

## Project Structure

```
.
├── backend/              # FastAPI backend service
│   ├── src/             # Source code with src/ layout
│   │   ├── auth/        # JWT authentication
│   │   ├── config/      # Configuration management
│   │   ├── database/    # Neo4j connection
│   │   ├── models/      # Neo4j data models
│   │   ├── routes/      # API endpoints
│   │   ├── schemas/     # Pydantic models
│   │   └── websocket/   # WebSocket module
│   ├── tests/           # Backend tests
│   └── Dockerfile       # Multi-stage build
│
├── frontends/
│   ├── web/            # React web frontend
│   │   ├── src/        # React components and hooks
│   │   └── tests/      # Frontend tests
│   │
│   └── xr/             # WebXR frontend
│       ├── src/        # 3D components and scenes
│       └── tests/      # XR tests
│
├── docs/               # Documentation (to be created)
│   ├── setup.md        # Detailed setup guide
│   ├── architecture.md # System architecture
│   ├── api.md          # API reference
│   └── development.md  # Development workflows
│
├── scripts/            # Helper scripts
│   ├── setup.sh        # Initial setup
│   ├── test.sh         # Run all tests
│   ├── clean.sh        # Clean containers/volumes
│   └── logs.sh         # View service logs
│
├── docker-compose.yml  # Root orchestration
└── .env.example        # Environment variables template
```

## Development

### Schema Generation Workflow

The backend uses a data model-first approach where Pydantic schemas are automatically generated from the Mind data model definitions.

**Data Model Files** (source of truth):
- `backend/src/models/mind.py` - Base Mind class
- `backend/src/models/mind_types.py` - Specialized Mind types
- `backend/src/models/enums.py` - Enum definitions

**Generated Schemas**:
- `backend/src/schemas/minds.py` - Auto-generated Pydantic schemas

**Workflow**:

1. Make changes to the data model files (mind.py, mind_types.py, or enums.py)

2. Run the schema generator:
```bash
cd backend
uv run python scripts/generate_schemas.py
```

3. Verify the generated schemas are correct:
```bash
# Review the changes
git diff src/schemas/minds.py
```

4. Run smoke tests to verify the system still works:
```bash
uv run pytest tests/smoke/ -q
```

5. Commit both the model changes and generated schemas together

**Important**: Never manually edit `src/schemas/minds.py` - always regenerate it using the script when the data model changes.

### Running Tests

Run all tests across services:
```bash
./scripts/test.sh
```

Or run tests for individual services:
```bash
# Backend tests
cd backend
uv run pytest -q

# Web frontend tests
cd frontends/web
npm test -- --run

# XR frontend tests
cd frontends/xr
npm test -- --run
```

### Viewing Logs

View logs from all services:
```bash
./scripts/logs.sh
```

View logs from a specific service:
```bash
./scripts/logs.sh backend
./scripts/logs.sh web
./scripts/logs.sh xr
./scripts/logs.sh neo4j
```

### Hot-Reload

All services support hot-reload during development:
- **Backend**: Changes to `backend/src/` automatically reload the FastAPI server
- **Web Frontend**: Changes to `frontends/web/src/` trigger Vite hot module replacement
- **XR Frontend**: Changes to `frontends/xr/src/` trigger Vite hot module replacement

### Cleaning Up

Stop services and optionally remove volumes:
```bash
./scripts/clean.sh
```

## API Overview

### Authentication

Register a new user:
```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret","fullname":"John Doe"}'
```

Login and get JWT token:
```bash
curl -X POST http://localhost:8080/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"secret"}'
```

### Posts

Create a post (requires JWT):
```bash
curl -X POST http://localhost:8080/posts \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello World","content":"My first post","tags":["intro"]}'
```

List all posts (requires JWT):
```bash
curl -X GET http://localhost:8080/posts \
  -H "Authorization: Bearer <your-jwt-token>"
```

### WebSocket

Connect to WebSocket for real-time messaging:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws?token=<your-jwt-token>');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.send(JSON.stringify({
  type: 'message',
  content: 'Hello, everyone!'
}));
```

## Documentation

Detailed documentation is available in the `docs/` directory:

- **[Setup Guide](docs/setup.md)**: Comprehensive installation and configuration instructions
- **[Architecture](docs/architecture.md)**: System design and component relationships
- **[API Reference](docs/api.md)**: Complete REST and WebSocket API documentation
- **[Development Guide](docs/development.md)**: Development workflows and best practices

> **Note**: Documentation files are currently being created. Check back soon!

## Security Considerations

### Production Deployment

Before deploying to production:

1. **Change JWT Secret**: Generate a strong random secret
   ```bash
   openssl rand -hex 32
   ```

2. **Update Neo4j Password**: Use a strong, unique password

3. **Enable HTTPS**: Configure SSL/TLS certificates for all services

4. **Update CORS Origins**: Restrict to your production domains

5. **Use Environment Variables**: Never commit secrets to version control

6. **Enable Reverse Proxy**: Uncomment and configure the proxy service in `docker-compose.yml`

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Quality

- Follow Python type hints and TypeScript strict mode
- Write tests for new features
- Ensure all tests pass before submitting PR
- Follow existing code style and conventions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:

- **Issues**: Open an issue on GitHub
- **Documentation**: Check the `docs/` directory
- **API Docs**: Visit http://localhost:8080/docs when running locally

## Roadmap

Future enhancements planned:

- [ ] User profile management and avatars
- [ ] Post comments and reactions
- [ ] Real-time collaborative editing
- [ ] Voice chat in XR environment
- [ ] Spatial audio for XR
- [ ] Mobile app support
- [ ] Advanced graph queries and analytics
- [ ] Kubernetes deployment configurations
- [ ] CI/CD pipeline setup

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Neo4j](https://neo4j.com/) - Graph database platform
- [React](https://react.dev/) - UI library
- [Three.js](https://threejs.org/) - 3D graphics library
- [Vite](https://vitejs.dev/) - Next generation frontend tooling
