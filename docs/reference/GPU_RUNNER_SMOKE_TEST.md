# GPU Runner Smoke Test Guide

This guide walks through testing the GPU Runner feature end-to-end.

> **Note:** Commands are for Windows PowerShell. Run from project root unless specified.

## Prerequisites

1. Docker Desktop installed
2. Python 3.11+ installed
3. (Optional) For SSH adapter testing: a remote GPU VM

---

## Step 1: Start Infrastructure

```powershell
docker compose -p nex up -d
```

**Verify services are running:**
```powershell
docker ps
```

Expected containers:
- `nex-db` - PostgreSQL
- `nex-minio` - MinIO object storage
- `nex-backend` - API server
- `nex-frontend` - Frontend

**Access points:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- MinIO Console: http://localhost:9001 (login: minioadmin/minioadmin)

---

## Step 2: Run Database Migration

```powershell
cd backend
pip install -r requirements.txt  # If not already installed
alembic upgrade head
```

**Verify migration:**
```powershell
alembic current
# Should show: 020_add_gpu_runner (head)
```

---

## Step 3: Seed Data

```powershell
cd backend
python -m scripts.seed_gpu_runner
```

Expected output:
```
🚀 Seeding GPU Runner data...
  📦 Creating M5 highlighted dataset...
  🧪 Creating M5 forecasting recipe...
  📋 Creating recipe version...
  📊 Creating sample highlighted dataset...
✅ GPU Runner seed data created successfully!
```

---

## Step 4: Test Highlighted Datasets API

### 4.1 List Datasets
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/highlighted-datasets | ConvertTo-Json -Depth 5
```

Expected: Should return M5 dataset with `availability_state: "NOT_PRESENT"`

### 4.2 Get Dataset Details
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/highlighted-datasets/m5_forecasting | ConvertTo-Json -Depth 5
```

### 4.3 Resolve Dataset (should indicate upload needed)
```powershell
Invoke-RestMethod -Method POST http://localhost:8000/api/v1/highlighted-datasets/m5_forecasting/resolve `
  -ContentType "application/json" `
  -Body "{}" | ConvertTo-Json
```

Expected: `"message": "Dataset requires manual file upload..."`

---

## Step 5: Test File Upload

Create a sample CSV for testing:
```powershell
@"
date,store_id,item_id,sales
2020-01-01,CA_1,ITEM_001,100
2020-01-02,CA_1,ITEM_001,120
2020-01-03,CA_1,ITEM_001,90
"@ | Out-File -FilePath "$env:TEMP\sales.csv" -Encoding UTF8
```

### 5.1 Upload File
```powershell
# Using curl (comes with Windows 10+)
curl.exe -X POST "http://localhost:8000/api/v1/highlighted-datasets/m5_forecasting/upload?version_label=v1" `
  -F "file=@$env:TEMP\sales.csv"
```

### 5.2 Complete Upload
```powershell
Invoke-RestMethod -Method POST http://localhost:8000/api/v1/highlighted-datasets/m5_forecasting/upload/complete `
  -ContentType "application/json" `
  -Body '{"version_label": "v1"}'
```

### 5.3 Verify Dataset is Available
```powershell
(Invoke-RestMethod http://localhost:8000/api/v1/highlighted-datasets/m5_forecasting).availability_state
# Should return: "AVAILABLE"
```

### 5.4 Check MinIO
Visit http://localhost:9001 and navigate to:
`nex-data / datasets / m5 / v1 /`

You should see:
- `raw/sales.csv`
- `manifest.json`

---

## Step 6: Test ML Recipe & Runs

### 6.1 List Recipes
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/recipes | ConvertTo-Json -Depth 5
```

Should include `recipe_m5_forecast_v1`

### 6.2 Create a Run
```powershell
$body = @{
    recipe_id = "recipe_m5_forecast_v1"
    recipe_version_id = "ver_m5_forecast_v1_100"
    run_type = "train"
} | ConvertTo-Json

$run = Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs `
  -ContentType "application/json" `
  -Body $body

$run | ConvertTo-Json
$runId = $run.id
Write-Host "Run ID: $runId"
```

### 6.3 Check Run Status
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs/$runId | ConvertTo-Json -Depth 3
```

### 6.4 Get Run Logs
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs/$runId/logs
```

---

## Step 7: Test Derived Assets

### 7.1 List Assets
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/assets | ConvertTo-Json -Depth 5
```

### 7.2 Bank a Run (if run succeeded)
```powershell
$bankBody = @{
    asset_type = "temporal"
    name = "Test forecast results"
} | ConvertTo-Json

$asset = Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/$runId/bank `
  -ContentType "application/json" `
  -Body $bankBody

$asset | ConvertTo-Json -Depth 3
$assetId = $asset.id
```

### 7.3 Promote Asset to Permanent
```powershell
Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/assets/$assetId/promote `
  -ContentType "application/json" `
  -Body '{"notes": "Promoted for production use"}' | ConvertTo-Json -Depth 3
```

### 7.4 Delete Asset
```powershell
Invoke-RestMethod -Method DELETE http://localhost:8000/api/v1/ml-development/assets/$assetId
```

---

## Step 8: Test Interaction Logs

### 8.1 List All Interactions
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/interactions | ConvertTo-Json -Depth 5
```

### 8.2 Filter by Event Type
```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/interactions?event_type=DATASET_RESOLVE" | ConvertTo-Json -Depth 5
```

### 8.3 Get Run History
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/interactions/run/$runId | ConvertTo-Json -Depth 5
```

### 8.4 List Event Types
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/interactions/event-types | ConvertTo-Json -Depth 3
```

---

## Step 9: Test Frontend UI

### 9.1 Highlighted Datasets Page
1. Open http://localhost:3000/model-development/datasets
2. Should see M5 dataset card
3. Click "Upload Data" to test upload flow
4. Verify state changes to "AVAILABLE" after upload

### 9.2 Derived Assets Page
1. Open http://localhost:3000/model-development/assets
2. Should see any banked assets
3. Test "Promote" button on temporal assets
4. Test "Delete" button

---

## Step 10: Test Recipe Container (Optional)

### 10.1 Build Container
```powershell
cd recipes\forecast_m5_v1
docker build -t nex/forecast-m5:v1 .
```

### 10.2 Run Locally with Test Data
```powershell
docker run -it --rm `
  -e RUN_ID=test_001 `
  -e INPUT_URI=datasets/m5/v1 `
  -e OUTPUT_URI=runs/test_001 `
  -e S3_ENDPOINT=http://host.docker.internal:9000 `
  -e S3_ACCESS_KEY=minioadmin `
  -e S3_SECRET_KEY=minioadmin `
  -e S3_BUCKET=nex-data `
  -e PARAMS_JSON='{"horizon": 7, "n_estimators": 10}' `
  nex/forecast-m5:v1
```

### 10.3 Verify Outputs in MinIO
Check `nex-data / runs / test_001 / outputs /`:
- `forecast.parquet`
- `metrics.json`
- `run_manifest.json`

---

## Troubleshooting

### MinIO Connection Failed
```powershell
# Check if MinIO is running
docker logs nex-minio

# Verify bucket exists
docker exec nex-minio mc ls local/
```

### Database Migration Issues
```powershell
# Check current migration state
alembic history

# Rollback and retry
alembic downgrade -1
alembic upgrade head
```

### Backend Not Starting
```powershell
# Check logs
docker logs nex-backend

# Common issues:
# - Missing environment variables
# - Database not ready
# - Port conflicts
```

### Frontend API Errors
```powershell
# Check browser console (F12) for CORS or network errors
# Verify VITE_API_URL is set correctly
```

---

## Expected Results Summary

| Test | Expected Result |
|------|-----------------|
| List datasets | Returns M5 with NOT_PRESENT |
| Upload files | State changes to AVAILABLE |
| MinIO browser | Shows datasets/m5/v1/manifest.json |
| Create run | Returns run_id with status=queued |
| Bank run | Creates temporal asset with TTL |
| Promote asset | Changes to permanent, TTL removed |
| Interaction logs | Shows audit trail of all actions |
| Frontend datasets | Displays cards with upload flow |
| Frontend assets | Shows table with promote/delete |

---

## Cleanup

```powershell
# Stop all containers
docker compose -p nex down

# Remove volumes (caution: deletes data)
docker compose -p nex down -v
```
