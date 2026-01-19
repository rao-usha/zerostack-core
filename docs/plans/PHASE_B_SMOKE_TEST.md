# ML Compute Engine - Phase B Smoke Test

> Test the Phase B features: Cost tracking, Reuse engine, Retries, RunPod

## Prerequisites

```powershell
# 1. Start services
docker compose -p nex up -d

# 2. Run migrations (includes Phase B: 021_add_phase_b)
docker exec nex-backend alembic upgrade head

# 3. Verify backend is healthy
Invoke-RestMethod http://localhost:8000/api/v1/health
```

---

## Test 1: GPU Pricing

**Verify the GPU pricing table was seeded correctly.**

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/gpu-pricing | ConvertTo-Json -Depth 3
```

**Expected:** List of GPU options with pricing

```json
[
  { "id": "local_any", "provider": "local", "gpu_type": "any", "hourly_rate_usd": 0.0, "memory_gb": null },
  { "id": "runpod_rtx_a4000", "provider": "runpod", "gpu_type": "NVIDIA RTX A4000", "hourly_rate_usd": 0.2, "memory_gb": 16 },
  { "id": "runpod_a100_40gb", "provider": "runpod", "gpu_type": "NVIDIA A100 40GB", "hourly_rate_usd": 1.09, "memory_gb": 40 }
]
```

✅ **PASS** if you see at least 5+ GPU options with providers `local` and `runpod`

---

## Test 2: Plan Run (No Match - Should Proceed)

**Test the reuse engine with a unique request.**

```powershell
$uniqueParams = @{
    recipe_id = "test_recipe_$(Get-Date -Format 'HHmmss')"
    recipe_version_id = "test_version_1"
    dataset_version_id = "test_dataset_1"
    parameters = @{ test_param = "unique_$(Get-Random)" }
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/plan `
    -ContentType "application/json" `
    -Body $uniqueParams | ConvertTo-Json -Depth 3
```

**Expected:**

```json
{
  "action": "PROCEED",
  "similarity_hash": "a1b2c3d4e5f67890",
  "best_match_run_id": null,
  "confidence": 1.0,
  "reason": "No matching runs found",
  "potential_savings_usd": null,
  "estimated_cost_usd": 0.0,
  "matching_run_count": 0
}
```

✅ **PASS** if `action` is `"PROCEED"` and `matching_run_count` is `0`

---

## Test 3: Plan Run (Force Rerun)

**Verify force_rerun bypasses reuse checking.**

```powershell
$forceRerun = @{
    recipe_id = "any_recipe"
    recipe_version_id = "any_version"
    parameters = @{}
    force_rerun = $true
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/plan `
    -ContentType "application/json" `
    -Body $forceRerun | ConvertTo-Json -Depth 3
```

**Expected:**

```json
{
  "action": "PROCEED",
  "reason": "Forced rerun requested"
}
```

✅ **PASS** if `action` is `"PROCEED"` and reason mentions "Forced rerun"

---

## Test 4: Create Run with Cost Tracking

**Create a run and verify cost fields are present.**

```powershell
# First, check if we have any recipes
$recipes = Invoke-RestMethod http://localhost:8000/api/v1/ml-development/recipes
if ($recipes.recipes.Count -eq 0) {
    Write-Host "No recipes found. Creating a test recipe..."
    
    $recipe = @{
        id = "test_cost_recipe"
        name = "Test Cost Recipe"
        description = "Recipe for testing cost tracking"
        model_family = "forecasting"
        level = "starter"
        status = "active"
    } | ConvertTo-Json
    
    Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/recipes `
        -ContentType "application/json" `
        -Body $recipe
}

# Create a run
$runRequest = @{
    recipe_id = "test_cost_recipe"
    recipe_version_id = "v1"
} | ConvertTo-Json

$run = Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs `
    -ContentType "application/json" `
    -Body $runRequest

Write-Host "Created run: $($run.id)"
$run | ConvertTo-Json -Depth 3
```

✅ **PASS** if run is created successfully

---

## Test 5: Get Run Cost

**Check cost breakdown for a run.**

```powershell
# Use the run ID from Test 4, or replace with a known run ID
$runId = "your-run-id-here"

Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs/$runId/cost | ConvertTo-Json
```

**Expected:**

```json
{
  "run_id": "run_abc123",
  "estimated_cost_usd": 0.0,
  "actual_cost_usd": null,
  "runtime_seconds": null,
  "gpu_type": null,
  "savings_from_reuse": null
}
```

✅ **PASS** if endpoint returns without error (cost values may be null for local runs)

---

## Test 6: Compare Runs

**Compare metrics across multiple runs.**

```powershell
# Get list of runs first
$runs = Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs
$runIds = ($runs.runs | Select-Object -First 2 | ForEach-Object { $_.id }) -join ","

if ($runIds) {
    Write-Host "Comparing runs: $runIds"
    Invoke-RestMethod "http://localhost:8000/api/v1/ml-development/runs/compare?run_ids=$runIds" | ConvertTo-Json -Depth 5
} else {
    Write-Host "Need at least 2 runs to compare. Create more runs first."
}
```

✅ **PASS** if comparison returns run details and metrics (or helpful error message)

---

## Test 7: Retry Endpoint

**Test the retry functionality (for failed runs).**

```powershell
# This will fail if the run isn't in FAILED or RETRYING state (expected!)
$runId = "your-run-id"

try {
    Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/$runId/retry `
        -ContentType "application/json" `
        -Body '{"max_retries": 3}'
} catch {
    $response = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "Expected error: $($response.detail)"
}
```

**Expected:** Error saying "Can only retry failed or retrying runs"

✅ **PASS** if you get an appropriate error (runs must be in FAILED state to retry)

---

## Test 8: Database Schema Verification

**Verify Phase B columns exist in the database.**

```powershell
docker exec nex-db psql -U nex -d nex -c "\d ml_run" | Select-String -Pattern "estimated_cost|actual_cost|similarity_hash|retry_count"
```

**Expected output should show:**
- `estimated_cost_usd`
- `actual_cost_usd`
- `similarity_hash`
- `retry_count`
- `max_retries`
- `failure_reason`
- `failure_type`

✅ **PASS** if all Phase B columns exist

---

## Test 9: GPU Pricing Table

**Verify GPU pricing table exists and has data.**

```powershell
docker exec nex-db psql -U nex -d nex -c "SELECT id, provider, gpu_type, hourly_rate_usd FROM gpu_pricing LIMIT 5;"
```

✅ **PASS** if table exists with RunPod pricing data

---

## Test 10: Run Unit Tests

**Run the Phase B unit tests.**

```powershell
docker exec nex-backend python -m pytest tests/test_phase_b.py -v
```

✅ **PASS** if all tests pass

---

## Summary Checklist

| Test | Description | Status |
|------|-------------|--------|
| 1 | GPU Pricing endpoint | ⬜ |
| 2 | Plan run (no match) | ⬜ |
| 3 | Plan run (force rerun) | ⬜ |
| 4 | Create run with cost | ⬜ |
| 5 | Get run cost | ⬜ |
| 6 | Compare runs | ⬜ |
| 7 | Retry endpoint | ⬜ |
| 8 | DB schema verification | ⬜ |
| 9 | GPU pricing table | ⬜ |
| 10 | Unit tests | ⬜ |

---

## Troubleshooting

### Migration not applied

```powershell
docker exec nex-backend alembic current
# Should show: 021_add_phase_b (head)

# If not, run:
docker exec nex-backend alembic upgrade head
```

### GPU pricing table empty

```powershell
# Re-run migration (it seeds data)
docker exec nex-backend alembic downgrade -1
docker exec nex-backend alembic upgrade head
```

### Endpoint not found

Check backend logs:
```powershell
docker logs nex-backend --tail 50
```

Restart backend:
```powershell
docker compose -p nex restart backend
```
