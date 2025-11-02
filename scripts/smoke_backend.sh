#!/usr/bin/env bash
set -euo pipefail

DB_URL="${1:-postgresql+psycopg://nex:nex@localhost:5432/nex}"

# Export for backend settings (pydantic-settings will read this)
# Settings uses 'database_url' field with case_sensitive=False, so DATABASE_URL maps correctly
export DATABASE_URL="$DB_URL"

echo "==> Smoke: backend health"

# Save current directory
ORIG_DIR=$(pwd)

# Start uvicorn in background for smoke test
cd backend || exit 1
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning &
PID=$!

# Return to original directory
cd "$ORIG_DIR" || exit 1

# Wait for server to start
sleep 5

# Check health endpoint
set +e
curl -fsS http://localhost:8000/health > /dev/null 2>&1
status=$?
set -e

# Kill the server
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true

if [ $status -ne 0 ]; then
  echo "ERROR: Health endpoint check failed"
  exit 1
fi

echo "==> Smoke OK"

