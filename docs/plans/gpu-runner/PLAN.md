# GPU Runner - Phase A Implementation Plan

> **Status:** ✅ Implementation Complete  
> **Created:** 2026-01-06  
> **Last Updated:** 2026-01-06

## Overview

Implement remote GPU compute execution for ML model runs, starting with M5 forecasting. This feature **extends the existing `ml_development` domain** rather than creating parallel structures.

### Goals

- Remote GPU compute execution for model runs
- Highlighted Datasets catalog with availability resolver
- Automatic results banking as Temporal/Permanent DerivedAssets
- Full interaction audit trail linking chat → run → asset
- Minimal but working UI for the complete workflow

### Use Case

1. User selects M5 dataset from Highlighted Datasets
2. User triggers a forecasting run with parameters
3. System submits job to remote GPU (SSH or K8s)
4. System polls job status, captures logs
5. On success, system auto-banks results as Temporal DerivedAsset
6. User can promote to Permanent if results are valuable

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NEX Platform                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ml_development (EXTENDED)                         │    │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────────────────┐   │    │
│  │  │ ml_recipe  │  │  ml_model  │  │         ml_run              │   │    │
│  │  │ + container│──│            │──│ + compute_target            │   │    │
│  │  │   _image   │  │            │  │ + remote_job_id             │   │    │
│  │  └────────────┘  └────────────┘  │ + input_dataset_version_id  │   │    │
│  │                                   │ + logs_uri, output_uri      │   │    │
│  │                                   └──────────────┬──────────────┘   │    │
│  │                                                  │                   │    │
│  │  ┌───────────────────────────────────────────────▼───────────────┐  │    │
│  │  │              ml_derived_assets (NEW TABLE)                    │  │    │
│  │  │  • Temporal / Permanent results banking                       │  │    │
│  │  │  • TTL expiry for temporal assets                             │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              highlighted_datasets (NEW DOMAIN)                       │    │
│  │  • Curated dataset catalog (M5, etc.)                               │    │
│  │  • Availability resolver (AVAILABLE / NOT_PRESENT)                  │    │
│  │  • Versioned dataset references with manifests                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              interaction_logs (NEW TABLE)                            │    │
│  │  • Chat-session-aware audit trail                                   │    │
│  │  • Links chat → run → asset for full traceability                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                            Services Layer                                    │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │  services/compute/   │  │ services/object_store│                         │
│  │  • ComputeAdapter    │  │ • S3/MinIO client    │                         │
│  │  • SSHAdapter        │  │ • URI helpers        │                         │
│  │  • K8sGatewayAdapter │  │ • Manifest I/O       │                         │
│  │  • RunFinalizer      │  │                      │                         │
│  └──────────────────────┘  └──────────────────────┘                         │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                         Infrastructure Layer                                 │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌─────────────────────┐               │
│  │Postgres│  │ MinIO  │  │  API   │  │  Compute Gateway    │               │
│  │   DB   │  │  (S3)  │  │(FastAPI│  │  (or SSH to GPU VM) │               │
│  └────────┘  └────────┘  └────────┘  └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Extend `ml_run`** instead of creating new `model_runs` table (avoids naming conflict)
2. **Extend `ml_recipe`** with container fields instead of new `model_recipes` table
3. **New `highlighted_datasets` domain** - distinct concept from existing datasets
4. **New `ml_derived_assets` table** - follows distillation banking pattern
5. **Add MinIO** for S3-compatible object storage
6. **ComputeAdapter abstraction** - supports SSH and K8s backends

---

## Database Schema

### Migration: `020_add_gpu_runner.py`

#### 1. Extend `ml_recipe`

```sql
ALTER TABLE ml_recipe ADD COLUMN container_image VARCHAR(500);
ALTER TABLE ml_recipe ADD COLUMN container_entrypoint TEXT[];
ALTER TABLE ml_recipe ADD COLUMN default_compute_target VARCHAR(50) DEFAULT 'local';
ALTER TABLE ml_recipe ADD COLUMN gpu_required BOOLEAN DEFAULT FALSE;
```

#### 2. Extend `ml_run`

```sql
ALTER TABLE ml_run ADD COLUMN compute_target VARCHAR(50) DEFAULT 'local';
ALTER TABLE ml_run ADD COLUMN remote_job_id VARCHAR(255);
ALTER TABLE ml_run ADD COLUMN input_dataset_version_id UUID;
ALTER TABLE ml_run ADD COLUMN parameters JSONB DEFAULT '{}';
ALTER TABLE ml_run ADD COLUMN logs_uri VARCHAR(500);
ALTER TABLE ml_run ADD COLUMN output_manifest_uri VARCHAR(500);
ALTER TABLE ml_run ADD COLUMN status_reason TEXT;
ALTER TABLE ml_run ADD COLUMN created_by VARCHAR(100);
ALTER TABLE ml_run ADD COLUMN chat_session_id VARCHAR(100);
```

#### 3. New: `highlighted_datasets`

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(100) PK | e.g., "m5_forecasting" |
| display_name | VARCHAR(255) | Human-readable name |
| description | TEXT | Dataset description |
| tags | TEXT[] | Searchable tags |
| source_type | VARCHAR(50) | manual_upload, http_download, kaggle |
| availability_state | VARCHAR(30) | AVAILABLE, NOT_PRESENT, REQUIRES_CREDENTIALS |
| resolver_config | JSONB | Resolver-specific configuration |
| license_notes | TEXT | License information |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

#### 4. New: `highlighted_dataset_versions`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| highlighted_dataset_id | VARCHAR(100) FK | |
| version_label | VARCHAR(64) | e.g., "v1" |
| manifest_uri | VARCHAR(500) | s3://bucket/datasets/m5/v1/manifest.json |
| storage_uri | VARCHAR(500) | s3://bucket/datasets/m5/v1/ |
| file_count | INTEGER | |
| total_bytes | BIGINT | |
| schema_json | JSONB | Optional schema |
| created_at | TIMESTAMPTZ | |
| created_by | VARCHAR(100) | |

#### 5. New: `ml_derived_assets`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| source_run_id | VARCHAR(255) FK | |
| name | VARCHAR(255) | |
| asset_type | VARCHAR(20) | temporal, permanent |
| storage_uri | VARCHAR(500) | s3://bucket/assets/{id}/ |
| manifest_uri | VARCHAR(500) | |
| ttl_expires_at | TIMESTAMPTZ | NULL for permanent |
| metrics_json | JSONB | Copied from run |
| tags | TEXT[] | |
| approval_state | VARCHAR(20) | draft, approved |
| notes | TEXT | |
| created_at | TIMESTAMPTZ | |
| promoted_at | TIMESTAMPTZ | When promoted to permanent |

#### 6. New: `interaction_logs`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| chat_session_id | VARCHAR(100) | Links to chat session |
| actor | VARCHAR(50) | user, assistant, system |
| event_type | VARCHAR(50) | See event types below |
| message | TEXT | Optional message content |
| refs | JSONB | {run_id, asset_id, dataset_id} |
| metadata | JSONB | Additional context |
| created_at | TIMESTAMPTZ | |

**Event Types:**
- CHAT_MESSAGE, DATASET_RESOLVE, INGEST_START, INGEST_COMPLETE
- RUN_SUBMITTED, RUN_STARTED, RUN_COMPLETED, RUN_FAILED
- ASSET_CREATED, ASSET_PROMOTED, VIEW_STATUS, VIEW_LOGS

---

## API Endpoints

### Highlighted Datasets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/highlighted-datasets` | List all with availability |
| GET | `/api/v1/highlighted-datasets/{id}` | Get details |
| POST | `/api/v1/highlighted-datasets/{id}/resolve` | Resolve (download if needed) |
| POST | `/api/v1/highlighted-datasets/{id}/upload` | Manual file upload |
| GET | `/api/v1/highlighted-datasets/{id}/versions` | List versions |

### ML Runs (Extended)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ml-development/runs` | Create run (supports compute_target) |
| GET | `/api/v1/ml-development/runs/{id}` | Get with compute details |
| GET | `/api/v1/ml-development/runs/{id}/logs` | Stream/fetch logs |
| POST | `/api/v1/ml-development/runs/{id}/cancel` | Cancel job |
| POST | `/api/v1/ml-development/runs/{id}/bank` | Bank as derived asset |

### Derived Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ml-development/assets` | List assets |
| GET | `/api/v1/ml-development/assets/{id}` | Get details |
| POST | `/api/v1/ml-development/assets/{id}/promote` | Promote to permanent |
| DELETE | `/api/v1/ml-development/assets/{id}` | Delete asset |

### Interaction Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/interactions` | List (filterable) |
| GET | `/api/v1/interactions/session/{id}` | Get session history |

---

## File Structure

```
backend/
├── domains/
│   ├── ml_development/           # EXTENDED
│   │   ├── derived_assets_service.py  # NEW
│   │   └── ... (extended models, router, service)
│   │
│   └── highlighted_datasets/     # NEW DOMAIN
│       ├── __init__.py
│       ├── db_models.py
│       ├── models.py
│       ├── router.py
│       ├── service.py
│       └── resolvers/
│           ├── base.py
│           ├── manual_upload.py
│           └── http_download.py
│
├── services/
│   ├── compute/                  # NEW
│   │   ├── adapter.py
│   │   ├── ssh_adapter.py
│   │   ├── k8s_gateway_adapter.py
│   │   ├── local_adapter.py
│   │   └── finalizer.py
│   │
│   ├── object_store/             # NEW
│   │   ├── client.py
│   │   ├── paths.py
│   │   └── manifests.py
│   │
│   └── interaction_logger.py     # NEW

recipes/
└── forecast_m5_v1/               # NEW
    ├── Dockerfile
    ├── requirements.txt
    └── run.py
```

---

## Object Store Layout

```
nex-data/                          # S3 Bucket
├── datasets/
│   └── m5/v1/
│       ├── manifest.json
│       └── raw/*.csv
├── runs/{run_id}/
│   ├── logs.txt
│   └── outputs/
│       ├── run_manifest.json
│       ├── metrics.json
│       └── forecast.parquet
└── assets/{asset_id}/
    ├── manifest.json
    └── data/
```

---

## Configuration

Add to `core/config.py`:

```python
# Object Storage
s3_endpoint: str = "http://localhost:9000"
s3_access_key: str = "minioadmin"
s3_secret_key: str = "minioadmin"
s3_bucket: str = "nex-data"

# Compute
compute_adapter: str = "local"  # local, ssh, k8s_gateway
ssh_host: Optional[str] = None
ssh_user: str = "ubuntu"
ssh_key_path: Optional[str] = None

# GPU Runner
gpu_count_default: int = 1
derived_asset_ttl_days: int = 14
finalizer_poll_interval_seconds: int = 30
```

---

## Implementation Order

| Step | Task | Status |
|------|------|--------|
| 1 | Add MinIO to docker-compose | ⬜ |
| 2 | Add config settings | ⬜ |
| 3 | Create migration 020 | ⬜ |
| 4 | Implement object_store service | ⬜ |
| 5 | Implement compute service | ⬜ |
| 6 | Create highlighted_datasets domain | ⬜ |
| 7 | Extend ml_development domain | ⬜ |
| 8 | Implement interaction_logger | ⬜ |
| 9 | Build forecast recipe container | ⬜ |
| 10 | Create seed script | ⬜ |
| 11 | Frontend pages | ⬜ |
| 12 | Update App.tsx routes | ⬜ |
| 13 | End-to-end test | ⬜ |
| 14 | Documentation | ⬜ |

---

## Acceptance Criteria

- [ ] `GET /highlighted-datasets` returns M5 with `NOT_PRESENT` state
- [ ] Upload files changes state to `AVAILABLE`
- [ ] `POST /ml-development/runs` with `compute_target: "gpu-ssh"` submits remote job
- [ ] Run status transitions: queued → running → succeeded
- [ ] Logs captured and accessible
- [ ] Metrics stored in run and visible
- [ ] Temporal DerivedAsset auto-created with 14-day TTL
- [ ] Promote converts to permanent (TTL removed)
- [ ] interaction_logs has full audit trail
- [ ] MinIO shows proper folder structure

---

## Related Documents

- [Architecture Details](./ARCHITECTURE.md)
- [Implementation Changelog](./CHANGELOG.md)
