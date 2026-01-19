# ML Compute Engine - Phase 2 Roadmap

> **Status:** ✅ Complete  
> **Prerequisites:** Phase B (Must Have) complete and tested  
> **Estimated Effort:** ~6 days  
> **Completed:** 2026-01-09

## Overview

Phase 2 adds **operational features** that make the ML Compute Engine production-ready:
- Schedule recurring runs (daily forecasts)
- Track asset history and versions
- Compare runs side-by-side in UI
- Detect when outputs drift

---

## Features

### 2.1 Scheduled Runs ⏰

**What:** Create cron-style schedules for recurring ML runs

**Use Case:** "Run my forecast every Monday at 9am"

**API:**
```
POST /api/v1/schedules
GET  /api/v1/schedules
GET  /api/v1/schedules/{id}
PUT  /api/v1/schedules/{id}
DELETE /api/v1/schedules/{id}
POST /api/v1/schedules/{id}/trigger  (manual trigger)
```

**Example:**
```json
{
  "name": "Weekly M5 Forecast",
  "recipe_id": "recipe_m5_forecast_v1",
  "dataset_id": "m5_sales",
  "parameters": { "horizon": 28 },
  "cron_expression": "0 9 * * 1",
  "is_active": true
}
```

**Database:** `run_schedules` table (already created in migration 021)

**Implementation:**
- Background scheduler service (APScheduler or similar)
- Tracks `last_run_id`, `last_run_at`, `next_run_at`
- Respects reuse engine (won't duplicate if inputs unchanged)

---

### 2.2 Asset Versioning 📚

**What:** Track history of derived assets over time

**Use Case:** "Show me all versions of this forecast asset"

**API:**
```
GET /api/v1/ml-development/assets/{id}/history
POST /api/v1/ml-development/assets/{id}/rollback
```

**Fields added to `ml_derived_assets`:**
- `version_number` (already in migration 021)
- `replaced_by_asset_id` (already in migration 021)
- `parent_asset_id` (links versions together)

**Example Response:**
```json
{
  "asset_id": "asset_abc",
  "current_version": 3,
  "versions": [
    { "version": 1, "created_at": "2026-01-01", "status": "replaced" },
    { "version": 2, "created_at": "2026-01-08", "status": "replaced" },
    { "version": 3, "created_at": "2026-01-15", "status": "current" }
  ]
}
```

---

### 2.3 Run Comparison UI 📊

**What:** Visual comparison of metrics across runs

**Use Case:** "Compare accuracy between these 3 model versions"

**API:** Already implemented: `GET /runs/compare?run_ids=a,b,c`

**Frontend:**
- Side-by-side table of run parameters
- Metrics comparison with highlighting (best/worst)
- Cost comparison
- Select runs from list to compare

---

### 2.4 Drift Detection 🚨

**What:** Alert when model outputs change significantly

**Use Case:** "Notify me if forecast accuracy drops below 90%"

**API:**
```
POST /api/v1/drift-checks
GET  /api/v1/drift-checks
GET  /api/v1/drift-checks/{id}/alerts
```

**Drift Types:**
- **Metric drift:** Accuracy/RMSE changes beyond threshold
- **Output drift:** Prediction distribution shifts
- **Input drift:** Feature distributions change

**Example:**
```json
{
  "name": "Forecast Accuracy Check",
  "asset_id": "asset_abc",
  "metric": "rmse",
  "threshold": 0.15,
  "comparison": "percentage_increase",
  "alert_on_breach": true
}
```

---

## Implementation Order

| Step | Task | Effort | Dependencies |
|------|------|--------|--------------|
| 1 | Scheduler service | 1 day | None |
| 2 | Schedule CRUD endpoints | 0.5 day | Step 1 |
| 3 | Schedule execution integration | 0.5 day | Steps 1-2 |
| 4 | Asset version tracking | 0.5 day | None |
| 5 | Asset history endpoint | 0.5 day | Step 4 |
| 6 | Run comparison frontend | 1 day | Compare API (done) |
| 7 | Drift check service | 1 day | None |
| 8 | Drift alert system | 0.5 day | Step 7 |
| 9 | Tests & documentation | 0.5 day | All |

**Total: ~6 days**

---

## Database Changes

### New Table: `drift_checks`

```sql
CREATE TABLE drift_checks (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    asset_id UUID REFERENCES ml_derived_assets(id),
    recipe_id VARCHAR(255),
    metric VARCHAR(100) NOT NULL,
    threshold NUMERIC(10,4) NOT NULL,
    comparison VARCHAR(50) NOT NULL,  -- 'absolute', 'percentage_increase', etc.
    baseline_value NUMERIC(10,4),
    latest_value NUMERIC(10,4),
    is_breached BOOLEAN DEFAULT FALSE,
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### New Table: `drift_alerts`

```sql
CREATE TABLE drift_alerts (
    id UUID PRIMARY KEY,
    drift_check_id UUID REFERENCES drift_checks(id),
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    baseline_value NUMERIC(10,4),
    current_value NUMERIC(10,4),
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(255)
);
```

---

## File Structure

```
backend/
├── services/
│   ├── scheduler.py           # NEW - APScheduler integration
│   └── drift_detector.py      # NEW - Drift detection logic
│
├── domains/
│   ├── schedules/             # NEW
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── models.py
│   │
│   └── drift/                 # NEW
│       ├── __init__.py
│       ├── router.py
│       ├── service.py
│       └── models.py
│
├── migrations/
│   └── versions/
│       └── 022_add_phase_2.py # NEW
│
└── tests/
    ├── test_scheduler.py      # NEW
    └── test_drift.py          # NEW
```

---

## Acceptance Criteria

### Scheduled Runs
- [ ] Can create schedule with cron expression
- [ ] Schedules execute at correct times
- [ ] Schedule respects reuse engine
- [ ] Can pause/resume schedules
- [ ] Manual trigger works

### Asset Versioning
- [ ] New assets get version_number = 1
- [ ] Updated assets increment version
- [ ] History endpoint shows all versions
- [ ] Can rollback to previous version

### Run Comparison
- [ ] Frontend shows side-by-side comparison
- [ ] Highlights best/worst metrics
- [ ] Shows cost comparison

### Drift Detection
- [ ] Can configure drift checks
- [ ] Alerts generated when threshold breached
- [ ] Can acknowledge alerts

---

## Configuration

```python
# core/config.py additions
scheduler_enabled: bool = True
scheduler_timezone: str = "UTC"
drift_check_interval_hours: int = 24
```

```yaml
# docker-compose.yml additions
- SCHEDULER_ENABLED=${SCHEDULER_ENABLED:-true}
- SCHEDULER_TIMEZONE=${SCHEDULER_TIMEZONE:-UTC}
```

---

## Testing Strategy

| Feature | Test Approach |
|---------|---------------|
| Scheduler | Mock time, verify executions |
| Asset Versioning | Create/update, verify chain |
| Drift Detection | Generate metrics, verify alerts |

---

## Getting Started with Phase 2

When ready to implement:

```powershell
# 1. Create migration
# backend/migrations/versions/022_add_phase_2.py

# 2. Create scheduler service
# backend/services/scheduler.py

# 3. Create schedule endpoints
# backend/domains/schedules/

# 4. Test
python -m pytest tests/test_scheduler.py -v
```

---

## Questions to Decide Before Starting

1. **Scheduler library:** APScheduler vs Celery vs simple asyncio?
2. **Drift detection frequency:** Per-run vs periodic?
3. **Alert delivery:** In-app only vs email/Slack?
4. **Version retention:** Keep all versions vs max N versions?

---

## Related Documents

- [Phase B Plan](./plans/ml-compute-engine/PLAN.md) - Current phase details
- [Phase B Smoke Test](./PHASE_B_SMOKE_TEST.md) - Test before starting Phase 2
- [User Guide](./guides/ML_COMPUTE_ENGINE.md) - How to use current features
