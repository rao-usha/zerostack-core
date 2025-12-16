# Evaluation Packs - Setup & Testing Guide

## ✅ What's Been Implemented

### Backend (100% Complete)
- ✅ Database models for 5 tables
- ✅ Alembic migration
- ✅ Pydantic models with full type safety
- ✅ Service layer with execution engine
- ✅ REST API with 15 endpoints
- ✅ Seed data with 4 baseline packs
- ✅ Router registered in main.py

### Frontend (75% Complete)
- ✅ Evaluation Packs tab added to Model Library
- ✅ Pack listing with filters
- ⏳ Pack Detail page (needs creation)
- ⏳ Recipe Detail integration (needs pack attachment UI)
- ⏳ Run Detail integration (needs results display)
- ⏳ Model Detail integration (needs monitoring display)

---

## 🚀 Setup Instructions

### Step 1: Run Database Migration

```bash
# Run the migration to create evaluation pack tables
docker exec nex-backend-dev alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 009 -> 010, add evaluation packs
```

### Step 2: Seed Evaluation Packs

```bash
# Seed the 4 baseline evaluation packs
docker exec nex-backend-dev python scripts/seed_evaluation_packs.py
```

**Expected Output:**
```
✓ Successfully seeded 4 evaluation packs:
  - Forecasting Standard Evaluation v1
  - Pricing Standard Evaluation v1
  - NBA Standard Evaluation v1
  - Location Scoring Standard Evaluation v1
```

### Step 3: Verify Backend API

```bash
# Test the evaluation packs API
curl http://localhost:8000/api/v1/evaluation-packs
```

**Expected Response:**
```json
{
  "packs": [
    {
      "id": "pack_forecasting_standard",
      "name": "Forecasting Standard Evaluation v1",
      "model_family": "forecasting",
      "status": "approved",
      "tags": ["standard", "time-series", "baseline"],
      "created_at": "2025-12-16T...",
      "updated_at": "2025-12-16T..."
    },
    ...3 more packs...
  ],
  "total": 4
}
```

### Step 4: Test Frontend

```bash
# Open Model Development in browser
start http://localhost:3000/model-development
```

1. You should see a new **"Evaluation Packs"** tab (with CheckCircle2 icon)
2. Click the tab
3. You should see 4 evaluation pack cards
4. Each card shows:
   - Pack name
   - Status badge (Approved)
   - Model family tag
   - Tags (standard, baseline, etc.)

---

## 📊 Current Status Summary

| Component | Status | Details |
|-----------|--------|---------|
| **Database Schema** | ✅ Complete | 5 tables created |
| **Backend API** | ✅ Complete | 15 endpoints working |
| **Seed Data** | ✅ Complete | 4 packs seeded |
| **Pack Library UI** | ✅ Complete | Tab + list view |
| **Pack Detail Page** | ⏳ Pending | Needs creation |
| **Recipe Integration** | ⏳ Pending | Attach packs UI |
| **Run Integration** | ⏳ Pending | Results display |
| **Model Integration** | ⏳ Pending | Monitoring snapshots |

---

## 🧪 API Testing Examples

### List Packs with Filters
```bash
# Filter by model family
curl "http://localhost:8000/api/v1/evaluation-packs?model_family=forecasting"

# Filter by status
curl "http://localhost:8000/api/v1/evaluation-packs?status=approved"

# Search
curl "http://localhost:8000/api/v1/evaluation-packs?search=forecasting"
```

### Get Pack Details
```bash
curl http://localhost:8000/api/v1/evaluation-packs/pack_forecasting_standard
```

### Get Pack Versions
```bash
curl http://localhost:8000/api/v1/evaluation-packs/pack_forecasting_standard/versions
```

### Attach Pack to Recipe
```bash
curl -X POST http://localhost:8000/api/v1/evaluation-packs/recipes/recipe_forecasting_base/attach \
  -H "Content-Type: application/json" \
  -d '{
    "recipe_id": "recipe_forecasting_base",
    "pack_id": "pack_forecasting_standard"
  }'
```

### Execute Pack on Run
```bash
# First, get a run ID from your existing runs
curl http://localhost:8000/api/v1/ml-development/runs

# Then execute a pack on that run (mocked evaluation)
curl -X POST http://localhost:8000/api/v1/evaluation-packs/execute \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "YOUR_RUN_ID",
    "pack_id": "pack_forecasting_standard",
    "pack_version_id": "ver_pack_forecasting_standard_v1"
  }'
```

### Get Evaluation Results for a Run
```bash
curl http://localhost:8000/api/v1/evaluation-packs/runs/YOUR_RUN_ID/results
```

### Create Monitoring Snapshot
```bash
# First, get a model ID
curl http://localhost:8000/api/v1/ml-development/models

# Create monitoring snapshot (mocked evaluation)
curl -X POST http://localhost:8000/api/v1/evaluation-packs/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "YOUR_MODEL_ID",
    "pack_id": "pack_forecasting_standard",
    "pack_version_id": "ver_pack_forecasting_standard_v1"
  }'
```

### Get Model Monitoring Snapshots
```bash
curl http://localhost:8000/api/v1/evaluation-packs/models/YOUR_MODEL_ID/snapshots
```

---

## 🎯 Remaining Frontend Tasks

### Task 1: Create Evaluation Pack Detail Page

**File:** `frontend/src/pages/EvaluationPackDetail.tsx`

**Features Needed:**
- Overview tab: Show pack metadata, metrics, thresholds
- Pack Definition tab: JSON editor (similar to Recipe Detail manifest editor)
- Versions tab: Version history with diffs
- Test Run tab: Execute pack on a selected run_id
- Actions: Save new version, Approve, Clone

**Route:** `/model-development/evaluation-packs/:id`

### Task 2: Integrate Packs into Recipe Detail

**File:** `frontend/src/pages/RecipeDetail.tsx`

**Changes Needed:**
- Add "Evaluation Packs" section in Overview tab
- Show attached packs with badges
- Button to "Attach Pack" (opens modal)
- Modal lists available packs, allows selection
- Shows pack summary (metrics + thresholds)
- Button to detach pack

**API Calls:**
- `GET /api/v1/evaluation-packs/recipes/{recipe_id}/packs` - List attached packs
- `POST /api/v1/evaluation-packs/recipes/{recipe_id}/attach` - Attach pack
- `DELETE /api/v1/evaluation-packs/recipes/{recipe_id}/detach/{pack_id}` - Detach

### Task 3: Integrate Results into Run Detail

**File:** `frontend/src/pages/RunDetail.tsx`

**Changes Needed:**
- Add "Evaluation Results" panel
- Show all evaluation results for this run
- Display:
  - Pack name
  - Overall status (Pass/Warn/Fail badge)
  - Metrics table (metric name, actual value, threshold, status)
  - Summary text
- Button to "Re-run Evaluation Packs"

**API Calls:**
- `GET /api/v1/evaluation-packs/runs/{run_id}/results` - Get results
- `POST /api/v1/evaluation-packs/execute` - Execute pack

### Task 4: Integrate Monitoring into Model Detail

**File:** `frontend/src/pages/ModelDetail.tsx`

**Changes Needed:**
- Add "Evaluation Pack Monitoring" section in Monitoring tab
- Show:
  - Time series chart of pass/warn/fail counts (mock OK)
  - Last evaluation timestamp
  - Top failing metrics
  - List of snapshots with status badges
- Button to "Run Evaluation Now"

**API Calls:**
- `GET /api/v1/evaluation-packs/models/{model_id}/snapshots` - Get snapshots
- `POST /api/v1/evaluation-packs/monitor` - Create new snapshot

---

## 📦 Pack JSON Schema Reference

Each evaluation pack version contains a `pack_json` with this structure:

```typescript
interface PackDefinition {
  id: string
  name: string
  model_family: 'forecasting' | 'pricing' | 'next_best_action' | 'location_scoring'
  description: string
  metrics: MetricDefinition[]
  slices?: SliceDefinition[]
  comparators?: ComparatorDefinition[]
  economic_mapping?: EconomicMapping[]
  outputs?: { artifacts: string[], reports: string[] }
}

interface MetricDefinition {
  key: string
  display_name: string
  compute: string  // e.g. "MAPE", "RMSE", "uplift"
  thresholds: {
    promote?: number  // Pass threshold
    warn?: number     // Warning threshold
    fail?: number     // Fail threshold
  }
  direction: 'higher_is_better' | 'lower_is_better'
}

interface SliceDefinition {
  dimension: string
  values?: string[]  // null = all values
}

interface ComparatorDefinition {
  type: 'baseline' | 'prior_model' | 'rules_engine'
  reference_id?: string
}

interface EconomicMapping {
  metric_key: string
  dollar_per_unit: number
  unit_label: string
}
```

---

## 🔧 Troubleshooting

### Issue: "Table already exists" error
**Solution:** Drop and recreate the tables:
```bash
docker exec nex-backend-dev alembic downgrade -1
docker exec nex-backend-dev alembic upgrade head
```

### Issue: "Pack not found" when clicking
**Solution:** Ensure seed script ran successfully:
```bash
docker exec nex-backend-dev python scripts/seed_evaluation_packs.py
```

### Issue: Frontend tab not showing
**Solution:** 
1. Check browser console for errors
2. Ensure backend is restarted: `docker restart nex-backend-dev`
3. Hard refresh browser: `Ctrl + Shift + R`

### Issue: API returns 404
**Solution:** Check that router is registered in `main.py`:
```python
from domains.evaluation_packs.router import router as evaluation_packs_router
app.include_router(evaluation_packs_router, prefix=settings.api_prefix)
```

---

## 📝 Next Steps

1. **Test the current implementation:**
   - Run migrations
   - Seed data
   - Verify backend API
   - Check frontend tab

2. **Complete remaining frontend:**
   - Create Evaluation Pack Detail page
   - Integrate into Recipe, Run, and Model pages

3. **End-to-end testing:**
   - Create pack → attach to recipe → run training → execute evaluation → view results → see monitoring

---

## 💡 Tips for Frontend Development

1. **Follow existing patterns:**
   - Look at `RecipeDetail.tsx` for tab structure
   - Look at `RunDetail.tsx` for results display
   - Use same styling (colors, spacing, borders)

2. **Mock evaluation results structure:**
```json
{
  "id": "eval_xxx",
  "run_id": "run_xxx",
  "pack_id": "pack_forecasting_standard",
  "status": "pass",
  "executed_at": "2025-12-16T...",
  "summary_text": "Evaluation PASS: 4/5 metrics passed, 1 warnings, 0 failures",
  "results_json": {
    "metrics": [
      {
        "key": "MAPE",
        "display_name": "Mean Absolute Percentage Error",
        "actual_value": 0.14,
        "thresholds": { "promote": 0.15, "warn": 0.25, "fail": 0.40 },
        "status": "pass",
        "direction": "lower_is_better"
      }
    ]
  }
}
```

3. **Status colors:**
   - Pass: `#10b981` (green)
   - Warn: `#fbbf24` (yellow)
   - Fail: `#ef4444` (red)

---

## ✨ Features Highlights

✅ **Versioned Packs** - Full audit trail of pack changes
✅ **Flexible Thresholds** - Promote/Warn/Fail levels per metric
✅ **Slice Analysis** - Evaluate by segments (v1 structure ready)
✅ **Comparators** - Compare against baselines/prior models
✅ **Economic Mapping** - Translate metrics to dollars
✅ **Monitoring Ready** - Time-series snapshots for tracking
✅ **Reusable** - Attach same pack to multiple recipes
✅ **Cloneable** - Easy customization from baselines

Ready to test! 🎉

