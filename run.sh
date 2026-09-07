#!/usr/bin/env bash
# JALDRISHTI AI Quick Start Script
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Ensure virtualenv is used
if [ -d "$PROJECT_ROOT/.venv" ]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="$(command -v python3)"
else
    echo "Error: Python not found. Please set up a virtual environment."
    exit 1
fi

echo "=========================================="
echo " Starting JALDRISHTI AI Services"
echo "=========================================="
echo "Python binary : $PYTHON"
echo "Project root  : $PROJECT_ROOT"

# 1. Start or verify FastAPI backend on port 8000
if lsof -i :8000 &>/dev/null; then
    echo "✓ Backend is already running on http://127.0.0.1:8000"
else
    echo "Starting FastAPI backend on http://127.0.0.1:8000..."
    "$PYTHON" -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload &
    BACKEND_PID=$!
    echo "✓ Backend started (PID: $BACKEND_PID)"
fi

# 2. Start frontend on port 3000
if lsof -i :3000 &>/dev/null; then
    echo "✓ Frontend is already running on http://localhost:3000"
else
    echo "Starting frontend dev server on http://localhost:3000..."
    cd "$PROJECT_ROOT/apps/web"
    npm run dev &
    FRONTEND_PID=$!
    echo "✓ Frontend started (PID: $FRONTEND_PID)"
fi

echo "=========================================="
echo "JALDRISHTI AI is live:"
echo "  • Frontend UI : http://localhost:3000"
echo "  • Backend API : http://127.0.0.1:8000"
echo "  • Swagger API : http://127.0.0.1:8000/docs"
echo "=========================================="
