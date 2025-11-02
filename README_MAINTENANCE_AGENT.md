# Maintenance Agent

The Maintenance Agent automatically checks, debugs, and cleans your NEX.AI application on a regular schedule using GitHub Actions.

## Overview

The agent runs **every 6 hours** and performs:

1. **Code Quality Checks**: Formatting (black), linting (ruff), type checking (mypy)
2. **Security Scanning**: Bandit (Python security), pip-audit (dependency vulnerabilities)
3. **Testing**: Unit tests and smoke tests
4. **Build Verification**: Frontend build check
5. **Auto-issue Creation**: Opens a GitHub issue if any check fails

## Local Usage

Run the same checks locally using the Makefile:

```bash
# Run all checks
make verify

# Individual checks
make format    # Auto-format code with black
make lint      # Run ruff and bandit
make type      # Type checking with mypy
make test      # Run pytest
make build     # Build frontend
make smokes    # Smoke test backend health
make clean     # Clean cache and artifacts
```

## Files Added

- `.github/workflows/agent.yml` - GitHub Actions workflow
- `docker-compose.ci.yml` - Minimal Postgres setup for CI
- `requirements-dev.txt` - Development dependencies
- `Makefile` - Task runner for local checks
- `scripts/smoke_backend.sh` - Backend health check
- `scripts/cleanup.sh` - Cleanup script
- `scripts/agent_ci.sh` - Full CI runner script
- `backend/tests/test_health.py` - Health endpoint test
- `.pre-commit-config.yaml` - Optional pre-commit hooks
- `pytest.ini` - Pytest configuration

## Setup Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

This will automatically format and lint your code before each commit.

## Manual Workflow Trigger

You can manually trigger the maintenance agent from GitHub Actions UI:
- Go to Actions tab → Maintenance Agent → Run workflow

## Customization

- **Schedule**: Edit `.github/workflows/agent.yml` cron schedule (default: every 6 hours)
- **Checks**: Modify `Makefile` targets
- **Dependencies**: Update `requirements-dev.txt` for Python dev tools

## Troubleshooting

If the agent fails:
1. Check the GitHub Actions logs
2. Run `make verify` locally to reproduce
3. An issue will be auto-created in your repo with a link to the failed run

