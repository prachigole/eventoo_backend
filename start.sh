#!/bin/bash
set -e

cd "$(dirname "$0")"   # always run from eventoo_backend/, regardless of where you call this from

source .venv/bin/activate

echo "✓ PostgreSQL: $(pg_isready)"
echo "✓ Starting Eventoo backend on http://0.0.0.0:8000"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
