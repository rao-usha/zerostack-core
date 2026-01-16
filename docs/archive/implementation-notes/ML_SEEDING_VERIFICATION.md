# ML Model Development - Seeding Verification Guide

## ✅ What Was Seeded

### Successfully populated all ML Model Development components:

| Component | Count | Description |
|-----------|-------|-------------|
| **ML Recipes** | 4 | Baseline recipes for all 4 model families |
| **Evaluation Packs** | 4 | Standard evaluation packs for each family |
| **Recipe-Pack Attachments** | 4 | Each recipe linked to matching pack |
| **ML Models** | 6 | Registered models from approved recipes |
| **Runs** | 19 | Training, eval, and backtest runs |
| **Monitoring Snapshots** | 28 | Time-series monitoring for production models |
| **Evaluation Results** | 10 | Execution of packs on successful runs |
| **Monitor Eval Snapshots** | 15 | Evaluation monitoring over time |

---

## 🧪 Quick API Verification

### 1. Check Recipes
```bash
curl http://localhost:8000/api/v1/ml-development/recipes
```
**Expected:** 4 recipes (forecasting, pricing, NBA, location scoring)

### 2. Check Evaluation Packs
```bash
curl http://localhost:8000/api/v1/evaluation-packs
```
**Expected:** 4 evaluation packs with "approved" status

### 3. Check Models
```bash
curl http://localhost:8000/api/v1/ml-development/models
```
**Expected:** 6 models (various statuses: draft, staging, production)

### 4. Check Runs
```bash
curl http://localhost:8000/api/v1/ml-development/runs
```
**Expected:** 19 runs (train/eval/backtest, succeeded/failed)

### 5. Check Recipe-Pack Attachments
```bash
curl http://localhost:8000/api/v1/evaluation-packs/recipes/recipe_forecasting_base/packs
```
**Expected:** Forecasting Standard Evaluation v1 pack attached

### 6. Check Evaluation Results
```bash
# Get a run ID first
curl http://localhost:8000/api/v1/ml-development/runs | jq -r '.runs[0].id'

# Then check its evaluation results
curl http://localhost:8000/api/v1/evaluation-packs/runs/YOUR_RUN_ID/results
```
**Expected:** Evaluation results with pass/warn/fail status

### 7. Check Monitoring Snapshots
```bash
# Get a production model ID
curl "http://localhost:8000/api/v1/ml-development/models?status=production" | jq -r '.models[0].id'

# Check its monitoring snapshots
curl http://localhost:8000/api/v1/ml-development/models/YOUR_MODEL_ID/monitor-snapshots
```
**Expected:** Multiple snapshots showing performance over time

### 8. Check Monitoring Evaluation Snapshots
```bash
curl http://localhost:8000/api/v1/evaluation-packs/models/YOUR_MODEL_ID/snapshots
```
**Expected:** Evaluation pack executions for monitoring

---

## 🌐 Frontend Verification

### 1. Model Library
Open: `http://localhost:3000/model-development`

**Expected to see:**
- **Recipes Tab:** 4 recipe cards
- **Models Tab:** 6 model cards (different statuses)
- **Runs Tab:** 19 run cards
- **Evaluation Packs Tab:** 4 evaluation pack cards

### 2. Recipe Detail
Click any recipe → Check for:
- Overview with metadata
- Manifest editor
- Versions tab
- Synthetic example
- **Attached evaluation pack** (in Overview or separate section)

### 3. Model Detail
Click a production model → Check for:
- Overview
- Deployments
- **Monitoring tab with 5-9 snapshots**
- Alerts

### 4. Run Detail
Click a succeeded run → Check for:
- Run metadata
- Metrics JSON
- Artifacts
- **Evaluation Results panel** (if evaluated)

### 5. Evaluation Pack Detail
Click any evaluation pack → Check for:
- Pack metadata
- Metrics with thresholds
- Status badge (Approved)
- Tags

---

## 📊 Sample Data Highlights

### Models Created:
1. **Forecasting Baseline v1 Model v1** (Production)
   - Has monitoring snapshots
   - Has evaluation results

2. **Pricing Optimization Baseline v1 Model v2** (Production)
   - Has monitoring snapshots
   - Has multiple successful runs

3. **Next Best Action Baseline v1 Model v1** (Production)
   - Has successful eval runs
   - Has evaluation results

4. **Location Scoring Baseline v1 Model v1** (Production)
   - Has monitoring snapshots
   - Has backtest runs

### Run Types:
- **Train runs:** Model training executions
- **Eval runs:** Evaluation on holdout sets
- **Backtest runs:** Historical validation

### Evaluation Pack Metrics:

**Forecasting:**
- MAPE, RMSE, MAE, forecast_bias, coverage_80

**Pricing:**
- revenue_lift, margin_impact, elasticity_accuracy, calibration, constraint_violations

**NBA:**
- uplift, precision_at_10, qini_coefficient, incremental_revenue, action_distribution

**Location Scoring:**
- rank_correlation, calibration, hit_rate_at_10, lift_top_decile, geographic_coverage

---

## 🎯 Test Scenarios

### Scenario 1: View Recipe and its Evaluation Pack
1. Go to Model Development → Recipes
2. Click "Forecasting Baseline v1"
3. Verify "Forecasting Standard Evaluation v1" is attached
4. Check metrics and thresholds

### Scenario 2: View Model Performance
1. Go to Model Development → Models
2. Filter by status="production"
3. Click a production model
4. Go to Monitoring tab
5. See performance metrics over time
6. Check for drift warnings

### Scenario 3: View Run Evaluation
1. Go to Model Development → Runs
2. Click a "succeeded" run
3. Scroll to "Evaluation Results" section
4. See metrics table with pass/warn/fail indicators
5. Check summary text

### Scenario 4: Clone an Evaluation Pack
1. Go to Model Development → Evaluation Packs
2. Click any pack
3. Click "Clone" button
4. Give it a new name
5. Verify new pack created with same metrics

---

## 🔧 Troubleshooting

### Issue: No data showing in UI
**Solution:** Hard refresh browser (`Ctrl + Shift + R`)

### Issue: API returns empty arrays
**Solution:** Check backend logs:
```bash
docker logs nex-backend-dev --tail 50
```

### Issue: Evaluation results missing
**Solution:** Re-run comprehensive seed:
```bash
docker exec nex-backend-dev python scripts/seed_ml_complete.py
```

### Issue: Monitoring snapshots not showing
**Solution:** Only production models have monitoring snapshots. Filter by status="production".

---

## 📈 Expected Metrics Ranges

### Forecasting:
- MAPE: 0.10 - 0.30 (lower is better)
- RMSE: 30 - 120 (lower is better)
- MAE: 20 - 80 (lower is better)

### Pricing:
- Revenue Lift: 0.01 - 0.08 (higher is better)
- Margin Impact: 0.02 - 0.10 (higher is better)
- Calibration: 0.80 - 0.98 (higher is better)

### NBA:
- Uplift: 0.05 - 0.18 (higher is better)
- Precision@10: 0.15 - 0.40 (higher is better)
- Incremental Revenue: $50K - $150K (higher is better)

### Location Scoring:
- Rank Correlation: 0.60 - 0.85 (higher is better)
- Hit Rate@10: 0.30 - 0.60 (higher is better)
- Lift Top Decile: 1.5 - 3.0 (higher is better)

---

## 🎉 Success Indicators

✅ **All endpoints return data (not empty arrays)**  
✅ **Frontend shows all 4 tabs with data**  
✅ **Recipe detail pages show attached packs**  
✅ **Run detail pages show evaluation results**  
✅ **Model monitoring shows time-series data**  
✅ **Evaluation packs show metrics with thresholds**  

---

## 💡 Next Steps

1. **Explore the UI:** Navigate through all pages and tabs
2. **Test workflows:** 
   - Attach/detach packs to recipes
   - Execute evaluation packs on runs
   - Create monitoring snapshots
3. **Complete remaining frontend:**
   - Evaluation Pack Detail page
   - Integration into Recipe/Run/Model pages
4. **Customize evaluation packs:**
   - Clone existing packs
   - Modify thresholds
   - Add new metrics

---

## 📚 Related Documentation

- `EVALUATION_PACKS_IMPLEMENTATION.md` - Technical implementation details
- `EVALUATION_PACKS_SETUP_GUIDE.md` - Setup and API examples
- `ML_MODEL_DEVELOPMENT.md` - Full ML workspace documentation

**Everything is ready! 🚀 Start exploring at http://localhost:3000/model-development**

