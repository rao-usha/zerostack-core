#!/usr/bin/env bash
set -euo pipefail

echo "==> Formatting"
python -m black backend

echo "==> Linting"
ruff check backend

echo "==> Typing"
mypy backend --ignore-missing-imports

echo "==> Security (bandit)"
bandit -q -r backend || true

echo "==> Python dependency audit"
pip-audit || true

echo "==> Frontend build"
npm --prefix frontend ci
npm --prefix frontend run build

echo "==> Pytests"
pytest -q --maxfail=1 --disable-warnings

echo "==> Smoke tests"
bash scripts/smoke_backend.sh "postgresql+psycopg://nex:nex@localhost:5432/nex"

echo "==> Done"

