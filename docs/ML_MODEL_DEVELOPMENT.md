# ML Model Development Workspace

## Overview

The ML Model Development workspace is a comprehensive feature for managing machine learning model lifecycles in NEX. It supports four model families:

1. **Forecasting** - Time series prediction models
2. **Pricing** - Price optimization and elasticity models
3. **Next Best Action (NBA)** - Recommendation and uplift models
4. **Location Scoring** - Site selection and location analysis models

## Architecture

### Backend Components

**Database Tables (6 new tables):**
- `ml_recipe` - Recipe definitions (templates/manifests)
- `ml_recipe_version` - Version history with manifests
- `ml_model` - Registered ML model artifacts
- `ml_run` - Training/evaluation run records
- `ml_monitor_snapshot` - Time-series monitoring data
- `ml_synthetic_example` - Example datasets for recipes

**Domain Structure:**
- `backend/domains/ml_development/models.py` - Pydantic models
- `backend/domains/ml_development/service.py` - Business logic layer
- `backend/domains/ml_development/router.py` - FastAPI endpoints

**API Endpoints:**
- `GET /api/ml-development/recipes` - List recipes
- `GET /api/ml-development/recipes/{id}` - Get recipe detail
- `POST /api/ml-development/recipes` - Create recipe
- `PUT /api/ml-development/recipes/{id}` - Update recipe
- `POST /api/ml-development/recipes/{id}/clone` - Clone recipe
- `GET /api/ml-development/recipes/{id}/versions` - List versions
- `POST /api/ml-development/recipes/{id}/versions` - Create new version
- `GET /api/ml-development/models` - List models
- `POST /api/ml-development/models` - Register model
- `GET /api/ml-development/runs` - List runs
- `POST /api/ml-development/runs` - Create run
- `GET /api/ml-development/models/{id}/monitoring` - Get monitoring data
- `POST /api/ml-development/chat` - Chat assistant

### Frontend Components

**Pages:**
- `ModelLibrary.tsx` - Landing page with tabs for Recipes/Models/Runs/Monitoring
- `RecipeDetail.tsx` - Recipe detail with manifest editor and versions
- `ModelDetail.tsx` - Model detail with monitoring dashboards
- `RunDetail.tsx` - Run detail with metrics and logs
- `MLChat.tsx` - Chat-assisted recipe builder

**Routes:**
- `/model-development` - Main library
- `/model-development/recipes/:id` - Recipe detail
- `/model-development/models/:id` - Model detail
- `/model-development/runs/:id` - Run detail
- `/model-development/chat` - Chat assistant

## Setup Instructions

### 1. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This will create the 6 new ML tables in your database.

### 2. Seed Baseline Recipes

```bash
cd backend
python scripts/seed_ml_recipes.py
```

This will create 4 baseline recipes:
- Forecasting Baseline v1
- Pricing Optimization Baseline v1
- Next Best Action Baseline v1
- Location Scoring Baseline v1

### 3. Install Frontend Dependencies

The frontend uses `recharts` for monitoring visualizations. Install if needed:

```bash
cd frontend
npm install recharts
```

### 4. Restart Services

```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

## Usage Guide

### Creating a New Recipe

**Option 1: Using the UI**
1. Navigate to Model Development in the sidebar
2. Click "Recipes" tab
3. View existing baseline recipes
4. Clone a baseline recipe and customize it

**Option 2: Using the Chat Assistant**
1. Navigate to Model Development
2. Click "Build with Chat"
3. Describe your model requirements in natural language
4. The assistant will guide you through recipe creation

### Recipe Inheritance

Recipes follow a 3-level hierarchy:
- **Baseline** - Foundation recipes (provided)
- **Industry** - Industry-specific variants (you create by cloning baseline)
- **Client** - Client-specific customizations (you create by cloning industry)

Each recipe maintains a `parent_id` linking it to its parent.

### Managing Recipe Versions

1. Open a recipe detail page
2. Click "Manifest Editor" tab
3. Click "Edit Manifest"
4. Modify the JSON manifest
5. Click "Save as New Version"

Versions are immutable and follow semantic versioning.

### Registering a Model

1. Navigate to a recipe detail page
2. Ensure the recipe is "approved" status
3. From the Models tab in the main library, create a new model
4. Select the recipe and specific version to use

### Running Training/Evaluation

1. Navigate to Runs tab
2. Create a new run
3. Select recipe, version, and run type (train/eval/backtest)
4. Monitor run status and view metrics when complete

### Monitoring Models

1. Navigate to a model detail page
2. Click "Monitoring" tab
3. View performance metrics over time
4. Check drift metrics and data freshness
5. Review active alerts

## Manifest Schema

All recipes use a standardized manifest JSON schema:

```json
{
  "metadata": {
    "id": "recipe_id",
    "name": "Recipe Name",
    "description": "What this recipe does",
    "model_family": "pricing|next_best_action|location_scoring|forecasting",
    "level": "baseline|industry|client",
    "version": "1.0.0"
  },
  "requirements": {
    "feature_sets": {
      "required": ["feature_set_1"],
      "optional": ["feature_set_2"]
    },
    "grain": "granularity level",
    "labels": ["target_column"],
    "min_history": "data history requirement"
  },
  "pipeline": {
    "stages": [
      {
        "name": "stage_name",
        "type": "quality|feature_prep|training|evaluation|deployment",
        "config": {}
      }
    ]
  },
  "evaluation": {
    "metrics": {
      "metric_name": {
        "target": 0.0,
        "threshold_warning": 0.0,
        "threshold_critical": 0.0
      }
    },
    "validation": {
      "method": "validation_strategy",
      "test_size": "split_size"
    }
  },
  "lineage": {
    "input_features": [],
    "output_features": []
  },
  "deployment": {
    "mode": "batch|realtime",
    "schedule": "cron_expression",
    "endpoint_spec": {}
  },
  "monitoring": {
    "metrics": [],
    "drift": {
      "method": "PSI|KS",
      "threshold": 0.0,
      "features": []
    },
    "freshness": {
      "max_age_hours": 0,
      "features": []
    },
    "alerts": {
      "alert_name": {
        "condition": "expression",
        "severity": "warning|critical"
      }
    }
  }
}
```

## Model Family Specifics

### Forecasting Models
- **Key Metrics**: MAPE, RMSE, MAE, coverage
- **Common Algorithms**: ARIMA, Prophet, LSTM
- **Deployment**: Typically batch (daily/weekly)

### Pricing Models
- **Key Metrics**: revenue_lift, margin_impact, elasticity, calibration
- **Common Techniques**: Elasticity estimation, optimization
- **Deployment**: Batch (weekly) or realtime API

### Next Best Action Models
- **Key Metrics**: uplift, precision@k, incremental_revenue, qini_coefficient
- **Common Techniques**: Uplift modeling, two-model approach
- **Deployment**: Realtime API for recommendations

### Location Scoring Models
- **Key Metrics**: rank_correlation, calibration, hit_rate@k, lift
- **Common Techniques**: Gradient boosting, trade area analysis
- **Deployment**: On-demand batch scoring

## Advanced Features

### Synthetic Examples

Each recipe can have a synthetic example for testing:
- Sample dataset schema
- Sample input rows
- Expected output format
- Example metrics

Access via: `GET /api/ml-development/recipes/{id}/synthetic-example`

### Chat Assistant

The chat assistant (stubbed in v1) helps with:
- Recipe creation guidance
- Manifest editing suggestions
- Model family selection
- Best practices recommendations

Access via: `/model-development/chat`

### Monitoring & Alerts

Models can be monitored for:
- **Performance**: Tracking key metrics over time
- **Drift**: Feature and prediction distribution changes
- **Freshness**: Data recency checks
- **Alerts**: Threshold-based notifications

Monitoring snapshots are captured periodically and displayed as time series.

## API Reference

### Recipe Operations

**List Recipes**
```bash
GET /api/ml-development/recipes?model_family=pricing&level=baseline&status=approved
```

**Create Recipe**
```bash
POST /api/ml-development/recipes
{
  "name": "My Custom Recipe",
  "model_family": "pricing",
  "level": "industry",
  "parent_id": "recipe_pricing_base",
  "tags": ["retail", "dynamic-pricing"],
  "manifest": {...}
}
```

**Clone Recipe**
```bash
POST /api/ml-development/recipes/{id}/clone?name=My%20Clone
```

### Model Operations

**Register Model**
```bash
POST /api/ml-development/models
{
  "name": "Production Pricing Model",
  "recipe_id": "recipe_pricing_base",
  "recipe_version_id": "ver_pricing_base_v1",
  "owner": "data-science-team"
}
```

**Update Model Status**
```bash
PUT /api/ml-development/models/{id}
{
  "status": "production"
}
```

### Run Operations

**Create Run**
```bash
POST /api/ml-development/runs
{
  "recipe_id": "recipe_pricing_base",
  "recipe_version_id": "ver_pricing_base_v1",
  "run_type": "train",
  "model_id": "model_123"
}
```

**Update Run Results**
```bash
PUT /api/ml-development/runs/{id}
{
  "status": "succeeded",
  "metrics_json": {
    "MAPE": 0.142,
    "RMSE": 45.2
  },
  "artifacts_json": {
    "model_path": "s3://bucket/models/model.pkl"
  }
}
```

### Monitoring Operations

**Create Monitoring Snapshot**
```bash
POST /api/ml-development/models/{id}/monitoring
{
  "performance_metrics_json": {"MAPE": 0.15},
  "drift_metrics_json": {"PSI": 0.08},
  "data_freshness_json": {"last_update": "2024-01-15T10:00:00Z"},
  "alerts_json": {}
}
```

## Troubleshooting

### Migration Issues
If the migration fails, check:
- Database connection string in `.env`
- Existing table conflicts
- Alembic version history

### Frontend Build Issues
If the frontend doesn't build:
```bash
cd frontend
npm install recharts lucide-react react-router-dom
npm run build
```

### API 404 Errors
Ensure the router is registered in `backend/main.py`:
```python
from domains.ml_development.router import router as ml_development_router
app.include_router(ml_development_router, prefix=settings.api_prefix)
```

## Future Enhancements

Potential v2 features:
- Real LLM integration for chat assistant
- Automated hyperparameter tuning
- A/B test management
- Model comparison tools
- Drift detection automation
- Auto-retraining pipelines
- Integration with MLflow/Weights & Biases
- Model explainability dashboards

## Support

For questions or issues:
1. Check this documentation
2. Review seed recipes for examples
3. Use the chat assistant for guidance
4. Check API responses for detailed error messages


