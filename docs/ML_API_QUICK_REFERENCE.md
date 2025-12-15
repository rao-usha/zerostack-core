# ML Model Development - API Quick Reference

## Base URL
All endpoints are prefixed with `/api/ml-development`

## Authentication
Follow NEX standard authentication (not yet implemented in v1)

---

## 📚 Recipes

### List Recipes
```http
GET /api/ml-development/recipes
Query Params:
  - model_family: pricing|next_best_action|location_scoring|forecasting
  - level: baseline|industry|client
  - status: draft|approved|archived
  - limit: int (default 100, max 500)
  - offset: int (default 0)
```

### Get Recipe
```http
GET /api/ml-development/recipes/{recipe_id}
```

### Create Recipe
```http
POST /api/ml-development/recipes
Body: {
  "name": "string",
  "model_family": "pricing|next_best_action|location_scoring|forecasting",
  "level": "baseline|industry|client",
  "parent_id": "string|null",
  "tags": ["string"],
  "manifest": {...}
}
```

### Update Recipe
```http
PUT /api/ml-development/recipes/{recipe_id}
Body: {
  "name": "string",
  "status": "draft|approved|archived",
  "tags": ["string"]
}
```

### Delete Recipe
```http
DELETE /api/ml-development/recipes/{recipe_id}
```

### Clone Recipe
```http
POST /api/ml-development/recipes/{recipe_id}/clone
Query Params:
  - name: string (required)
```

---

## 📝 Recipe Versions

### List Versions
```http
GET /api/ml-development/recipes/{recipe_id}/versions
```

### Get Version
```http
GET /api/ml-development/recipes/{recipe_id}/versions/{version_id}
```

### Create Version
```http
POST /api/ml-development/recipes/{recipe_id}/versions
Body: {
  "recipe_id": "string",
  "manifest_json": {...},
  "change_note": "string",
  "created_by": "string"
}
```

---

## 📦 Models

### List Models
```http
GET /api/ml-development/models
Query Params:
  - model_family: pricing|next_best_action|location_scoring|forecasting
  - status: draft|staging|production|retired
  - limit: int (default 100, max 500)
  - offset: int (default 0)
```

### Get Model
```http
GET /api/ml-development/models/{model_id}
```

### Register Model
```http
POST /api/ml-development/models
Body: {
  "name": "string",
  "recipe_id": "string",
  "recipe_version_id": "string",
  "owner": "string"
}
```

### Update Model
```http
PUT /api/ml-development/models/{model_id}
Body: {
  "name": "string",
  "status": "draft|staging|production|retired",
  "owner": "string"
}
```

---

## 🏃 Runs

### List Runs
```http
GET /api/ml-development/runs
Query Params:
  - model_id: string
  - recipe_id: string
  - status: queued|running|succeeded|failed
  - limit: int (default 100, max 500)
  - offset: int (default 0)
```

### Get Run
```http
GET /api/ml-development/runs/{run_id}
```

### Create Run
```http
POST /api/ml-development/runs
Body: {
  "recipe_id": "string",
  "recipe_version_id": "string",
  "run_type": "train|eval|backtest",
  "model_id": "string|null"
}
```

### Update Run
```http
PUT /api/ml-development/runs/{run_id}
Body: {
  "status": "queued|running|succeeded|failed",
  "metrics_json": {...},
  "artifacts_json": {...},
  "logs_text": "string"
}
```

---

## 📊 Monitoring

### List Monitoring Snapshots
```http
GET /api/ml-development/models/{model_id}/monitoring
Query Params:
  - limit: int (default 100, max 500)
  - offset: int (default 0)
```

### Create Monitoring Snapshot
```http
POST /api/ml-development/models/{model_id}/monitoring
Body: {
  "model_id": "string",
  "performance_metrics_json": {...},
  "drift_metrics_json": {...},
  "data_freshness_json": {...},
  "alerts_json": {...}
}
```

---

## 🧪 Synthetic Examples

### Get Synthetic Example
```http
GET /api/ml-development/recipes/{recipe_id}/synthetic-example
```

### Create Synthetic Example
```http
POST /api/ml-development/recipes/{recipe_id}/synthetic-example
Body: {
  "recipe_id": "string",
  "dataset_schema_json": {...},
  "sample_rows_json": [...],
  "example_run_json": {...}
}
```

---

## 💬 Chat Assistant

### Chat
```http
POST /api/ml-development/chat
Body: {
  "message": "string",
  "context": {...},
  "recipe_id": "string|null"
}
```

---

## 📋 Response Formats

### Recipe Response
```json
{
  "id": "recipe_pricing_base",
  "name": "Pricing Baseline v1",
  "model_family": "pricing",
  "level": "baseline",
  "status": "approved",
  "parent_id": null,
  "tags": ["baseline", "optimization"],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Recipe Version Response
```json
{
  "version_id": "ver_pricing_base_v1",
  "recipe_id": "recipe_pricing_base",
  "version_number": "1.0.0",
  "manifest_json": {...},
  "diff_from_prev": null,
  "created_by": "system",
  "created_at": "2024-01-15T10:00:00Z",
  "change_note": "Initial version"
}
```

### Model Response
```json
{
  "id": "model_abc123",
  "name": "Production Pricing Model",
  "model_family": "pricing",
  "recipe_id": "recipe_pricing_base",
  "recipe_version_id": "ver_pricing_base_v1",
  "status": "production",
  "owner": "data-science-team",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-16T14:30:00Z"
}
```

### Run Response
```json
{
  "id": "run_xyz789",
  "model_id": "model_abc123",
  "recipe_id": "recipe_pricing_base",
  "recipe_version_id": "ver_pricing_base_v1",
  "run_type": "train",
  "status": "succeeded",
  "started_at": "2024-01-15T10:00:00Z",
  "finished_at": "2024-01-15T10:15:00Z",
  "metrics_json": {
    "revenue_lift": 0.042,
    "margin_impact": 0.068
  },
  "artifacts_json": {
    "model_path": "s3://bucket/models/model.pkl"
  },
  "logs_text": "Training started...\nEpoch 1/10..."
}
```

### Monitoring Snapshot Response
```json
{
  "id": "snap_def456",
  "model_id": "model_abc123",
  "captured_at": "2024-01-15T12:00:00Z",
  "performance_metrics_json": {
    "revenue_lift": 0.038,
    "MAPE": 0.15
  },
  "drift_metrics_json": {
    "PSI": 0.08
  },
  "data_freshness_json": {
    "last_update": "2024-01-15T11:00:00Z"
  },
  "alerts_json": {}
}
```

### List Response Format
```json
{
  "recipes": [...],  // or "models", "runs"
  "total": 42
}
```

---

## 🔑 Enums Reference

### Model Families
- `pricing`
- `next_best_action`
- `location_scoring`
- `forecasting`

### Recipe Levels
- `baseline` - Foundation recipes
- `industry` - Industry-specific variants
- `client` - Client-specific customizations

### Recipe Statuses
- `draft` - Work in progress
- `approved` - Ready for use
- `archived` - No longer active

### Model Statuses
- `draft` - Development
- `staging` - Pre-production testing
- `production` - Live deployment
- `retired` - No longer in use

### Run Types
- `train` - Model training
- `eval` - Model evaluation
- `backtest` - Historical backtesting

### Run Statuses
- `queued` - Waiting to start
- `running` - In progress
- `succeeded` - Completed successfully
- `failed` - Completed with errors

---

## 🚨 Error Responses

### 404 Not Found
```json
{
  "detail": "Recipe not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid model_family value"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 💡 Usage Examples

### Example 1: Create and Deploy a Pricing Model
```bash
# 1. List available recipes
curl http://localhost:8000/api/ml-development/recipes?model_family=pricing

# 2. Clone baseline recipe
curl -X POST http://localhost:8000/api/ml-development/recipes/recipe_pricing_base/clone?name=Retail%20Pricing%20v1

# 3. Create new version with custom manifest
curl -X POST http://localhost:8000/api/ml-development/recipes/{new_recipe_id}/versions \
  -H "Content-Type: application/json" \
  -d '{"recipe_id": "{new_recipe_id}", "manifest_json": {...}, "change_note": "Added retail features"}'

# 4. Approve recipe
curl -X PUT http://localhost:8000/api/ml-development/recipes/{new_recipe_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}'

# 5. Register model
curl -X POST http://localhost:8000/api/ml-development/models \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Retail Pricing", "recipe_id": "{new_recipe_id}", "recipe_version_id": "{version_id}", "owner": "team"}'

# 6. Create training run
curl -X POST http://localhost:8000/api/ml-development/runs \
  -H "Content-Type: application/json" \
  -d '{"recipe_id": "{new_recipe_id}", "recipe_version_id": "{version_id}", "run_type": "train", "model_id": "{model_id}"}'

# 7. Update run with results
curl -X PUT http://localhost:8000/api/ml-development/runs/{run_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "succeeded", "metrics_json": {"revenue_lift": 0.045}}'

# 8. Promote model to production
curl -X PUT http://localhost:8000/api/ml-development/models/{model_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "production"}'

# 9. Create monitoring snapshot
curl -X POST http://localhost:8000/api/ml-development/models/{model_id}/monitoring \
  -H "Content-Type: application/json" \
  -d '{"model_id": "{model_id}", "performance_metrics_json": {"revenue_lift": 0.042}, ...}'
```

### Example 2: Query Runs for a Model
```bash
# Get all successful runs for a model
curl http://localhost:8000/api/ml-development/runs?model_id={model_id}&status=succeeded

# Get run details
curl http://localhost:8000/api/ml-development/runs/{run_id}
```

### Example 3: Monitor Model Performance
```bash
# Get recent monitoring snapshots
curl http://localhost:8000/api/ml-development/models/{model_id}/monitoring?limit=10

# Get model details
curl http://localhost:8000/api/ml-development/models/{model_id}
```

---

## 🔗 Related Routes (Frontend)

- `/model-development` - Model library (landing)
- `/model-development/recipes/:id` - Recipe detail
- `/model-development/models/:id` - Model detail
- `/model-development/runs/:id` - Run detail
- `/model-development/chat` - Chat assistant

---

## 📖 See Also

- `docs/ML_MODEL_DEVELOPMENT.md` - Full user guide
- `ML_MODEL_DEVELOPMENT_IMPLEMENTATION.md` - Implementation details
- `backend/domains/ml_development/models.py` - Pydantic model definitions
- `backend/domains/ml_development/router.py` - Endpoint implementations


