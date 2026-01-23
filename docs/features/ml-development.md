# ML Model Development

A complete ML Model Development workspace supporting 4 model families with recipes, versioning, monitoring, and evaluation packs.

## Overview

The ML Development workspace provides:
- **Recipe Management**: Templates defining ML workflows with 3-level inheritance
- **Model Registry**: Track trained model artifacts with lifecycle management
- **Run Tracking**: Monitor training, evaluation, and backtest runs
- **Monitoring**: Time-series performance and drift tracking
- **Evaluation Packs**: Standardized evaluation criteria per model family
- **Chat Assistant**: AI-guided recipe building

## Quick Start

### 1. Run Migration
```bash
cd backend
alembic upgrade head
```

### 2. Seed Baseline Recipes
```bash
cd backend
python scripts/seed_ml_recipes.py
python scripts/seed_evaluation_packs.py
```

### 3. Access the Feature
1. Open the app at `http://localhost:3000`
2. Click **"Model Development"** in sidebar
3. Explore the 4 baseline recipes

---

## Model Families

| Family | Description | Use Cases |
|--------|-------------|-----------|
| **Forecasting** | Time series predictions | Demand forecasting, sales prediction |
| **Pricing** | Price optimization | Elasticity modeling, margin optimization |
| **Next Best Action** | Recommendation engines | Uplift modeling, campaign optimization |
| **Location Scoring** | Site selection | Trade area analysis, expansion planning |

---

## Core Concepts

### Recipes (Manifests)

Templates defining ML workflows:

```json
{
  "metadata": { "name": "...", "version": "..." },
  "requirements": { "features": [...], "grain": "...", "labels": [...] },
  "pipeline": {
    "quality": { "checks": [...] },
    "feature_prep": { "transformations": [...] },
    "training": { "algorithm": "...", "hyperparameters": {...} },
    "evaluation": { "metrics": [...] },
    "deployment": { "mode": "batch|realtime" }
  },
  "monitoring": { "metrics": [...], "drift_detection": {...} }
}
```

### Recipe Levels

| Level | Description |
|-------|-------------|
| **Baseline** | Battle-tested templates maintained centrally |
| **Industry** | Industry-specific customizations |
| **Client** | Client-specific configurations |

### Models

Trained model instances from recipes:
- Link to specific recipe version
- Status lifecycle: `draft` → `staging` → `production` → `retired`
- Owner assignment and tracking

### Runs

Execution of training/evaluation:
- Types: `train`, `eval`, `backtest`
- Status: `queued` → `running` → `succeeded`/`failed`
- Metrics and artifacts tracking
- Logs storage

### Monitoring

Time-series tracking:
- Performance metrics over time
- Drift detection (PSI/KS)
- Data freshness indicators
- Alert definitions

---

## Evaluation Packs

Standardized evaluation criteria per model family:

### Structure

```json
{
  "metrics": [
    {
      "key": "mape",
      "display_name": "MAPE",
      "thresholds": { "promote": 0.05, "warn": 0.10, "fail": 0.15 },
      "direction": "lower_is_better"
    }
  ],
  "slices": [
    { "dimension": "region", "values": ["US", "EU", "APAC"] }
  ],
  "comparators": [
    { "type": "baseline", "reference_id": "naive_forecast" }
  ],
  "economic_mapping": [
    { "metric_key": "mape", "dollar_per_unit": 10000 }
  ]
}
```

### Baseline Packs

| Pack | Key Metrics |
|------|-------------|
| **Forecasting** | MAPE, RMSE, MAE, forecast_bias, coverage_80 |
| **Pricing** | revenue_lift, margin_impact, elasticity_accuracy |
| **NBA** | uplift, precision_at_10, qini_coefficient |
| **Location Scoring** | rank_correlation, calibration, hit_rate_at_10 |

---

## API Reference

### Recipes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ml-development/recipes` | List recipes (with filters) |
| `POST` | `/api/ml-development/recipes` | Create recipe |
| `POST` | `/api/ml-development/recipes/{id}/clone` | Clone recipe |
| `GET` | `/api/ml-development/recipes/{id}/versions` | List versions |
| `POST` | `/api/ml-development/recipes/{id}/versions` | Create version |

### Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ml-development/models` | List models |
| `POST` | `/api/ml-development/models` | Register model |
| `GET` | `/api/ml-development/models/{id}/monitoring` | Get snapshots |

### Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ml-development/runs` | List runs |
| `POST` | `/api/ml-development/runs` | Create run |

### Evaluation Packs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/evaluation-packs` | List packs |
| `POST` | `/api/v1/evaluation-packs/execute` | Execute pack on run |
| `POST` | `/api/v1/evaluation-packs/recipes/{id}/attach` | Attach to recipe |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ml-development/chat` | Chat with ML assistant |

---

## UI Pages

| Page | Route | Description |
|------|-------|-------------|
| **Model Library** | `/model-development` | Main landing (4 tabs) |
| **Recipe Detail** | `/model-development/recipes/:id` | Recipe config & versions |
| **Model Detail** | `/model-development/models/:id` | Monitoring dashboards |
| **Run Detail** | `/model-development/runs/:id` | Metrics & logs |
| **ML Chat** | `/model-development/chat` | AI assistant |

---

## Usage Scenarios

### Build a Custom Model

1. Go to **Model Development** → **Recipes**
2. Find a baseline recipe (e.g., "Forecasting Baseline v1")
3. Click **Clone Recipe**
4. Edit manifest with custom features
5. Save as new version
6. Click **Approve Recipe**
7. Create model from approved recipe

### Monitor Production Model

1. Go to **Model Development** → **Models**
2. Click on production model
3. View **Monitoring** tab
4. Check performance trends
5. Review drift metrics and alerts

### Run Evaluation

1. Create run with `type: eval`
2. Attach evaluation pack to recipe
3. Execute pack on run results
4. View pass/warn/fail status per metric

---

## Database Tables

| Table | Description |
|-------|-------------|
| `ml_recipe` | Recipe definitions |
| `ml_recipe_version` | Immutable version snapshots |
| `ml_model` | Registered model artifacts |
| `ml_run` | Training/evaluation runs |
| `ml_monitor_snapshot` | Time-series monitoring |
| `evaluation_pack` | Evaluation pack definitions |
| `evaluation_pack_version` | Pack version snapshots |
| `evaluation_result` | Execution results |

---

## Related Documentation

- [ML API Quick Reference](../ML_API_QUICK_REFERENCE.md)
- [GPU Runner Quickstart](../GPU_RUNNER_QUICKSTART.md)
- [API Reference](../api.md)
