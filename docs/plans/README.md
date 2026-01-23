# NEX Implementation Plans

This directory contains detailed implementation plans organized by agent topic/feature area. Each plan documents:

- **Architecture decisions** - How the feature integrates with existing NEX components
- **Database schema** - Tables, migrations, relationships
- **API endpoints** - REST API design
- **Service implementations** - Backend logic
- **Frontend components** - UI pages and components
- **Acceptance criteria** - What defines "done"

## Plan Index

| Plan | Status | Description | Created |
|------|--------|-------------|---------|
| [GPU Runner (Phase A)](./gpu-runner/PLAN.md) | ✅ Complete | Remote GPU compute for ML model runs | 2026-01-06 |
| [ML Compute Engine (Phase B)](./ml-compute-engine/PLAN.md) | ✅ Complete | Cost tracking, reuse engine, RunPod | 2026-01-07 |
| [Phase 2 Features](../PHASE_2_ROADMAP.md) | ✅ Complete | Drift detection, scheduling, versioning | 2026-01-09 |
| [Synthetic Data](./synthetic-data/PLAN.md) | ✅ Complete | Synthetic data generation with SDV | 2026-01-15 |
| [Feature Store](./feature-store/PLAN.md) | 🔵 Planned | Centralized ML feature management | 2026-01-16 |

## Directory Structure

```
docs/plans/
├── README.md                 # This file - plan index
├── gpu-runner/               # Phase A: GPU Runner / Remote Compute
│   ├── PLAN.md              # Main implementation plan
│   └── CHANGELOG.md         # Implementation progress log
├── ml-compute-engine/        # Phase B: Cost-aware, reliable execution
│   ├── PLAN.md              # Main implementation plan
│   └── CHANGELOG.md         # Implementation progress log
├── synthetic-data/           # Synthetic data generation
│   ├── PLAN.md              # Main implementation plan
│   └── CHANGELOG.md         # Implementation progress log
├── feature-store/            # Feature Store for ML
│   ├── PLAN.md              # Main implementation plan
│   └── CHANGELOG.md         # Implementation progress log
├── model-registry/          # (Future) Model versioning & registry
└── ...
```

## Plan Template

When creating a new plan, include:

1. **Overview** - What problem does this solve?
2. **Architecture** - How does it fit into NEX?
3. **Database Schema** - Migrations and models
4. **API Design** - Endpoints and contracts
5. **Implementation Order** - Step-by-step tasks
6. **Acceptance Criteria** - Definition of done

## Status Legend

- 🔵 Planned - Not started
- 🚧 In Progress - Currently implementing
- ✅ Complete - Fully implemented
- ⏸️ Paused - On hold
- ❌ Cancelled - Not pursuing
