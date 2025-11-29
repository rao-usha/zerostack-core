# Testing Guide

## Quick Test Steps

### 1. Start Services

```bash
cd nex-collector
docker-compose up -d db redis
```

Wait ~10 seconds for services to be ready.

### 2. Create Initial Migration

```bash
docker-compose run --rm api alembic revision --autogenerate -m "initial_schema"
```

### 3. Apply Migrations

```bash
docker-compose run --rm api alembic upgrade head
```

### 4. Run Seed Script (requires OPENAI_API_KEY)

```bash
# Set your OpenAI API key
$env:OPENAI_API_KEY = "sk-..."

# Run seed script
docker-compose run --rm -e OPENAI_API_KEY=$env:OPENAI_API_KEY api python scripts/seed_demo.py
```

### 5. Inspect Generated Data

```bash
docker-compose run --rm api python scripts/inspect_data.py
```

### 6. Start API and Worker (optional)

```bash
# Start API
docker-compose up -d api

# Start worker (in another terminal)
docker-compose up -d worker

# View API docs
# Open http://localhost:8080/docs
```

## View Data in Database

### Using psql

```bash
docker-compose exec db psql -U postgres -d nex_collector
```

Then run SQL queries:
```sql
-- Count records
SELECT 'context_docs' as table_name, COUNT(*) FROM context_docs
UNION ALL
SELECT 'context_variants', COUNT(*) FROM context_variants
UNION ALL
SELECT 'underwriting_runs', COUNT(*) FROM underwriting_runs
UNION ALL
SELECT 'synthetic_examples', COUNT(*) FROM synthetic_examples
UNION ALL
SELECT 'teacher_runs', COUNT(*) FROM teacher_runs
UNION ALL
SELECT 'dataset_manifests', COUNT(*) FROM dataset_manifests;

-- View contexts
SELECT id, title, version, LENGTH(body_text) as body_length FROM context_docs;

-- View variants with underwriting
SELECT 
    v.id,
    v.domain,
    v.persona,
    v.task,
    u.decision,
    u.risk_score,
    u.utility_score
FROM context_variants v
LEFT JOIN LATERAL (
    SELECT decision, risk_score, utility_score
    FROM underwriting_runs
    WHERE variant_id = v.id
    ORDER BY created_at DESC
    LIMIT 1
) u ON true;

-- View examples with teacher outputs
SELECT 
    e.id,
    e.example_type,
    COUNT(tr.id) as teacher_run_count
FROM synthetic_examples e
LEFT JOIN teacher_runs tr ON tr.example_id = e.id
GROUP BY e.id, e.example_type;
```

### View Fine-Tune Pack Files

```bash
# List files in data directory
docker-compose exec api ls -la /code/data/packs/

# View manifest
docker-compose exec api cat /code/data/packs/*/manifest.json
```

## Troubleshooting

### Migration errors
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d db redis
docker-compose run --rm api alembic upgrade head
```

### Check logs
```bash
docker-compose logs api
docker-compose logs worker
```

