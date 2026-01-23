# ML Compute Engine - User Guide

> Run ML models on cloud GPUs with cost tracking and smart reuse

---

## 🚀 Quick Start

**New to RunPod?** → [**UI Quick Start Guide**](./RUNPOD_QUICKSTART.md) - Step-by-step with screenshots

**Want API access?** → Continue reading below for full API reference

---

## What This Does

The ML Compute Engine lets you:
- **Run ML recipes** on local Docker, remote SSH, or RunPod cloud GPUs
- **See costs before you run** - know exactly what you'll spend
- **Avoid duplicate work** - automatically detect if you've run the same thing before
- **Auto-retry failures** - infrastructure issues retry automatically
- **Track everything** - full history of runs, costs, and results

---

## Quick Start

### 1. Check Available GPUs & Pricing

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/gpu-pricing | ConvertTo-Json -Depth 3
```

Output:
```json
[
  { "id": "local_any", "provider": "local", "gpu_type": "any", "hourly_rate_usd": 0.0 },
  { "id": "runpod_rtx_a4000", "provider": "runpod", "gpu_type": "NVIDIA RTX A4000", "hourly_rate_usd": 0.2 },
  { "id": "runpod_a100_40gb", "provider": "runpod", "gpu_type": "NVIDIA A100 40GB", "hourly_rate_usd": 1.09 }
]
```

### 2. Plan Before Running (Check for Reuse)

Before starting a run, **always plan first** to see if you can reuse existing results:

```powershell
$planRequest = @{
    recipe_id = "recipe_m5_forecast_v1"
    recipe_version_id = "ver_m5_forecast_v1_100"
    dataset_version_id = "m5_sales_v1"
    parameters = @{ horizon = 28; learning_rate = 0.1 }
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/plan `
    -ContentType "application/json" `
    -Body $planRequest | ConvertTo-Json -Depth 3
```

**Response - No Match (Proceed):**
```json
{
  "action": "PROCEED",
  "similarity_hash": "a1b2c3d4e5f67890",
  "estimated_cost_usd": 0.20,
  "matching_run_count": 0,
  "reason": "No matching runs found"
}
```

**Response - Match Found (Reuse):**
```json
{
  "action": "REUSE_RECOMMENDED",
  "similarity_hash": "a1b2c3d4e5f67890",
  "best_match_run_id": "run_abc123",
  "confidence": 0.95,
  "potential_savings_usd": 0.50,
  "reason": "Exact match found (run run_abc123). Reuse strongly recommended."
}
```

### 3. Create a Run

If plan says PROCEED:

```powershell
$runRequest = @{
    recipe_id = "recipe_m5_forecast_v1"
    recipe_version_id = "ver_m5_forecast_v1_100"
    dataset_version_id = "m5_sales_v1"
    parameters = @{ horizon = 28 }
} | ConvertTo-Json

$run = Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs `
    -ContentType "application/json" `
    -Body $runRequest

Write-Host "Run ID: $($run.id)"
```

### 4. Check Run Status

```powershell
$runId = "your-run-id"
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs/$runId | ConvertTo-Json
```

States:
- `queued` → Waiting to start
- `scheduled` → Assigned to compute
- `running` → Executing
- `succeeded` → Done!
- `failed` → Error (check failure_reason)
- `retrying` → Auto-retrying

### 5. Get Cost After Completion

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs/$runId/cost | ConvertTo-Json
```

```json
{
  "run_id": "run_abc123",
  "estimated_cost_usd": 0.20,
  "actual_cost_usd": 0.08,
  "runtime_seconds": 1440,
  "gpu_type": "NVIDIA RTX A4000"
}
```

---

## Compute Adapters

### Local (Default - Free)

Runs on your local Docker. Good for testing.

```env
COMPUTE_ADAPTER=local
```

### RunPod (Cloud GPUs)

Pay-per-use cloud GPUs. Great for production.

```env
COMPUTE_ADAPTER=runpod
RUNPOD_API_KEY=your-key-here
RUNPOD_DEFAULT_GPU=NVIDIA RTX A4000
```

Get your API key: https://www.runpod.io/console/user/settings

### SSH (Your Own GPU Server)

Run on a remote machine you own.

```env
COMPUTE_ADAPTER=ssh
SSH_HOST=gpu-server.example.com
SSH_USER=ubuntu
SSH_KEY_PATH=/path/to/key.pem
```

---

## Smart Features

### Reuse Detection

The engine creates a **similarity hash** from:
- Recipe ID
- Dataset version
- Parameters (order doesn't matter)

Same inputs = same hash = candidate for reuse.

**Force a new run** even if match exists:
```powershell
$planRequest = @{
    recipe_id = "recipe_m5_forecast_v1"
    recipe_version_id = "ver_m5_forecast_v1_100"
    parameters = @{}
    force_rerun = $true  # <-- Bypass reuse
} | ConvertTo-Json
```

### Auto-Retry

Infrastructure failures automatically retry:
- Connection errors
- GPU out of memory
- Pod evictions
- Timeouts

Model errors (code bugs) do **not** retry.

Default: 2 retries. Configure per-run:
```json
{ "max_retries": 5 }
```

### Manual Retry

If a run failed and you want to try again:

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/$runId/retry `
    -ContentType "application/json" `
    -Body '{"max_retries": 3}'
```

---

## Compare Runs

Compare metrics across multiple runs:

```powershell
$runIds = "run_abc,run_def,run_ghi"
Invoke-RestMethod "http://localhost:8000/api/v1/ml-development/runs/compare?run_ids=$runIds" | ConvertTo-Json -Depth 5
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/gpu-pricing` | List GPU options & prices |
| POST | `/runs/plan` | Check reuse before running |
| POST | `/runs` | Create a new run |
| GET | `/runs/{id}` | Get run status |
| GET | `/runs/{id}/cost` | Get cost breakdown |
| POST | `/runs/{id}/retry` | Retry a failed run |
| POST | `/runs/{id}/cancel` | Cancel a running job |
| GET | `/runs/{id}/logs` | Get run logs |
| GET | `/runs/compare?run_ids=a,b,c` | Compare multiple runs |
| POST | `/runs/{id}/bank` | Save results as asset |

All endpoints are prefixed with `/api/v1/ml-development`

---

## Troubleshooting

### "RUNPOD_API_KEY not configured"

Add to your `.env` file:
```env
COMPUTE_ADAPTER=runpod
RUNPOD_API_KEY=your-key
```

Then restart:
```powershell
docker compose -p nex down
docker compose -p nex up -d
```

### Run stuck in "queued"

Check backend logs:
```powershell
docker logs nex-backend --tail 100
```

### Cost not tracking

1. Run migration: `alembic upgrade head`
2. Check gpu_pricing table has data

### Reuse not detecting matches

- Parameters must be **exactly** the same (values, not just keys)
- Matching run must have status `succeeded`
- Matching run must be < 30 days old

---

---

## Phase 2 Features (Complete)

### Drift Detection 🚨

Monitor metrics and get alerts when they change significantly.

```powershell
# Create a drift check
$body = @{
    name = "Forecast RMSE Monitor"
    metric = "rmse"
    threshold = 0.10
    comparison = "percentage_both"
    recipe_id = "recipe_m5_forecast_v1"
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/drift/checks `
    -ContentType "application/json" -Body $body | ConvertTo-Json

# Check alerts
Invoke-RestMethod http://localhost:8000/api/v1/drift/alerts | ConvertTo-Json
```

### Scheduled Runs ⏰

Set up recurring runs with cron expressions.

```powershell
# Create weekly forecast schedule
$body = @{
    name = "Weekly M5 Forecast"
    recipe_id = "recipe_m5_forecast_v1"
    cron_expression = "0 9 * * 1"  # Monday 9am
    timezone = "UTC"
    use_reuse_engine = $true
    notify_on_failure = $true
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/schedules `
    -ContentType "application/json" -Body $body | ConvertTo-Json

# Trigger manually
Invoke-RestMethod -Method POST http://localhost:8000/api/v1/schedules/{id}/trigger
```

### Asset Versioning 📚

Track history of derived assets.

```powershell
# Get asset version history
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/assets/{id}/history | ConvertTo-Json -Depth 4

# Compare versions
Invoke-RestMethod "http://localhost:8000/api/v1/ml-development/assets/compare?version1_id=xxx&version2_id=yyy"
```

### Run Comparison UI 📊

Compare multiple runs side-by-side at:
**http://localhost:3000/model-development/runs/compare**

---

## Phase 3 (Coming Soon)

- **Multi-Tenancy** - Multiple users with quotas
- **Agent Workflows** - AI decides when to run vs reuse
- **Governance** - Approval workflows for expensive runs
