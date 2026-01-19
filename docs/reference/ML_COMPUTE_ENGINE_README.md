# ML Compute Engine

The ML Compute Engine provides reliable, cost-aware ML model execution with support for local, SSH, and RunPod cloud GPUs.

## Features

### Phase A (Complete)
- ✅ Highlighted Datasets catalog
- ✅ ModelRecipe registry
- ✅ Remote GPU execution (SSH adapter)
- ✅ Automatic results banking (DerivedAssets)
- ✅ Interaction logging
- ✅ Object storage integration (MinIO/S3)

### Phase B (Complete)
- ✅ **Cost Tracking** - Estimate and track costs per run
- ✅ **Reuse-Before-Rerun** - Avoid duplicate work, save money
- ✅ **Retry Logic** - Auto-retry failed GPU jobs
- ✅ **State Machine** - Clear run states and failure handling
- ✅ **RunPod Integration** - Cloud GPU execution

### Phase C (Planned)
- ⬜ Scheduled runs (cron-style)
- ⬜ Asset versioning/history
- ⬜ Multi-tenancy
- ⬜ Agent workflows

---

## Quick Start

### 1. Start Services

```powershell
docker compose -p nex up -d
```

### 2. Run Migrations

```powershell
cd backend
alembic upgrade head
```

### 3. Seed Data

```powershell
python -m scripts.seed_gpu_runner
```

---

## Using the Cost Tracker

### Check Cost Before Running

```powershell
$body = @{
    recipe_id = "recipe_m5_forecast_v1"
    recipe_version_id = "ver_m5_forecast_v1_100"
    parameters = @{ horizon = 28 }
} | ConvertTo-Json

Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/plan `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 5
```

Response:
```json
{
  "action": "PROCEED",
  "similarity_hash": "a1b2c3d4e5f6g7h8",
  "estimated_cost_usd": 0.20,
  "matching_run_count": 0,
  "reason": "No matching runs found"
}
```

### List GPU Pricing

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/gpu-pricing | ConvertTo-Json
```

### Get Run Cost After Completion

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/ml-development/runs/$runId/cost | ConvertTo-Json
```

---

## Using Reuse-Before-Rerun

The engine automatically checks for existing runs with identical inputs:

1. **Same recipe** + **Same dataset** + **Same parameters** = Same hash
2. If a matching successful run exists, you'll get `REUSE_RECOMMENDED`
3. You can either reuse the existing results or force a rerun

### Example: Reuse Recommended

```json
{
  "action": "REUSE_RECOMMENDED",
  "similarity_hash": "a1b2c3d4e5f6g7h8",
  "best_match_run_id": "run_abc123",
  "confidence": 0.95,
  "potential_savings_usd": 0.50,
  "reason": "Exact match found. Reuse strongly recommended."
}
```

### Force Rerun

Set `force_rerun: true` in your plan request to bypass reuse checking.

---

## RunPod Integration

### Configuration

Add to your `.env`:

```env
COMPUTE_ADAPTER=runpod
RUNPOD_API_KEY=your-api-key-here
RUNPOD_DEFAULT_GPU=NVIDIA RTX A4000
```

### Supported GPUs

| GPU | Hourly Rate | Memory |
|-----|-------------|--------|
| RTX A4000 | $0.20 | 16 GB |
| RTX A5000 | $0.30 | 24 GB |
| RTX 3090 | $0.22 | 24 GB |
| RTX 4090 | $0.44 | 24 GB |
| A40 | $0.39 | 48 GB |
| A100 40GB | $1.09 | 40 GB |
| A100 80GB | $1.69 | 80 GB |
| H100 80GB | $2.69 | 80 GB |

---

## Retry Logic

### Automatic Retries

When a run fails due to infrastructure issues (connection errors, GPU OOM, pod evictions), it automatically retries:

1. `RUNNING` → `RETRYING` (if retry_count < max_retries)
2. `RETRYING` → `SCHEDULED` (queued for retry)
3. After max retries → `FAILED` (terminal)

### Manual Retry

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/api/v1/ml-development/runs/$runId/retry `
  -ContentType "application/json" `
  -Body '{"max_retries": 5}'
```

### Failure Types

| Type | Description | Auto-Retry? |
|------|-------------|-------------|
| `infra` | Infrastructure (connection, OOM) | ✅ Yes |
| `timeout` | Job timeout | ✅ Yes |
| `model` | Model error (code bug) | ❌ No |

---

## Run States

```
QUEUED → SCHEDULED → RUNNING → SUCCEEDED
            ↓           ↓
         FAILED ←── RETRYING ──→ (back to SCHEDULED)
            ↓
        CANCELLED
```

---

## API Reference

### Cost & Reuse

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/runs/plan` | Pre-run decision |
| GET | `/runs/{id}/cost` | Cost breakdown |
| GET | `/gpu-pricing` | List GPU options |
| GET | `/runs/compare?run_ids=a,b,c` | Compare runs |

### Run Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/runs` | Create run |
| GET | `/runs/{id}` | Get run status |
| POST | `/runs/{id}/retry` | Retry failed run |
| POST | `/runs/{id}/cancel` | Cancel run |
| GET | `/runs/{id}/logs` | Get logs |
| POST | `/runs/{id}/bank` | Bank as asset |

---

## Testing

Run the Phase B tests:

```powershell
cd backend
python -m pytest tests/test_phase_b.py -v
```

---

## Troubleshooting

### RunPod Not Connecting

1. Check API key: `echo $env:RUNPOD_API_KEY`
2. Verify key at https://runpod.io/console/user/settings
3. Check logs: `docker logs nex-backend`

### Costs Not Tracking

1. Ensure migration ran: `alembic current` should show `021_add_phase_b`
2. Check gpu_pricing table has data

### Reuse Not Working

1. Check similarity hash is being recorded
2. Verify matching run exists and succeeded
3. Check parameters are exactly the same (order doesn't matter)
