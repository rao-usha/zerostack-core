# CLAUDE.md - ZeroStack (formerly Nex) Project Instructions

This file provides Claude Code with project-specific context and conventions.

## Project Overview

- **Name**: ZeroStack (formerly Nex)
- **Stack**: Python (FastAPI) backend + TypeScript (React/Vite) frontend + PostgreSQL
- **Purpose**: ML/Data platform with data dictionary, distillation workbench, lineage tracking, and ML development features

## Key Directories

```
backend/
├── core/              # Core config, settings
├── db/                # Database models, connections
├── domains/           # Feature domains (chat, data_explorer, distillation, etc.)
├── migrations/        # Alembic migrations
├── scripts/           # Backend scripts (seeding, etc.)
├── services/          # Shared services
└── tests/             # Backend tests

frontend/
├── src/
│   ├── api/           # API client
│   ├── components/    # Reusable components
│   └── pages/         # Page components
└── package.json

docs/                  # All documentation (see structure below)
scripts/               # Shell/PowerShell scripts
```

## Documentation Structure (IMPORTANT)

All docs MUST follow this structure. Reference `docs/plans/CODEBASE_IMPROVEMENT_PLAN.md` for current status.

```
docs/
├── README.md                    # Entry point
├── api.md, development.md       # Core docs
├── TECHNICAL_OVERVIEW.md        # Architecture
│
├── features/                    # Feature docs (one per feature)
├── setup/                       # Installation & config guides
├── guides/                      # User tutorials
├── plans/                       # Roadmaps & improvement plans
│   ├── CODEBASE_IMPROVEMENT_PLAN.md   # Master improvement plan
│   ├── PARALLEL_EXECUTION_PLAN.md     # Work streams for agents
│   ├── FEATURE_ROADMAP.md
│   └── FEATURE_STATUS.md
├── reference/                   # Technical references (ML, MCP, GPU)
├── branding/                    # Style guides
├── testing/                     # Test procedures
└── archive/                     # Historical (bug-fixes, implementation-notes)
```

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
pytest                           # Run tests
alembic upgrade head             # Run migrations
```

### Frontend
```bash
cd frontend
npm install
npm run dev                      # Start dev server (port 5173)
npm run build                    # Production build
npm run lint                     # Lint check
```

### Database
```bash
# PostgreSQL should be running
# See docs/setup/DATABASE_SETUP.md for details
```

## Code Conventions

### Backend (Python)
- FastAPI for routing
- SQLAlchemy models in `domains/*/db_models.py`
- Pydantic schemas in `domains/*/models.py`
- Services in `domains/*/service.py`
- Follow existing domain patterns

### Frontend (TypeScript/React)
- Functional components with hooks
- API calls via `src/api/client.ts`
- Pages in `src/pages/`, components in `src/components/`
- TailwindCSS for styling

## Multi-Agent Workflow

When working on codebase improvements, reference:
- `docs/plans/CODEBASE_IMPROVEMENT_PLAN.md` - Full feature status and tasks
- `docs/plans/PARALLEL_EXECUTION_PLAN.md` - Work streams for parallel execution

### Work Streams (for parallel agents)
- **Stream A**: Security & Auth (critical path)
- **Stream B**: Backend feature completion
- **Stream C**: Frontend improvements
- **Stream D**: Testing
- **Stream E**: Operations (Docker, CI/CD)
- **Stream F**: Quick wins

## Git Workflow

- Branch from `main`
- Branch naming: `type/description` (e.g., `feat/add-auth`, `fix/login-bug`)
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Always test before committing

## Development Workflow (MANDATORY)

Every feature implementation MUST follow this sequence:

1. **Explore** - Read existing code, understand patterns, identify dependencies
2. **Plan** - Create a clear plan with steps, use TodoWrite to track
3. **Approve** - Get user approval before implementing (use EnterPlanMode for complex tasks)
4. **Execute** - Implement the feature following existing patterns
5. **Test** - Run tests, verify functionality works:
   - Backend: `pytest backend/tests/` or specific test file
   - Frontend: `npm run build` (catches TS errors), manual verification
   - API: `curl` or Postman to verify endpoints
6. **Fix** - Address any test failures or bugs found
7. **Test Again** - Verify fixes work, run full test suite
8. **Commit** - Only commit after tests pass

**NEVER commit untested code.** Testing is not optional.

## Important Notes

1. **Never skip testing** - Test before every commit
2. **Never skip planning** - Use TodoWrite for multi-step tasks
3. **Follow existing patterns** - Check similar domains before implementing
4. **Update docs** - Keep feature docs in sync with implementation
5. **Archive completed work** - Move implementation notes to `docs/archive/`
