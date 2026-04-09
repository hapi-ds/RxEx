import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.config import settings
from src.database.database import initiate_database
from src.exceptions import (
    MindDatabaseError,
    MindError,
    MindNotFoundError,
    MindValidationError,
    RateLimitError,
)
from src.logging_config import setup_logging
from src.routes.minds import (
    generic_exception_handler,
    mind_database_handler,
    mind_error_handler,
    mind_not_found_handler,
    mind_validation_handler,
    rate_limit_handler,
    value_error_handler,
)
from src.routes.minds import (
    router as minds_router,
)
from src.routes.relationships import router as relationships_router
from src.routes.posts import PostRouter
from src.routes.users import UserRouter
from src.routes.chat import router as chat_router
from src.routes.skills import skills_router
from src.routes.data import data_router
from src.routes.schedules import router as schedules_router
from src.routes.reports import router as reports_router
from src.routes.fmea import router as fmea_router
from src.routes.graphrag import router as graphrag_router
from src.websocket.routes import router as websocket_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.
    """
    setup_logging(settings)
    logger.info(
        "Application starting: log_dir=%s, log_level=%s",
        settings.log_dir,
        settings.log_level,
    )
    logger.info(
        "AI Chat Service configuration loaded",
        extra={
            "provider": settings.ai_provider,
            "model": settings.ai_model_name,
            "endpoint": settings.ai_api_endpoint,
            "request_timeout": settings.ai_request_timeout,
        },
    )
    initiate_database()
    yield
    logger.info("App shutdown complete.")


app = FastAPI(
    title="FastAPI Neo4j Multi-Frontend System",
    version="1.0.0",
    description="""
## Multi-Frontend System API

A high-performance FastAPI backend with Neo4j graph database, supporting multiple frontend clients
(web and XR/VR) with real-time WebSocket communication.

### Features

* **JWT Authentication**: Secure token-based authentication for REST and WebSocket endpoints
* **User Management**: Complete CRUD operations for user accounts
* **Post Management**: Create, read, update, and delete posts with tagging support
* **Real-time Communication**: WebSocket support for instant messaging between clients
* **Graph Database**: Neo4j for powerful relationship modeling

### Authentication

Most endpoints require JWT authentication. To authenticate:

1. Register a new user via `POST /users` or use existing credentials
2. Login via `POST /users/login` to receive a JWT access token
3. Include the token in the `Authorization` header as `Bearer <token>` for subsequent requests
4. For WebSocket connections, pass the token as a query parameter: `/ws?token=<token>`

Tokens expire after 40 minutes. You'll need to login again to get a fresh token.
    """,
    contact={"name": "API Support", "email": "samanidarix@gmail.com"},
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {"name": "Root", "description": "Health check and welcome endpoints"},
        {
            "name": "Administrator",
            "description": "User management operations including registration, login, and profile updates",
        },
        {
            "name": "Posts",
            "description": "Post management operations for creating and managing content",
        },
        {
            "name": "WebSocket",
            "description": "Real-time communication endpoints for instant messaging",
        },
    ],
    lifespan=lifespan,
)

# CORS middleware for multiple frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://web:3000",
        "http://xr:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def read_root():
    """Health check and welcome endpoint."""
    return {"message": "Welcome to this fantastic app."}


app.include_router(UserRouter, tags=["Administrator"], prefix="/users")
app.include_router(PostRouter, tags=["Posts"], prefix="/posts")
app.include_router(minds_router, tags=["Minds"], prefix="/api/v1/minds")
app.include_router(relationships_router, tags=["Relationships"], prefix="/api/v1/relationships")
app.include_router(chat_router, tags=["Chat"], prefix="/api/v1/chat")
app.include_router(skills_router, tags=["Skills"], prefix="/api/v1/skills")
app.include_router(data_router, tags=["Data"], prefix="/api/v1")
app.include_router(schedules_router, tags=["Scheduling"])
app.include_router(reports_router, tags=["Reports"])
app.include_router(fmea_router, tags=["FMEA"])
app.include_router(graphrag_router, tags=["GraphRAG"], prefix="/api/v1/graphrag")
app.include_router(websocket_router, tags=["WebSocket"])

# Register exception handlers for Mind system
app.add_exception_handler(MindNotFoundError, mind_not_found_handler)
app.add_exception_handler(MindValidationError, mind_validation_handler)
app.add_exception_handler(MindDatabaseError, mind_database_handler)
app.add_exception_handler(RateLimitError, rate_limit_handler)
app.add_exception_handler(MindError, mind_error_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)
