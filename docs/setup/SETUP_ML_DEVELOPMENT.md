# Setup Guide: ML Model Development Feature

## Problem: 500 Errors on ML Development Pages

If you're seeing errors like:
```
GET http://localhost:3000/api/ml-development/recipes 500 (Internal Server Error)
Error loading data: SyntaxError: Failed to execute 'json' on 'Response'
```

This means the **ML development database tables haven't been created yet**.

---

## ✅ Step-by-Step Setup

### Step 1: Check Current State

First, let's see if the tables exist:

```bash
cd backend
python check_ml_tables.py
```

If tables are missing, continue to Step 2.

---

### Step 2: Run Database Migration

Run the Alembic migration to create the 6 new ML tables:

**Option A: Using Alembic directly**
```bash
cd backend
alembic upgrade head
```

**Option B: Using Docker (if backend is in Docker)**
```bash
docker exec -it nex-backend-dev alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 008_dictionary -> 009_ml_development, Add ML Model Development tables
```

---

### Step 3: Seed Baseline Recipes

Load the 4 baseline recipes (Forecasting, Pricing, NBA, Location Scoring):

**Option A: Directly**
```bash
cd backend
python scripts/seed_ml_recipes.py
```

**Option B: Using Docker**
```bash
docker exec -it nex-backend-dev python scripts/seed_ml_recipes.py
```

**Expected Output:**
```
✅ Successfully seeded 4 baseline ML recipes!
   - Forecasting Baseline v1
   - Pricing Optimization Baseline v1
   - Next Best Action Baseline v1
   - Location Scoring Baseline v1
```

---

### Step 4: Verify Setup

Run the check script again:

```bash
cd backend
python check_ml_tables.py
```

**Expected Output:**
```
Checking ML Development tables...
--------------------------------------------------
✓ ml_recipe
✓ ml_recipe_version
✓ ml_model
✓ ml_run
✓ ml_monitor_snapshot
✓ ml_synthetic_example
--------------------------------------------------

✅ All ML tables exist!

Recipes in database: 4
✅ Seed data exists!
```

---

### Step 5: Restart Backend

**If backend is running locally:**
```bash
# It should auto-reload with uvicorn --reload
# But if not, restart:
cd backend
uvicorn main:app --reload
```

**If backend is in Docker:**
```bash
docker restart nex-backend-dev
# Or
docker-compose restart backend
```

---

### Step 6: Test in Browser

1. **Refresh your browser** (clear cache if needed)
2. Navigate to `/model-development`
3. You should see 4 baseline recipes!

---

## 🔍 Troubleshooting

### Issue: "alembic: command not found"

Install Alembic:
```bash
cd backend
pip install alembic
```

### Issue: "ModuleNotFoundError: No module named 'domains.ml_development'"

The backend needs to be restarted after adding new domains:
```bash
# Stop backend
# Start backend again
cd backend
uvicorn main:app --reload
```

### Issue: "sqlalchemy.exc.OperationalError: (psycopg.OperationalError) connection failed"

Check your database connection:
1. Ensure PostgreSQL is running
2. Check `.env` file has correct `DATABASE_URL`
3. Test connection:
   ```bash
   cd backend
   python -c "from core.config import settings; print(settings.database_url)"
   ```

### Issue: Tables exist but no recipes showing

Re-run the seed script:
```bash
cd backend
python scripts/seed_ml_recipes.py
```

### Issue: Still getting 500 errors after setup

Check backend logs:

**Local:**
```bash
# Check terminal where uvicorn is running
```

**Docker:**
```bash
docker logs nex-backend-dev
# Or follow logs
docker logs -f nex-backend-dev
```

Look for Python errors related to `ml_development`.

---

## 📋 Quick Setup (All-in-One)

### For Local Development:
```bash
cd backend
alembic upgrade head && python scripts/seed_ml_recipes.py && python check_ml_tables.py
```

### For Docker:
```bash
docker exec -it nex-backend-dev bash -c "alembic upgrade head && python scripts/seed_ml_recipes.py && python check_ml_tables.py"
```

---

## 🎯 What Gets Created

### Database Tables (6 tables):
- `ml_recipe` - Recipe definitions
- `ml_recipe_version` - Version history  
- `ml_model` - Registered models
- `ml_run` - Training/eval runs
- `ml_monitor_snapshot` - Monitoring data
- `ml_synthetic_example` - Example datasets

### Seed Data (4 recipes):
1. **Forecasting Baseline v1**
   - Time series prediction
   - ARIMA/Prophet
   - Metrics: MAPE, RMSE, MAE

2. **Pricing Optimization Baseline v1**
   - Margin/revenue optimization
   - Price elasticity
   - Metrics: revenue_lift, margin_impact

3. **Next Best Action Baseline v1**
   - Recommendation engine
   - Uplift modeling
   - Metrics: uplift, precision@k

4. **Location Scoring Baseline v1**
   - Site selection
   - Trade area analysis
   - Metrics: rank_correlation, calibration

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Migration ran successfully (009_ml_development)
- [ ] 6 tables exist in database
- [ ] 4 baseline recipes seeded
- [ ] Backend restarted/reloaded
- [ ] No errors in backend logs
- [ ] `/model-development` page loads without errors
- [ ] Can see 4 recipes in the Recipes tab
- [ ] Can click on a recipe to view details
- [ ] Settings button works in ML Chat
- [ ] Provider/model dropdown populated

---

## 🆘 Still Having Issues?

1. **Check backend logs** for Python errors
2. **Verify .env file** has DATABASE_URL
3. **Ensure PostgreSQL is running**
4. **Try the check script**: `python check_ml_tables.py`
5. **Check if router is registered** in `backend/main.py`:
   ```python
   from domains.ml_development.router import router as ml_development_router
   app.include_router(ml_development_router, prefix=settings.api_prefix)
   ```

---

## 📞 Success!

Once setup is complete, you should be able to:
- ✅ View 4 baseline recipes
- ✅ Clone and edit recipes
- ✅ Create models from recipes
- ✅ Track training runs
- ✅ View monitoring dashboards
- ✅ Chat with ML assistant using real LLMs

Enjoy building ML recipes! 🎉

