#!/bin/bash

# SupportFlow - Docker Deployment Script
# Usage: ./deploy-docker.sh

set -e  # Exit on error

echo "=================================="
echo "  SupportFlow - Docker Deployment"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo ""
    echo "Please create .env file with:"
    echo "  OPENAI_API_KEY=your-key-here"
    echo "  DB_PASSWORD=your-db-password"
    echo "  SECRET_KEY=your-secret-key"
    echo ""
    echo "You can copy from .env.example:"
    echo "  cp backend/.env.example .env"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo -e "${GREEN}✓ .env file found${NC}"
echo ""

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Build images
echo ""
echo "Building Docker images..."
docker-compose build

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for backend to be ready
echo ""
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo ""
echo "=================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=================================="
echo ""
echo "Services running:"
echo "  • Backend API:  http://localhost:8000"
echo "  • Frontend:     http://localhost:3000"
echo "  • API Docs:     http://localhost:8000/docs"
echo "  • Database:     PostgreSQL on port 5432"
echo ""
echo "View logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
