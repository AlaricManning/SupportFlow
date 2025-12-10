# Multi-stage build for SupportFlow

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy knowledge base
COPY knowledge_base/ ./knowledge_base/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./data/supportflow.db
ENV CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
