#!/bin/bash

echo "Starting MJ Estimate Generator Servers..."
echo ""

# Start Backend API
echo "[1/2] Starting FastAPI Backend Server..."
cd backend && python run.py &
BACKEND_PID=$!

# Start Frontend
echo "[2/2] Starting React Frontend Server..."
cd ../frontend && npm start &
FRONTEND_PID=$!

echo ""
echo "Servers are starting..."
echo "- Backend API: http://localhost:8000"
echo "- Frontend App: http://localhost:3000"
echo "- API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID