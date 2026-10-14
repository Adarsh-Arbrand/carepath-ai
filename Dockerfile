# Multi-stage build for CarePath AI
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --omit=dev

COPY frontend/ ./
RUN npm run build

# Stage 2: Build backend
FROM python:3.11-slim AS backend-builder

WORKDIR /app

COPY backend/requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY backend/ ./

# Copy frontend build to backend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Stage 3: Production image
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
COPY backend/requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# Copy backend code
COPY backend/ ./

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
