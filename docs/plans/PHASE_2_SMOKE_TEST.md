# ML Compute Engine - Phase 2 Smoke Test

> Test Phase 2 features: Drift Detection, Asset Versioning, Scheduling

## Prerequisites

```powershell
# 1. Start services
docker compose -p nex up -d

# 2. Run Phase 2 migration
docker exec nex-backend alembic upgrade head

# 3. Verify backend is healthy
Invoke-RestMethod http://localhost:8000/api/v1/health
```

---

## Test 1: Create Drift Check

**Create a drift check to monitor a metric.**

```powershell
$body = @{
    name = "Test RMSE Check"
    metric = "rmse"
    threshold = 0.10
    comparison = "percentage_both"
    recipe_id = "test_recipe"
    description = "Alert if RMSE changes by more than 10%"
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/drift/checks `
    -ContentType "application/json" `
    -Body $body | ConvertTo-Json -Depth 3
```

**Expected:** Drift check created with ID

✅ **PASS** if you get a check ID and the check appears in the response

---

## Test 2: Evaluate Drift Check

**Test drift detection with a value.**

```powershell
# First, set a baseline
$checkId = "your-check-id"
Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/drift/checks/$checkId/evaluate?current_value=0.10" | ConvertTo-Json

# Then test with a value that breaches threshold
Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/drift/checks/$checkId/evaluate?current_value=0.15" | ConvertTo-Json
```

**Expected for breach:**
```json
{
  "is_breached": true,
  "baseline_value": 0.10,
  "current_value": 0.15,
  "change_percent": 50.0,
  "severity": "critical"
}
```

✅ **PASS** if drift is detected correctly

---

## Test 3: List Drift Alerts

**Check if alerts were created.**

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/drift/alerts | ConvertTo-Json -Depth 3
```

**Expected:** List of alerts including the one from Test 2

✅ **PASS** if alert exists with correct details

---

## Test 4: Get Drift Summary

**Get overall drift detection status.**

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/drift/summary | ConvertTo-Json
```

**Expected:**
```json
{
  "total_checks": 1,
  "active_checks": 1,
  "breached_checks": 1,
  "total_alerts": 1,
  "unacknowledged_alerts": 1
}
```

✅ **PASS** if counts are accurate

---

## Test 5: Acknowledge Alert

**Acknowledge a drift alert.**

```powershell
$alertId = "your-alert-id"
Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/drift/alerts/$alertId/acknowledge" `
    -ContentType "application/json" `
    -Body '{"acknowledged_by": "smoke_test"}' | ConvertTo-Json -Depth 3
```

✅ **PASS** if alert is marked as acknowledged

---

## Test 6: Create Schedule

**Create a recurring run schedule.**

```powershell
$body = @{
    name = "Test Weekly Run"
    recipe_id = "test_recipe"
    cron_expression = "0 9 * * 1"
    timezone = "UTC"
    use_reuse_engine = $true
    notify_on_failure = $true
    notification_channels = @("slack")
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/schedules `
    -ContentType "application/json" `
    -Body $body | ConvertTo-Json -Depth 3
```

**Expected:** Schedule created with ID and next_run_at calculated

✅ **PASS** if schedule is created with correct cron settings

---

## Test 7: List Schedules

**Get all schedules.**

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/schedules | ConvertTo-Json -Depth 3
```

✅ **PASS** if the test schedule appears in the list

---

## Test 8: Trigger Schedule Manually

**Manually trigger a schedule execution.**

```powershell
$scheduleId = "your-schedule-id"
Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/schedules/$scheduleId/trigger" | ConvertTo-Json
```

**Expected:**
```json
{
  "message": "Schedule triggered successfully",
  "schedule_id": "...",
  "run_id": "..."
}
```

✅ **PASS** if schedule triggers and creates a run

---

## Test 9: Pause/Resume Schedule

**Test schedule control.**

```powershell
# Pause
$scheduleId = "your-schedule-id"
Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/schedules/$scheduleId/pause" | ConvertTo-Json

# Check it's paused
$schedule = Invoke-RestMethod "http://localhost:8000/api/v1/schedules/$scheduleId"
Write-Host "Is Active: $($schedule.is_active)"  # Should be False

# Resume
Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/schedules/$scheduleId/resume" | ConvertTo-Json
```

✅ **PASS** if schedule can be paused and resumed

---

## Test 10: Asset History

**Test asset version history (requires existing assets).**

```powershell
# List derived assets first
$assets = Invoke-RestMethod http://localhost:8000/api/v1/ml-development/assets
$assetId = $assets.assets[0].id

# Get history
Invoke-RestMethod "http://localhost:8000/api/v1/ml-development/assets/$assetId/history" | ConvertTo-Json -Depth 4
```

✅ **PASS** if history endpoint returns version information

---

## Test 11: Run Comparison API

**Test run comparison endpoint.**

```powershell
# Get some runs first
$runs = Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs
$runIds = ($runs.runs | Select-Object -First 2 | ForEach-Object { $_.id }) -join ","

if ($runIds) {
    Invoke-RestMethod "http://localhost:8000/api/v1/ml-development/runs/compare?run_ids=$runIds" | ConvertTo-Json -Depth 5
} else {
    Write-Host "Need at least 2 runs to compare"
}
```

✅ **PASS** if comparison returns metrics and cost data

---

## Test 12: Run Comparison Frontend

**Test the frontend page.**

1. Open browser to http://localhost:3000/model-development/runs/compare
2. Select 2-3 runs
3. Click "Compare"
4. Verify metrics table and cost summary display

✅ **PASS** if UI displays comparison correctly

---

## Test 13: Database Schema Verification

**Verify Phase 2 tables exist.**

```powershell
docker exec nex-db psql -U nex -d nex -c "\dt" | Select-String "drift|notification|schedule"
```

**Expected tables:**
- `drift_checks`
- `drift_alerts`
- `notification_settings`
- `run_schedules`

✅ **PASS** if all tables exist

---

## Summary Checklist

| Test | Description | Status |
|------|-------------|--------|
| 1 | Create drift check | ⬜ |
| 2 | Evaluate drift | ⬜ |
| 3 | List alerts | ⬜ |
| 4 | Drift summary | ⬜ |
| 5 | Acknowledge alert | ⬜ |
| 6 | Create schedule | ⬜ |
| 7 | List schedules | ⬜ |
| 8 | Trigger schedule | ⬜ |
| 9 | Pause/resume | ⬜ |
| 10 | Asset history | ⬜ |
| 11 | Run comparison API | ⬜ |
| 12 | Comparison frontend | ⬜ |
| 13 | Schema verification | ⬜ |

---

## Troubleshooting

### Migration not applied

```powershell
docker exec nex-backend alembic current
# Should show: 022_add_phase_2 (head)

# If not, run:
docker exec nex-backend alembic upgrade head
```

### Scheduler not working

Check if APScheduler is installed:
```powershell
docker exec nex-backend pip list | Select-String "APScheduler"
```

If not installed:
```powershell
docker exec nex-backend pip install apscheduler croniter pytz
```

### Drift tables missing

Run the migration manually:
```powershell
docker exec nex-db psql -U nex -d nex -c "
CREATE TABLE IF NOT EXISTS drift_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    metric VARCHAR(100) NOT NULL,
    threshold NUMERIC(10,4) NOT NULL,
    comparison VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"
```
