# frontends/phone/Dockerfile
FROM node:20-alpine AS base

WORKDIR /app

# Use the existing node user (UID 1000)
RUN chown -R node:node /app

# Development stage
FROM base AS development

USER node

# Copy package files
COPY --chown=node:node package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY --chown=node:node . .

# Expose port
EXPOSE 3002

# Command will be overridden by docker-compose
CMD ["npm", "run", "dev"]

# Build stage
FROM base AS build

USER node

COPY --chown=node:node package*.json ./
RUN npm ci

COPY --chown=node:node . .
RUN npm run build

# Production stage
FROM nginx:1.25-alpine AS production

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user for nginx or use existing one
RUN if ! id -u appuser > /dev/null 2>&1; then \
        adduser -D -u 1000 appuser; \
    fi && \
    chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

USER appuser

EXPOSE 3002

CMD ["nginx", "-g", "daemon off;"]
