# ML Compute Engine - Phase B Implementation Plan

> **Status:** ✅ Phase 1 (Must Have) Complete  
> **Created:** 2026-01-07  
> **Last Updated:** 2026-01-07  
> **Predecessor:** [GPU Runner Phase A](../gpu-runner/PLAN.md)

## Overview

Evolve the ML Compute Engine from "GPU-backed experimentation" to a **reliable, cost-aware, reusable platform** with RunPod integration.

### Goals

- **Cost Awareness** - Know what every run costs before and after
- **Reuse-Before-Rerun** - Don't waste money on duplicate work
- **Reliability** - Auto-retry failed GPU jobs
- **RunPod Integration** - Cloud GPU execution via RunPod
- **Visibility** - Clear job states and failure reasons

### Non-Goals (Deferred)

- Multi-tenancy (Phase C)
- Agent-driven workflows (Phase C)
- Governance/policy hooks (Phase C)
- K8s Gateway (can use RunPod instead)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ML Compute Engine                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Pre-Run Decision Engine                           │    │
│  │  ┌────────────────────────────────────────────────────────────────┐ │    │
│  │  │ POST /model-runs/plan                                          │ │    │
│  │  │  → Check similarity hash                                       │ │    │
│  │  │  → Find matching runs                                          │ │    │
│  │  │  → Return REUSE_RECOMMENDED or PROCEED                         │ │    │
│  │  │  → Include cost estimate                                       │ │    │
│  │  └────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Run State Machine                                 │    │
│  │                                                                      │    │
│  │   QUEUED → SCHEDULED → RUNNING → SUCCEEDED                          │    │
│  │              ↓           ↓                                          │    │
│  │           FAILED ←── RETRYING ──→ (back to SCHEDULED)               │    │
│  │              ↓                                                       │    │
│  │          CANCELLED                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Compute Adapters                                  │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │    │
│  │  │  Local   │  │   SSH    │  │  RunPod  │  │   K8s    │           │    │
│  │  │ (dev)    │  │  (PoC)   │  │ (primary)│  │ (future) │           │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Cost Tracking                                     │    │
│  │  • Estimate at submission (GPU type × max runtime)                  │    │
│  │  • Actual at completion (runtime × hourly rate)                     │    │
│  │  • Visible in UI and API                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: MUST HAVE (MVP)

| # | Feature | Description | Effort |
|---|---------|-------------|--------|
| 1.1 | **Cost Tracking** | Estimate + actual cost per run | 1 day |
| 1.2 | **Reuse-Before-Rerun** | Similarity hash, find matches, recommend | 2 days |
| 1.3 | **Retry Logic** | Configurable retries, retry_count tracking | 1 day |
| 1.4 | **State Machine** | Clear states, failure reasons, transitions | 1 day |
| 1.5 | **RunPod Adapter** | Cloud GPU execution via RunPod API | 2 days |

**Total: ~7 days**

### Phase 2: SHOULD HAVE

| # | Feature | Description | Effort |
|---|---------|-------------|--------|
| 2.1 | **Scheduled Runs** | Cron-style recurring runs | 2 days |
| 2.2 | **Asset Versioning** | History, replaced_by tracking | 1 day |
| 2.3 | **Run Comparison** | Compare metrics across runs | 1 day |
| 2.4 | **Drift Detection** | Basic statistical checks on outputs | 2 days |

**Total: ~6 days**

### Phase 3: NICE TO HAVE

| # | Feature | Description | Effort |
|---|---------|-------------|--------|
| 3.1 | **Multi-Tenancy** | Users, tenants, quotas | 3 days |
| 3.2 | **Agent Workflows** | Chat as planner, decision loops | 3 days |
| 3.3 | **Governance** | Policy hooks, audit | 2 days |
| 3.4 | **Budget Enforcement** | Hard limits, approvals | 1 day |

**Total: ~9 days**

---

## Database Schema Changes

### Migration: `021_add_phase_b.py`

#### 1. Extend `ml_run`

```sql
-- Cost tracking
ALTER TABLE ml_run ADD COLUMN estimated_cost_usd NUMERIC(10,4);
ALTER TABLE ml_run ADD COLUMN actual_cost_usd NUMERIC(10,4);
ALTER TABLE ml_run ADD COLUMN gpu_type VARCHAR(100);
ALTER TABLE ml_run ADD COLUMN runtime_seconds INTEGER;

-- Reuse tracking
ALTER TABLE ml_run ADD COLUMN similarity_hash VARCHAR(64);
ALTER TABLE ml_run ADD COLUMN reused_from_run_id VARCHAR(255);

-- Retry tracking
ALTER TABLE ml_run ADD COLUMN retry_count INTEGER DEFAULT 0;
ALTER TABLE ml_run ADD COLUMN max_retries INTEGER DEFAULT 2;
ALTER TABLE ml_run ADD COLUMN failure_reason TEXT;
ALTER TABLE ml_run ADD COLUMN failure_type VARCHAR(50);  -- 'infra' or 'model'

-- Lineage
ALTER TABLE ml_run ADD COLUMN parent_run_id VARCHAR(255);
```

#### 2. Extend `ml_derived_assets`

```sql
ALTER TABLE ml_derived_assets ADD COLUMN confidence_score NUMERIC(5,4);
ALTER TABLE ml_derived_assets ADD COLUMN replaced_by_asset_id UUID;
ALTER TABLE ml_derived_assets ADD COLUMN version_number INTEGER DEFAULT 1;
```

#### 3. New: `gpu_pricing` (reference table)

```sql
CREATE TABLE gpu_pricing (
    id VARCHAR(100) PRIMARY KEY,          -- e.g., 'runpod_a100'
    provider VARCHAR(50) NOT NULL,         -- 'runpod', 'local', 'ssh'
    gpu_type VARCHAR(100) NOT NULL,        -- 'NVIDIA A100', 'RTX 4090'
    hourly_rate_usd NUMERIC(10,4) NOT NULL,
    memory_gb INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4. New: `run_schedules` (Phase 2)

```sql
CREATE TABLE run_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    recipe_id VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(100),
    parameters JSONB DEFAULT '{}',
    cron_expression VARCHAR(100) NOT NULL,  -- e.g., '0 9 * * 1' (Monday 9am)
    is_active BOOLEAN DEFAULT TRUE,
    last_run_id VARCHAR(255),
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API Endpoints

### Phase 1 APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ml-development/runs/plan` | Pre-run decision (reuse vs run) |
| GET | `/api/v1/ml-development/runs/{id}/cost` | Get cost breakdown |
| POST | `/api/v1/ml-development/runs/{id}/retry` | Manual retry |
| GET | `/api/v1/gpu-pricing` | List GPU pricing options |

### Phase 2 APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/schedules` | Create scheduled run |
| GET | `/api/v1/schedules` | List schedules |
| DELETE | `/api/v1/schedules/{id}` | Delete schedule |
| GET | `/api/v1/ml-development/runs/compare` | Compare multiple runs |
| GET | `/api/v1/ml-development/assets/{id}/history` | Asset version history |

---

## File Structure (New/Modified)

```
backend/
├── services/
│   ├── compute/
│   │   ├── runpod_adapter.py      # NEW - RunPod integration
│   │   └── ...
│   ├── cost_tracker.py            # NEW - Cost estimation/tracking
│   ├── reuse_engine.py            # NEW - Similarity matching
│   └── scheduler.py               # NEW (Phase 2)
│
├── domains/
│   └── ml_development/
│       ├── router.py              # MODIFIED - new endpoints
│       ├── service.py             # MODIFIED - cost, reuse logic
│       └── state_machine.py       # NEW - run state transitions
│
├── migrations/
│   └── versions/
│       └── 021_add_phase_b.py     # NEW
│
└── tests/
    ├── test_cost_tracker.py       # NEW
    ├── test_reuse_engine.py       # NEW
    ├── test_runpod_adapter.py     # NEW
    └── test_state_machine.py      # NEW
```

---

## RunPod Configuration

```python
# core/config.py additions
runpod_api_key: Optional[str] = None
runpod_default_gpu: str = "NVIDIA RTX A4000"
runpod_template_id: Optional[str] = None  # Pre-configured template
```

```yaml
# docker-compose.yml environment
- RUNPOD_API_KEY=${RUNPOD_API_KEY:-}
- RUNPOD_DEFAULT_GPU=${RUNPOD_DEFAULT_GPU:-NVIDIA RTX A4000}
```

---

## Cost Calculation

### Estimation (at submit)
```python
estimated_cost = (max_runtime_hours) × (gpu_hourly_rate)
```

### Actual (at completion)
```python
actual_cost = (runtime_seconds / 3600) × (gpu_hourly_rate)
```

### Default GPU Pricing (seeded)
| Provider | GPU | $/hour |
|----------|-----|--------|
| runpod | RTX A4000 | $0.20 |
| runpod | RTX A5000 | $0.30 |
| runpod | A100 40GB | $1.09 |
| runpod | A100 80GB | $1.69 |
| local | any | $0.00 |

---

## Similarity Hash Algorithm

```python
def compute_similarity_hash(recipe_id: str, dataset_version_id: str, parameters: dict) -> str:
    """
    Create a deterministic hash for run deduplication.
    
    Same hash = same inputs = candidate for reuse.
    """
    canonical = {
        "recipe_id": recipe_id,
        "dataset_version_id": dataset_version_id,
        "parameters": json.dumps(parameters, sort_keys=True)
    }
    content = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

---

## State Machine

```
        ┌─────────┐
        │ QUEUED  │ (initial state)
        └────┬────┘
             │ scheduler picks up
             ▼
        ┌─────────┐
        │SCHEDULED│ (assigned to compute)
        └────┬────┘
             │ container starts
             ▼
        ┌─────────┐
        │ RUNNING │
        └────┬────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌───────┐ ┌───────┐ ┌────────┐
│SUCCEED│ │FAILED │ │RETRYING│
└───────┘ └───┬───┘ └────┬───┘
              │          │
              │    retry_count < max?
              │          │ yes
              │          └──────► SCHEDULED
              │          │ no
              └──────────┴──────► FAILED (final)
```

---

## Acceptance Criteria

### Phase 1 (Must Have)
- [ ] `POST /runs/plan` returns reuse recommendation with confidence
- [ ] Cost estimate shown before run starts
- [ ] Actual cost recorded after completion
- [ ] Failed runs auto-retry up to max_retries
- [ ] Clear failure_type (infra vs model)
- [ ] RunPod adapter can submit and track jobs
- [ ] All states visible in UI

### Phase 2 (Should Have)
- [ ] Scheduled runs execute on cron
- [ ] Asset history shows version chain
- [ ] Run comparison shows metrics side-by-side

### Phase 3 (Nice to Have)
- [ ] Multiple tenants with isolation
- [ ] Agent can decide reuse vs rerun
- [ ] Policy hooks block unapproved runs

---

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `test_cost_tracker.py` | Estimation, actual calculation, pricing lookup |
| `test_reuse_engine.py` | Hash generation, match finding, confidence |
| `test_runpod_adapter.py` | API mocking, job lifecycle |
| `test_state_machine.py` | State transitions, retry logic |
| `test_phase_b_integration.py` | End-to-end workflow |

---

## Implementation Order

| Step | Task | Dependencies |
|------|------|--------------|
| 1 | Create migration 021 | None |
| 2 | Seed GPU pricing table | Migration |
| 3 | Implement cost_tracker service | Migration |
| 4 | Implement reuse_engine service | Migration |
| 5 | Implement state_machine | Migration |
| 6 | Implement RunPodAdapter | None |
| 7 | Update ml_development router | Steps 3-6 |
| 8 | Write tests | Steps 3-7 |
| 9 | Update frontend (optional) | Step 7 |
| 10 | Update documentation | All |

---

## Related Documents

- [Phase A Plan](../gpu-runner/PLAN.md)
- [Phase B Changelog](./CHANGELOG.md)
- [User Guide](../../guides/ML_COMPUTE_ENGINE.md) - How to use this feature
