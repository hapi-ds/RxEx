# Multi-stage Dockerfile for FastAPI backend
FROM python:3.13-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Development stage
FROM base AS development

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

USER appuser

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY --chown=appuser:appuser src/ ./src/

# Expose port
EXPOSE 8080

# Command will be overridden by docker-compose
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]

# Production stage
FROM base AS production

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

USER appuser

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy source code
COPY --chown=appuser:appuser src/ ./src/

# Expose port
EXPOSE 8080

# Run with production settings
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
