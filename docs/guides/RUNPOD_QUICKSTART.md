# RunPod GPU Compute - User Guide

> Train ML models on cloud GPUs with one click from the NEX UI

## What You Can Do

✅ **Run forecasting recipes** on RunPod GPU cloud  
✅ **See costs before running** - estimated cost shown upfront  
✅ **Track progress** - real-time status updates in the UI  
✅ **View results** - metrics and logs displayed when complete  
✅ **Compare runs** - side-by-side comparison of multiple runs  

---

## Prerequisites

Before you start, make sure:

1. **NEX is running** - `docker compose -p nex up -d`
2. **RunPod API key is configured** - See [Setup](#setup-runpod) below
3. **You have a RunPod account** - Sign up at [runpod.io](https://runpod.io)

---

## Setup RunPod

### 1. Get Your API Key

1. Go to [RunPod Settings](https://www.runpod.io/console/user/settings)
2. Click **"API Keys"** in the sidebar
3. Click **"Create API Key"**
4. Copy the key

### 2. Configure NEX

Add to your `.env` file in the project root:

```env
COMPUTE_ADAPTER=runpod
RUNPOD_API_KEY=your-api-key-here
RUNPOD_DEFAULT_GPU=NVIDIA RTX A4000
```

### 3. Restart NEX

```powershell
docker compose -p nex down
docker compose -p nex up -d
```

---

## Step-by-Step: Run a Recipe on RunPod

### Step 1: Open Model Development

1. Open NEX in your browser: **http://localhost:3000**
2. Click **"Model Development"** in the sidebar

![Model Development](../images/model-dev-sidebar.png)

### Step 2: Browse Recipes

1. You'll see the **Recipes** tab by default
2. Browse available recipes (Forecasting, Pricing, etc.)
3. Click on a recipe card to view details

| Recipe | Description |
|--------|-------------|
| **Forecasting Base** | M5-style time series forecasting |
| **Pricing Base** | Price elasticity modeling |
| **Location Scoring** | Location scoring models |

### Step 3: View Recipe Details

1. Click a recipe to open its detail page
2. Review the recipe metadata and manifest
3. Click **"Run Recipe"** button (top right)

### Step 4: Configure Your Run

In the Run Configuration dialog:

| Field | Description | Example |
|-------|-------------|---------|
| **Compute Target** | Where to run | `runpod` |
| **Parameters** | Recipe-specific settings | `horizon: 28` |

Click **"Create Run"** to start.

### Step 5: Monitor Progress

1. You'll be taken to the **Runs** tab
2. Find your run (most recent at top)
3. Click to view details

**Run Statuses:**
- 🔘 **queued** - Waiting to start
- 🔵 **scheduled** - Submitted to RunPod
- 🔄 **running** - Executing on GPU
- ✅ **succeeded** - Complete!
- ❌ **failed** - Error occurred

### Step 6: View Results

Once complete, the Run Detail page shows:

- **Metrics** - MAE, RMSE, R², etc.
- **Artifacts** - Model files, predictions
- **Logs** - Full execution logs
- **Cost** - Actual cost incurred

---

## Run Comparison

Compare multiple runs side-by-side:

1. Go to **Model Development** → **Runs** tab
2. Note the Run IDs you want to compare
3. Navigate to: **http://localhost:3000/model-development/runs/compare**
4. Enter 2-5 Run IDs
5. Click **Compare**

You'll see:
- Side-by-side metrics
- Best/worst highlighted
- Cost comparison

---

## Available GPU Types

| GPU | Hourly Cost | Best For |
|-----|-------------|----------|
| RTX A4000 | ~$0.20/hr | Small-medium jobs |
| RTX A5000 | ~$0.30/hr | Medium jobs |
| A100 40GB | ~$1.09/hr | Large jobs |
| A100 80GB | ~$1.69/hr | Very large jobs |

---

## Tips & Best Practices

### 💰 Save Money

- **Use the Plan feature** - Check if similar run exists before starting
- **Start small** - Test with smaller datasets first
- **Use A4000** - Good balance of cost/performance

### ⏱️ Save Time

- **Reuse results** - NEX detects identical runs and can reuse outputs
- **Batch similar runs** - Slight parameter changes can reuse cached data

### 🔍 Debug Issues

1. Check **Run Detail** page for logs
2. Look for `failure_reason` field
3. Common issues:
   - GPU out of memory → Try smaller batch size
   - Timeout → Increase max runtime
   - Data not found → Check dataset configuration

---

## Troubleshooting

### "No recipes found"

Make sure recipes are seeded:
```powershell
docker exec nex-backend python -c "from scripts.seed_ml_recipes import seed_recipes; seed_recipes()"
```

### Run stuck in "queued"

1. Check backend logs:
   ```powershell
   docker logs nex-backend --tail 50
   ```
2. Verify RunPod API key is set:
   ```powershell
   docker exec nex-backend env | Select-String RUNPOD
   ```

### Run failed immediately

1. Check the `failure_reason` on the Run Detail page
2. Common causes:
   - Invalid API key
   - Insufficient RunPod credits
   - Container image not found

### Cost not showing

Ensure gpu_pricing table has data:
```powershell
docker exec nex-db psql -U nex -d nex -c "SELECT COUNT(*) FROM gpu_pricing;"
```

---

## API Reference (Advanced)

For automation or advanced usage, see the [ML Compute Engine API Guide](./ML_COMPUTE_ENGINE.md).

---

## Next Steps

- [Compare Runs](./ML_COMPUTE_ENGINE.md#compare-runs) - Analyze multiple experiments
- [Set Up Drift Detection](./ML_COMPUTE_ENGINE.md#drift-detection) - Monitor model performance
- [Schedule Recurring Runs](./ML_COMPUTE_ENGINE.md#scheduled-runs) - Automate retraining
