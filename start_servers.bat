@echo off
echo Starting MJ Estimate Application Servers...
echo.

REM Start backend server
echo [1/2] Starting Backend API Server (Port 8000)...
start cmd /k "cd /d %~dp0\backend && ..\venv\Scripts\activate && python run.py"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

REM Start frontend Streamlit server
echo [2/2] Starting Frontend Streamlit Server (Port 8501)...
start cmd /k "cd /d %~dp0 && venv\Scripts\activate && streamlit run app.py"

echo.
echo Both servers are starting...
echo.
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Frontend: http://localhost:8501
echo.
echo Press any key to exit this window...
pause > nul