#!/bin/bash

echo "===================================="
echo "  SupportFlow - Local Development"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r requirements.txt
    cd ..
else
    echo -e "${GREEN}Virtual environment found.${NC}"
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo ""
    echo -e "${RED}WARNING: .env file not found!${NC}"
    echo "Please copy backend/.env.example to backend/.env"
    echo "and add your OPENAI_API_KEY"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo ""
echo -e "${GREEN}Starting SupportFlow...${NC}"
echo ""
echo "Backend will run on: http://localhost:8000"
echo "Frontend will run on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Start backend
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}Both servers running!${NC}"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""

# Wait for user to stop
wait
