@echo off
echo ====================================
echo   SupportFlow - Local Development
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "backend\venv\" (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    echo Installing backend dependencies...
    pip install -r requirements.txt
    cd ..
) else (
    echo Virtual environment found.
)

REM Check if .env exists
if not exist "backend\.env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy backend\.env.example to backend\.env
    echo and add your OPENAI_API_KEY
    pause
    exit /b 1
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules\" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo Starting SupportFlow...
echo.
echo Backend will run on: http://localhost:8000
echo Frontend will run on: http://localhost:3000
echo.
echo Press Ctrl+C to stop both servers
echo.

REM Start backend in background
start "SupportFlow Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload"

REM Wait a bit for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
start "SupportFlow Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers starting...
echo Check the new terminal windows for output.
echo.
pause
