# NEX Collector Database Setup & Data Seeding Guide

This guide walks you through setting up the nex-collector database and seeding it with retail and insurance underwriting data.

## Prerequisites

Before starting, ensure you have:

1. ✅ **Docker Desktop** installed and running
2. ✅ **Main NEX database** running (nex-collector shares this database)
3. ✅ **OPENAI_API_KEY** set in your root `.env` file (required for generating synthetic examples)

## Step 1: Start Main NEX Database

The nex-collector service shares the PostgreSQL database with the main NEX service but uses a separate database name (`nex_collector`).

```powershell
# From project root directory
docker-compose up -d db

# Verify it's running
docker ps | findstr nex_db
```

Wait a few seconds for the database to be ready.

## Step 2: Start nex-collector Services

```powershell
# From project root directory
cd nex-collector

# Start all services (database setup, migrations, API, worker)
docker-compose up -d

# Or use the convenience script
.\start.bat
```

The `start.bat` script automatically:
- ✅ Checks if main NEX database is running
- ✅ Creates the `nex_collector` database if needed
- ✅ Starts Redis
- ✅ Runs database migrations
- ✅ Starts API and worker services

## Step 3: Verify Services Are Running

```powershell
# Check all services
docker-compose ps

# You should see:
# - nex-collector_api_1 (Up)
# - nex-collector_worker_1 (Up)
# - nex-collector_redis_1 (Up)

# Check health endpoint
curl http://localhost:8080/healthz
# Should return: {"ok": true, "mode": "integration"}
```

## Step 4: Verify Database Setup

```powershell
# Connect to the database
docker exec -it nex_db psql -U nex -d nex_collector

# List all tables
\dt

# You should see tables like:
# - context_docs
# - context_variants
# - chunks
# - feature_vectors
# - synthetic_examples
# - teacher_runs
# - targets
# - dataset_manifests
# - quality_assessments

# Exit psql
\q
```

## Step 5: Seed Retail Data

The retail seed script creates:
- A retail context document
- A retail variant (domain='retail', persona='sales_associate')
- Synthetic examples (task, QA, and instruction types)
- A fine-tune pack dataset

```powershell
# From nex-collector directory
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_retail.py
```

**What this creates:**
- **Context**: `ctx-retail-v1` - Retail Sales & Customer Service Guidelines
- **Variant**: `var-retail-customer-service` (domain: retail, persona: sales_associate, task: customer_service)
- **Examples**: ~13 synthetic examples (5 task + 5 QA + 3 instruction)
- **Dataset**: `ds-retail-v1` - Fine-tune pack at `data/packs/retail-customer-service@1.0.0/`

**Expected Output:**
```
🛍️ Creating Retail Context...
   API: http://api:8080

1️⃣ Creating ContextDoc...
   ✓ Created ContextDoc: ctx-retail-v1

2️⃣ Creating ContextVariant (domain=retail, persona=sales_associate)...
   ✓ Created ContextVariant: var-retail-customer-service
      Domain: retail
      Persona: sales_associate
      Task: customer_service

3️⃣ Generating synthetic examples...
   ✓ Generated 5 task examples
   ✓ Generated 5 QA examples
   ✓ Generated 3 instruction examples

   ✓ Total examples created: 13

4️⃣ Building fine-tune pack dataset...
   ✓ Dataset built successfully!
      Dataset ID: ds-retail-v1
      Files: 2
        - train.jsonl: abc123...
        - eval.jsonl: def456...
      Examples: 13
      Train: 11, Eval: 2

✅ Retail context and synthetic dataset created successfully!
```

## Step 6: Seed Insurance Underwriting Data

The insurance underwriter seed script creates:
- An insurance underwriting context document
- An insurance variant (domain='insurance', persona='underwriter')
- Note: This script doesn't generate examples by default (you can add that step)

```powershell
# From nex-collector directory
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_insurance_underwriter.py
```

**What this creates:**
- **Context**: `ctx-insurance-underwriter-v1` - Insurance Underwriting Guidelines
- **Variant**: `var-insurance-underwriter-risk-assessment` (domain: insurance, persona: underwriter, task: risk_assessment)

**Expected Output:**
```
🏢 Creating Insurance Underwriter Context...
   API: http://api:8080

1️⃣ Creating ContextDoc...
   ✓ Created ContextDoc: ctx-insurance-underwriter-v1

2️⃣ Creating ContextVariant (domain=insurance, persona=underwriter)...
   ✓ Created ContextVariant: var-insurance-underwriter-risk-assessment
      Domain: insurance
      Persona: underwriter
      Task: risk_assessment

3️⃣ Querying variants by domain='insurance'...
   ✓ Found 1 variant(s) with domain='insurance'
      - var-insurance-underwriter-risk-assessment: underwriter (risk_assessment)

✅ Insurance Underwriter context created successfully!
```

## Step 7: (Optional) Generate Examples for Insurance Underwriting

If you want to generate synthetic examples for the insurance variant:

```powershell
# Use the API directly or create a script
curl -X POST http://localhost:8080/v1/datasets/distill/examples \
  -H "Content-Type: application/json" \
  -d '{
    "variant_ids": ["var-insurance-underwriter-risk-assessment"],
    "example_type": "task",
    "quota_per_variant": 10
  }'
```

Or use the insurance dataset seed script:

```powershell
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_insurance_dataset.py
```

## Step 8: Verify Data in Database

### Check Contexts

```powershell
# Connect to database
docker exec -it nex_db psql -U nex -d nex_collector

# Query context docs
SELECT id, title, version FROM context_docs;

# Should show:
# - ctx-retail-v1
# - ctx-insurance-underwriter-v1

# Query variants
SELECT id, domain, persona, task FROM context_variants;

# Should show:
# - var-retail-customer-service (retail, sales_associate, customer_service)
# - var-insurance-underwriter-risk-assessment (insurance, underwriter, risk_assessment)

# Count examples
SELECT variant_id, example_type, COUNT(*) 
FROM synthetic_examples 
GROUP BY variant_id, example_type;

# Exit
\q
```

### Check via API

```powershell
# List all variants
curl http://localhost:8080/v1/contexts/variants

# Filter by domain
curl "http://localhost:8080/v1/contexts/variants?domain=retail"
curl "http://localhost:8080/v1/contexts/variants?domain=insurance"

# Get specific variant
curl http://localhost:8080/v1/contexts/variants/var-retail-customer-service
curl http://localhost:8080/v1/contexts/variants/var-insurance-underwriter-risk-assessment

# List datasets
curl http://localhost:8080/v1/datasets
```

### Check Dataset Files

```powershell
# List dataset files
dir nex-collector\data\packs

# View dataset manifest
type nex-collector\data\packs\retail-customer-service@1.0.0\manifest.json

# View training examples (first few lines)
Get-Content nex-collector\data\packs\retail-customer-service@1.0.0\train.jsonl | Select-Object -First 3
```

## Step 9: Explore Data in UI

1. **Start the frontend** (if not already running):
   ```powershell
   # From project root
   cd frontend
   npm run dev
   ```

2. **Open the Data Explorer**:
   - Navigate to http://localhost:3000/explorer
   - Select `context_variants` table to see retail and insurance variants
   - Select `synthetic_examples` table to see generated examples
   - Select `dataset_manifests` table to see built datasets

3. **Open the Distillation Explorer**:
   - Navigate to http://localhost:3000/distillation
   - Click on "Variants" to see all variants
   - Click on "Examples" to see synthetic examples
   - Click on "Datasets" to see built datasets

## Troubleshooting

### Database Not Found

If you get an error about the database not existing:

```powershell
# Create the database manually
docker exec -it nex_db psql -U nex -d postgres -c "CREATE DATABASE nex_collector;"

# Then run migrations
cd nex-collector
docker-compose run --rm api alembic upgrade head
```

### Seed Scripts Fail

If seed scripts fail:

1. **Check API is running**:
   ```powershell
   curl http://localhost:8080/healthz
   ```

2. **Check logs**:
   ```powershell
   docker-compose logs api
   ```

3. **Verify environment variables**:
   ```powershell
   docker-compose exec api env | findstr OPENAI
   ```

4. **Try running with explicit API URL**:
   ```powershell
   docker-compose run --rm -e API_BASE=http://localhost:8080 -e NEX_WRITE_TOKEN=dev-secret api python scripts/seed_retail.py
   ```

### Examples Not Generated

If examples aren't generated:

1. **Check worker is running**:
   ```powershell
   docker-compose ps worker
   ```

2. **Check worker logs**:
   ```powershell
   docker-compose logs worker
   ```

3. **Verify OPENAI_API_KEY is set**:
   ```powershell
   docker-compose exec api env | findstr OPENAI
   ```

### Data Already Exists

If you see "already exists" messages, that's fine! The scripts are idempotent and will use existing data. To start fresh:

```powershell
# Connect to database
docker exec -it nex_db psql -U nex -d nex_collector

# Delete specific data (be careful!)
DELETE FROM synthetic_examples WHERE variant_id = 'var-retail-customer-service';
DELETE FROM context_variants WHERE id = 'var-retail-customer-service';
DELETE FROM context_docs WHERE id = 'ctx-retail-v1';

# Or reset entire database (WARNING: deletes all data)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO nex;

# Then run migrations again
docker-compose run --rm api alembic upgrade head
```

## Quick Reference

### Database Connection
```powershell
docker exec -it nex_db psql -U nex -d nex_collector
```

### API Endpoints
- Health: `http://localhost:8080/healthz`
- Docs: `http://localhost:8080/docs`
- Variants: `http://localhost:8080/v1/contexts/variants`
- Datasets: `http://localhost:8080/v1/datasets`

### Seed Scripts Location
- `nex-collector/scripts/seed_retail.py`
- `nex-collector/scripts/seed_insurance_underwriter.py`
- `nex-collector/scripts/seed_insurance_dataset.py`

### Dataset Files Location
- `nex-collector/data/packs/{name}@{version}/`

## Summary

**Complete Setup Steps:**

```powershell
# 1. Start main NEX database
docker-compose up -d db

# 2. Start nex-collector
cd nex-collector
.\start.bat

# 3. Seed retail data
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_retail.py

# 4. Seed insurance underwriting data
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_insurance_underwriter.py

# 5. (Optional) Generate insurance examples
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_insurance_dataset.py

# 6. Verify
curl http://localhost:8080/v1/contexts/variants
```

Done! 🎉

You now have:
- ✅ Database set up with all tables
- ✅ Retail context and variant with examples
- ✅ Insurance underwriting context and variant
- ✅ Dataset files ready for fine-tuning

