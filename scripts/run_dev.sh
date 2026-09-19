#!/usr/bin/env bash
# HireFlow Phase 0 Development Runner

echo "Starting HireFlow Backend..."
cd backend && uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting HireFlow Frontend..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

function cleanup {
  echo "Stopping services..."
  kill $BACKEND_PID
  kill $FRONTEND_PID
}

trap cleanup EXIT
wait
