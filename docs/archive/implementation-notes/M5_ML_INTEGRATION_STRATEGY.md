# M5 Dataset Integration with ML Model Development

## 🎯 Strategic Overview

The **M5 Forecasting dataset** (Walmart retail demand data) is an ideal real-world dataset for demonstrating ML Model Development capabilities. It provides:

- **Real historical data** (1,969 days, 10 stores, 3,049 items)
- **Multiple model families** supported: Forecasting + Pricing
- **Rich feature set** (prices, events, SNAP days, hierarchies)
- **Evaluation-ready** (known actuals for backtesting)
- **Production-like complexity** (hierarchical, multi-variate)

---

## 🔗 Integration Points

### 1. **Data Source Layer** ⭐ High Priority

#### Add `data_sources` to ML Recipe Manifest
Link recipes to specific datasets/tables.

```json
{
  "id": "recipe_forecasting_m5",
  "name": "Forecasting - M5 Retail Demand",
  "model_family": "forecasting",
  "data_sources": {
    "primary": {
      "type": "postgres",
      "schema": "public",
      "tables": ["m5_sales", "m5_calendar", "m5_items", "m5_prices"],
      "description": "M5 Walmart retail sales data"
    },
    "grain": "item_store_day",
    "target": "sales",
    "date_column": "date",
    "hierarchy": ["state_id", "store_id", "dept_id", "cat_id", "item_id"]
  }
}
```

**Benefits:**
- Links recipes to actual data
- Documents data lineage
- Enables automated feature generation
- Supports data validation

---

### 2. **M5-Specific Recipes** ⭐ High Priority

Create specialized recipe variants optimized for M5 data.

#### Recipe: Forecasting - M5 Retail Demand
```json
{
  "id": "recipe_forecasting_m5_retail",
  "name": "M5 Retail Demand Forecasting",
  "model_family": "forecasting",
  "level": "industry",
  "parent_id": "recipe_forecasting_base",
  "data_sources": { /* as above */ },
  "requirements": {
    "features": [
      "historical_sales",
      "price",
      "day_of_week",
      "is_weekend",
      "is_event_day",
      "event_type",
      "is_snap_day",
      "store_id",
      "dept_id",
      "cat_id"
    ],
    "grain": "item_store_day",
    "target": "sales",
    "time_column": "date"
  },
  "pipeline": {
    "stages": [
      {
        "name": "feature_engineering",
        "steps": [
          "Create lag features (7, 14, 28 days)",
          "Calculate rolling averages (7, 28 days)",
          "Encode categorical variables (store, dept, cat)",
          "Create price change indicators",
          "Add event/SNAP day flags"
        ]
      },
      {
        "name": "training",
        "algorithm": "LightGBM",
        "hyperparameters": {
          "num_leaves": 31,
          "learning_rate": 0.05,
          "n_estimators": 100
        },
        "cv_strategy": "time_series_split"
      },
      {
        "name": "evaluation",
        "metrics": ["MAPE", "RMSE", "MAE"],
        "holdout_days": 28
      }
    ]
  }
}
```

#### Recipe: Pricing - M5 Price Optimization
```json
{
  "id": "recipe_pricing_m5_elasticity",
  "name": "M5 Price Elasticity Modeling",
  "model_family": "pricing",
  "level": "industry",
  "parent_id": "recipe_pricing_base",
  "data_sources": { /* m5_prices, m5_sales joined */ },
  "requirements": {
    "features": [
      "current_price",
      "avg_price_last_4weeks",
      "price_change_pct",
      "competitor_price_index",
      "demand_last_week",
      "inventory_level",
      "is_promotional_week"
    ],
    "target": "demand_response",
    "constraint_columns": ["min_price", "max_price"]
  }
}
```

---

### 3. **M5 Synthetic Examples** ⭐ High Priority

Add realistic M5-based examples to existing recipes.

**Table: `ml_synthetic_example`**

```python
# For forecasting recipe
{
  "recipe_id": "recipe_forecasting_base",
  "dataset_schema_json": {
    "columns": [
      {"name": "date", "type": "date"},
      {"name": "item_id", "type": "string"},
      {"name": "store_id", "type": "string"},
      {"name": "sales", "type": "integer"},
      {"name": "price", "type": "float"},
      {"name": "is_event_day", "type": "boolean"}
    ],
    "source": "M5 Forecasting - Walmart Retail"
  },
  "sample_rows_json": [
    {
      "date": "2016-05-01",
      "item_id": "FOODS_1_001",
      "store_id": "CA_1",
      "sales": 12,
      "price": 3.97,
      "is_event_day": false
    },
    // ... 10 more sample rows from actual M5 data
  ],
  "example_run_json": {
    "description": "Forecast daily sales for FOODS_1_001 at CA_1",
    "expected_metrics": {
      "MAPE": 0.18,
      "RMSE": 2.3,
      "MAE": 1.8
    }
  }
}
```

**Implementation Script:**
```bash
backend/scripts/add_m5_synthetic_examples.py
```

---

### 4. **Real Training Runs on M5 Data** ⭐ Medium Priority

Create actual training runs using M5 data instead of mocked metrics.

#### New Service: `M5TrainingService`
```python
# backend/domains/ml_development/m5_training_service.py

class M5TrainingService:
    """Execute real training runs on M5 data."""
    
    @staticmethod
    def train_forecasting_model(
        item_store_id: str,
        train_end_date: str,
        horizon_days: int = 28
    ) -> Dict:
        """
        Train forecasting model on M5 data.
        
        Returns actual metrics (MAPE, RMSE, MAE) from holdout validation.
        """
        # 1. Load M5 data from database
        # 2. Engineer features
        # 3. Train LightGBM model
        # 4. Evaluate on holdout
        # 5. Return actual metrics
        pass
    
    @staticmethod
    def train_pricing_model(
        item_id: str,
        store_ids: List[str]
    ) -> Dict:
        """
        Train price elasticity model on M5 data.
        
        Returns elasticity coefficients and lift estimates.
        """
        pass
```

**API Endpoint:**
```python
@router.post("/ml-development/runs/execute-m5-training")
def execute_m5_training(
    recipe_id: str,
    config: M5TrainingConfig
):
    """Execute real training on M5 data."""
    # Creates ml_run with actual metrics from M5
    pass
```

---

### 5. **M5-Specific Evaluation Packs** ⭐ Medium Priority

Create evaluation packs tuned for M5 characteristics.

```python
# backend/scripts/seed_m5_evaluation_packs.py

m5_forecasting_pack = {
    "id": "pack_forecasting_m5_retail",
    "name": "M5 Retail Forecasting Evaluation",
    "model_family": "forecasting",
    "description": "Evaluation pack optimized for M5 retail demand patterns",
    "metrics": [
        {
            "key": "WRMSSE",
            "display_name": "Weighted RMSSE (M5 Competition Metric)",
            "compute": "wrmsse",
            "thresholds": {
                "promote": 0.50,
                "warn": 0.60,
                "fail": 0.75
            },
            "direction": "lower_is_better"
        },
        {
            "key": "MAPE",
            "display_name": "Mean Absolute Percentage Error",
            "thresholds": {
                "promote": 0.15,
                "warn": 0.25,
                "fail": 0.40
            },
            "direction": "lower_is_better"
        },
        {
            "key": "forecast_bias",
            "display_name": "Forecast Bias (Over/Under forecasting)",
            "thresholds": {
                "promote": 0.05,
                "warn": 0.10,
                "fail": 0.20
            },
            "direction": "lower_is_better"
        },
        {
            "key": "event_day_accuracy",
            "display_name": "Accuracy on Event Days",
            "compute": "mape_subset",
            "thresholds": {
                "promote": 0.20,
                "warn": 0.30,
                "fail": 0.45
            },
            "direction": "lower_is_better"
        }
    ],
    "slices": [
        {"dimension": "store_id", "values": ["CA_1", "TX_1", "WI_1"]},
        {"dimension": "dept_id", "values": ["FOODS_1", "FOODS_2", "HOBBIES_1"]},
        {"dimension": "is_event_day", "values": ["true", "false"]}
    ],
    "comparators": [
        {
            "type": "baseline",
            "reference_id": "naive_seasonal",
            "description": "Same day last week (7-day lag)"
        },
        {
            "type": "baseline",
            "reference_id": "moving_average",
            "description": "28-day moving average"
        }
    ]
}
```

---

### 6. **Feature Store from M5** 🔮 Future Enhancement

Build a feature repository from M5 data.

```python
# backend/domains/features/m5_features.py

class M5FeatureStore:
    """Pre-computed features from M5 dataset."""
    
    features = {
        "item_store_features": [
            "avg_daily_sales_7d",
            "avg_daily_sales_28d",
            "sales_volatility",
            "price_change_last_week",
            "days_since_last_stockout"
        ],
        "calendar_features": [
            "is_weekend",
            "is_month_start",
            "is_month_end",
            "days_to_next_event",
            "is_snap_day"
        ],
        "hierarchical_features": [
            "dept_total_sales_7d",
            "store_total_sales_7d",
            "state_total_sales_7d"
        ]
    }
    
    @staticmethod
    def get_features(
        item_store_id: str,
        date: str,
        feature_list: List[str]
    ) -> Dict:
        """Retrieve pre-computed features for a given item-store-date."""
        pass
```

---

### 7. **Demo Workflows** ⭐ High Priority

Create end-to-end workflows showcasing M5 integration.

#### Workflow 1: Forecasting Demo
```markdown
1. User views Recipe: "M5 Retail Demand Forecasting"
2. Recipe shows M5 data source (m5_sales, m5_calendar)
3. Synthetic example shows actual M5 data preview
4. User clicks "Create Run"
5. Run executes on real M5 data (item FOODS_1_001, store CA_1)
6. Run completes with actual MAPE, RMSE, MAE
7. Evaluation pack executes automatically
8. Results show: PASS (MAPE=0.16), with slice analysis by day-of-week
9. Model registered and deployed
10. Monitoring tab shows daily re-evaluation on new M5 data
```

#### Workflow 2: Price Optimization Demo
```markdown
1. User views Recipe: "M5 Price Elasticity Modeling"
2. Recipe references m5_prices and m5_sales join
3. User creates run for item FOODS_1_001
4. Model trains on 18 months of price-demand data
5. Outputs elasticity coefficient: -1.8 (elastic good)
6. Evaluation pack checks: revenue lift > 2%, calibration > 0.85
7. Results: WARN (revenue lift = 1.5%, below promote threshold)
8. User adjusts pricing strategy in recipe
9. Re-runs and achieves PASS
```

---

## 🛠️ Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Add `data_sources` field to recipe manifest schema
- [ ] Create M5-specific synthetic examples for existing recipes
- [ ] Seed M5 synthetic examples into database
- [ ] Update Recipe Detail UI to show data sources

### Phase 2: M5 Recipes (Week 2)
- [ ] Create "M5 Retail Demand Forecasting" recipe
- [ ] Create "M5 Price Elasticity" recipe
- [ ] Seed M5 recipes into database
- [ ] Create M5-specific evaluation pack

### Phase 3: Real Training (Week 3)
- [ ] Implement `M5TrainingService`
- [ ] Add API endpoint for M5 training execution
- [ ] Create frontend "Train on M5 Data" button
- [ ] Execute real runs and verify metrics

### Phase 4: Enhanced UI (Week 4)
- [ ] Add data source display in Recipe Detail
- [ ] Show M5 data preview in Synthetic Example tab
- [ ] Add "View Source Data" link (opens data explorer)
- [ ] Create M5 dashboard widget for Model Development

### Phase 5: Feature Store (Future)
- [ ] Design feature schema
- [ ] Pre-compute M5 features
- [ ] Build feature retrieval API
- [ ] Integrate with recipe pipeline

---

## 📊 Expected Benefits

### For Users
✅ **Real-world examples** - Not just mocked data  
✅ **Interactive learning** - Experiment with actual ML workflows  
✅ **Production patterns** - See how real data flows through pipelines  
✅ **Benchmarking** - Compare models against known baselines  

### For Platform
✅ **Credibility** - Demonstrate capability on real data  
✅ **Completeness** - End-to-end ML lifecycle  
✅ **Differentiation** - Not just toy examples  
✅ **Extensibility** - Pattern for adding more datasets  

---

## 🎯 Quick Wins (Implement First)

### 1. Add M5 Synthetic Examples (2 hours)
```bash
# Script to populate synthetic examples with M5 data
python backend/scripts/add_m5_synthetic_examples.py
```

### 2. Create M5 Recipe Variant (1 hour)
```bash
# Add M5-specific recipe
python backend/scripts/seed_m5_recipes.py
```

### 3. Show Data Source in Recipe UI (2 hours)
```typescript
// In RecipeDetail.tsx, add Data Source section
<div className="data-source-section">
  <h3>Data Source</h3>
  <p>M5 Forecasting - Walmart Retail Sales</p>
  <div>
    <span>Tables: m5_sales, m5_calendar, m5_items, m5_prices</span>
    <button onClick={() => navigate('/data-explorer')}>
      Explore Data →
    </button>
  </div>
</div>
```

### 4. Link to Data Explorer (1 hour)
Add deep links from Recipe pages to Data Explorer with pre-filled M5 queries.

---

## 💡 Advanced Ideas

### 1. **AutoML on M5**
Automatically train multiple models on M5 data and compare results.

### 2. **M5 Leaderboard**
Show top-performing recipes/models ranked by M5 evaluation metrics.

### 3. **Interactive M5 Playground**
Let users modify recipe parameters and see impact on M5 forecasts in real-time.

### 4. **M5 Data Quality Reports**
Generate automated reports on M5 data characteristics (missingness, trends, seasonality).

### 5. **Hierarchical Forecasting Demo**
Train models at all hierarchy levels (item → dept → store → state) and show reconciliation.

---

## 🔗 Integration with Existing Features

### Data Dictionary
- Document M5 tables in Data Dictionary
- Link from Recipe → Data Dictionary entries
- Show feature definitions and data types

### Data Explorer
- Add M5 pre-built queries
- Create M5 dashboard templates
- Enable quick exploration from recipes

### Synthetic Data
- Use M5 as reference for generating realistic retail data
- Create "M5-like" synthetic datasets for privacy

### Distillation
- Train teacher models on full M5, distill to smaller student models
- Show compression ratios and speed improvements

---

## 📚 Documentation Needed

1. **M5 Integration Guide** - How to use M5 data in ML workflows
2. **Recipe Templates** - Best practices for M5-based recipes
3. **Evaluation Guidelines** - How to interpret M5 metrics
4. **Troubleshooting** - Common issues with M5 data

---

## ✅ Success Criteria

- [ ] At least 2 M5-specific recipes created and seeded
- [ ] Synthetic examples show actual M5 data
- [ ] Users can see data source information in Recipe UI
- [ ] One complete demo workflow documented
- [ ] M5 evaluation pack integrated and working
- [ ] Link from Recipe page to Data Explorer with M5 query

---

## 🚀 Get Started

**Step 1:** Add M5 synthetic examples to existing recipes  
**Step 2:** Create one M5-specific recipe (forecasting)  
**Step 3:** Show data source in Recipe Detail UI  
**Step 4:** Document the workflow  

**Estimated Time:** 6-8 hours for Phase 1

This integration will transform the ML Model Development toolkit from a demo to a **production-ready ML platform** with real-world data! 🎉
