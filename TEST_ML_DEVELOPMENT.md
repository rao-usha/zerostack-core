# ML Development - Diagnostic Tests

Run these tests in order to diagnose the issue.

---

## Test 1: Check if Backend is Running

```bash
curl http://localhost:8000/
```

**Expected:** 
```json
{"message":"NEX.AI - AI Native Data Platform API","status":"running"}
```

**If fails:** Backend isn't running or wrong port.

---

## Test 2: Check Backend Health

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status":"healthy","service":"NEX.AI API","database":"connected"}
```

**If database: "error":** Database connection issue.

---

## Test 3: Check if ML Router is Registered

```bash
curl http://localhost:8000/docs
```

Then open http://localhost:8000/docs in your browser and look for:
- `/api/ml-development/recipes` endpoint
- Tag: `ml-development`

**If not there:** Router not registered in main.py

---

## Test 4: Test ML Recipes Endpoint (Backend Port)

**IMPORTANT: Backend is on port 8000, not 3000!**

```bash
curl http://localhost:8000/api/ml-development/recipes
```

**Expected (if working):**
```json
{
  "recipes": [
    {
      "id": "recipe_forecasting_base",
      "name": "Forecasting Baseline v1",
      ...
    }
  ],
  "total": 4
}
```

**If 404:** Router not registered
**If 500:** Database tables don't exist
**If empty array:** No seed data

---

## Test 5: Check Database Tables Exist

### For Docker:
```bash
docker exec -it nex-backend-dev python check_ml_tables.py
```

### For Local:
```bash
cd backend
python check_ml_tables.py
```

**Expected:**
```
✓ ml_recipe
✓ ml_recipe_version
✓ ml_model
✓ ml_run
✓ ml_monitor_snapshot
✓ ml_synthetic_example

Recipes in database: 4
```

**If X (missing):** Run migration

---

## Test 6: Check Migration Status

### For Docker:
```bash
docker exec -it nex-backend-dev alembic current
```

### For Local:
```bash
cd backend
alembic current
```

**Expected:** Should show `009_ml_development` or higher

**If shows 008 or lower:** Migration not run

---

## Test 7: Check Database Directly

### For Docker:
```bash
docker exec -it nex-backend-dev python -c "
from sqlalchemy import create_engine, text
from core.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM ml_recipe'))
    count = result.scalar()
    print(f'Recipes in DB: {count}')
"
```

### For Local:
```bash
cd backend
python -c "
from sqlalchemy import create_engine, text
from core.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM ml_recipe'))
    count = result.scalar()
    print(f'Recipes in DB: {count}')
"
```

**Expected:** `Recipes in DB: 4`
**If 0:** Need to seed data
**If error:** Table doesn't exist

---

## Test 8: Check Backend Logs

### For Docker:
```bash
docker logs nex-backend-dev --tail 50
```

### For Local:
```bash
# Check terminal where uvicorn is running
```

**Look for:**
- Import errors
- Database connection errors
- Router registration confirmation

---

## Test 9: Test with Verbose Error

```bash
curl -v http://localhost:8000/api/ml-development/recipes
```

This shows full HTTP headers and response.

**Look for:**
- Status code (404, 500, 200)
- Content-Type header
- Full error message

---

## Test 10: Check if Router is Imported

### For Docker:
```bash
docker exec -it nex-backend-dev python -c "
import sys
sys.path.insert(0, '/app')
from domains.ml_development.router import router
print('✓ Router imports successfully')
print(f'Prefix: {router.prefix}')
print(f'Routes: {len(router.routes)}')
"
```

### For Local:
```bash
cd backend
python -c "
from domains.ml_development.router import router
print('✓ Router imports successfully')
print(f'Prefix: {router.prefix}')
print(f'Routes: {len(router.routes)}')
"
```

**Expected:**
```
✓ Router imports successfully
Prefix: /ml-development
Routes: 20+
```

---

## 🔧 Common Fixes Based on Test Results

### If Test 1 fails (Backend not running):
```bash
# For Docker
docker start nex-backend-dev
# Or
docker-compose up -d backend

# For Local
cd backend
uvicorn main:app --reload
```

### If Test 4 returns 404 (Router not registered):
Check `backend/main.py` has:
```python
from domains.ml_development.router import router as ml_development_router
app.include_router(ml_development_router, prefix=settings.api_prefix)
```

Then restart backend.

### If Test 5 shows missing tables (Migration needed):
```bash
# For Docker
docker exec -it nex-backend-dev alembic upgrade head

# For Local
cd backend
alembic upgrade head
```

### If Test 7 shows 0 recipes (Need seed data):
```bash
# For Docker
docker exec -it nex-backend-dev python scripts/seed_ml_recipes.py

# For Local
cd backend
python scripts/seed_ml_recipes.py
```

### If Test 10 fails (Import error):
Restart backend - it needs to reload the new domain.

---

## 🎯 Quick All-in-One Test

```bash
echo "=== Test 1: Backend Running ==="
curl -s http://localhost:8000/ | head -n 3

echo -e "\n=== Test 2: Health Check ==="
curl -s http://localhost:8000/health

echo -e "\n=== Test 3: ML Recipes Endpoint ==="
curl -s http://localhost:8000/api/ml-development/recipes | python -m json.tool | head -n 20

echo -e "\n=== Test 4: Check Tables (Docker) ==="
docker exec -it nex-backend-dev python check_ml_tables.py
```

---

## ⚠️ Important Note: Port Numbers

- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:3000

When testing APIs, always use **port 8000**, not 3000!

The frontend at 3000 proxies requests to backend at 8000.

So:
- ✅ `curl http://localhost:8000/api/ml-development/recipes`
- ❌ `curl http://localhost:3000/api/ml-development/recipes` (won't work directly)

---

## 📋 Run All Tests Script

Save this as `test_ml.sh`:

```bash
#!/bin/bash

echo "🧪 ML Development Diagnostic Tests"
echo "=================================="
echo ""

echo "Test 1: Backend Status"
echo "----------------------"
curl -s http://localhost:8000/ || echo "❌ Backend not responding"
echo -e "\n"

echo "Test 2: Health Check"
echo "----------------------"
curl -s http://localhost:8000/health || echo "❌ Health check failed"
echo -e "\n"

echo "Test 3: ML Recipes API"
echo "----------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/ml-development/recipes)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Status: $HTTP_CODE"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "❌ Status: $HTTP_CODE"
    echo "$BODY"
fi
echo ""

echo "Test 4: Database Tables (Docker)"
echo "----------------------"
docker exec -it nex-backend-dev python check_ml_tables.py 2>/dev/null || echo "⚠️  Run locally: cd backend && python check_ml_tables.py"
echo ""

echo "Test 5: Migration Status (Docker)"
echo "----------------------"
docker exec -it nex-backend-dev alembic current 2>/dev/null || echo "⚠️  Run locally: cd backend && alembic current"
echo ""

echo "=================================="
echo "Tests Complete!"
```

Make it executable and run:
```bash
chmod +x test_ml.sh
./test_ml.sh
```

---

Run these tests and share the output - it will tell us exactly what's wrong!

