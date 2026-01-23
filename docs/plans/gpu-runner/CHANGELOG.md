# GPU Runner - Implementation Changelog

Track implementation progress and decisions made during development.

---

## 2026-01-06 - Initial Implementation

### Plan Review & Adjustments

**Original Plan Issues Identified:**
- `model_runs` table would conflict with existing `ml_run`
- `model_recipes` table would conflict with existing `ml_recipe`
- `dataset_versions` table already exists

**Resolution:**
- Extend `ml_run` with compute fields instead of new table
- Extend `ml_recipe` with container fields instead of new table
- Create `highlighted_dataset_versions` for GPU runner datasets
- New `highlighted_datasets` domain (distinct concept)
- New `ml_derived_assets` table following distillation pattern

### Implementation Started

- [ ] Created documentation structure at `docs/plans/`
- [ ] Saved implementation plan at `docs/plans/gpu-runner/PLAN.md`

---

## Progress Log

### Step 1: Docker Compose + MinIO
- **Status:** ✅ Complete
- **Notes:** Added MinIO service, minio-setup, env vars to backend

### Step 2: Config Settings
- **Status:** ✅ Complete
- **Notes:** Added S3, compute, and GPU runner settings to config.py

### Step 3: Migration
- **Status:** ✅ Complete
- **Notes:** Created 020_add_gpu_runner.py migration

### Step 4: Object Store Service
- **Status:** ✅ Complete
- **Notes:** Created services/object_store/ with client.py and paths.py

### Step 5: Compute Service
- **Status:** ✅ Complete
- **Notes:** Created services/compute/ with adapter, local, SSH adapters, and finalizer

### Step 6: Highlighted Datasets Domain
- **Status:** ✅ Complete
- **Notes:** Created domains/highlighted_datasets/ with full CRUD and upload

### Step 7: ML Development Extensions
- **Status:** ✅ Complete
- **Notes:** Added db models, registered router in main.py

### Step 8: Interaction Logger
- **Status:** ✅ Complete
- **Notes:** Created services/interaction_logger.py

### Step 9: Forecast Recipe Container
- **Status:** ✅ Complete
- **Notes:** Created recipes/forecast_m5_v1/ with Dockerfile, run.py

### Step 10: Seed Script
- **Status:** ✅ Complete
- **Notes:** Created scripts/seed_gpu_runner.py

### Step 11: Frontend Pages
- **Status:** ✅ Complete
- **Notes:** Created HighlightedDatasets.tsx and DerivedAssets.tsx

### Step 12: Routes Update
- **Status:** ✅ Complete
- **Notes:** Added routes to App.tsx

### Step 13: Missing Endpoints (Added 2026-01-06)
- **Status:** ✅ Complete
- **Notes:** Added:
  - `GET /runs/{id}/logs` - Fetch run logs
  - `POST /runs/{id}/cancel` - Cancel running job
  - `POST /runs/{id}/bank` - Bank results as derived asset
  - `GET /assets` - List derived assets
  - `GET /assets/{id}` - Get asset details
  - `POST /assets/{id}/promote` - Promote to permanent
  - `DELETE /assets/{id}` - Delete asset
  - `GET /interactions` - List interaction logs
  - `GET /interactions/session/{id}` - Session history
  - `GET /interactions/run/{id}` - Run history
  - `GET /interactions/event-types` - List event types

### Step 14: Background Finalizer
- **Status:** ✅ Complete
- **Notes:** Wired up RunFinalizer in main.py lifespan

### Step 15: Smoke Test Documentation
- **Status:** ✅ Complete
- **Notes:** Created GPU_RUNNER_SMOKE_TEST.md

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-06 | Extend ml_run vs new table | Avoid naming conflict, reuse existing infrastructure |
| 2026-01-06 | Use MinIO for object storage | S3-compatible, works locally and in production |
| 2026-01-06 | SSH adapter first | Simpler to implement than K8s gateway, works immediately |
| 2026-01-06 | 14-day default TTL | Balance between keeping useful results and storage costs |
