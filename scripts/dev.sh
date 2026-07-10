#!/usr/bin/env bash
set -euo pipefail

echo "Start backend: cd backend && uvicorn app.main:app --reload --reload-dir app"
echo "Start frontend: cd frontend && npm run dev"
