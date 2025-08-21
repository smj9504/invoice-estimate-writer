@echo off
echo Starting MJ Estimate Application Servers...
echo.

REM Start backend server
echo [1/2] Starting Backend API Server (Port 8000)...
start cmd /k "cd /d %~dp0 && call venv\Scripts\activate && cd backend && uvicorn app.main:app --reload --port 8000"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

REM Start frontend React server
echo [2/2] Starting Frontend React Server (Port 3000)...
start cmd /k "cd /d %~dp0\frontend && set GENERATE_SOURCEMAP=false && npm start 2>nul"

echo.
echo Both servers are starting...
echo.
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Frontend React: http://localhost:3000
echo.
echo Press any key to exit this window...
pause > nul