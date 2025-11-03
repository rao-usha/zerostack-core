#!/usr/bin/env bash
set -euo pipefail

echo "==> Cleaning up..."

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove test artifacts
rm -rf .pytest_cache 2>/dev/null || true
rm -rf .mypy_cache 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true
rm -rf .coverage 2>/dev/null || true

# Remove frontend build artifacts (optional - comment out if you want to keep builds)
# rm -rf frontend/dist 2>/dev/null || true
# rm -rf frontend/node_modules/.cache 2>/dev/null || true

echo "==> Cleanup done"

