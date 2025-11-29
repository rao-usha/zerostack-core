# Quick Test Guide

## Option 1: Docker (Recommended - but takes time to build)

```bash
cd nex-collector

# 1. Start services
docker-compose up -d db redis

# 2. Wait for services (10 seconds)
Start-Sleep -Seconds 10

# 3. Create and apply migrations
docker-compose run --rm api alembic revision --autogenerate -m "initial"
docker-compose run --rm api alembic upgrade head

# 4. Run seed script (set OPENAI_API_KEY first)
$env:OPENAI_API_KEY = "sk-..."
docker-compose run --rm -e OPENAI_API_KEY=$env:OPENAI_API_KEY api python scripts/seed_demo.py

# 5. Inspect data
docker-compose run --rm api python scripts/inspect_data.py
```

## Option 2: Local Testing (Faster - requires local Postgres/Redis)

### Prerequisites
- PostgreSQL running on localhost:5432
- Redis running on localhost:6379
- Python 3.11+ with virtual environment

### Steps

```bash
cd nex-collector

# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/nex_collector"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:OPENAI_API_KEY = "sk-..."  # Your key

# 4. Create database
# Connect to Postgres and run:
# CREATE DATABASE nex_collector;

# 5. Run migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head

# 6. Run seed script
python scripts/seed_demo.py

# 7. Inspect data
python scripts/inspect_data.py
```

## Option 3: Manual API Testing (No seed script)

If you don't have OPENAI_API_KEY, you can still test the API manually:

```bash
# Start services
docker-compose up -d

# Create a context manually
curl -X POST http://localhost:8080/v1/contexts \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "ctx-test",
    "title": "Test Context",
    "version": "1.0.0",
    "body_text": "This is a test context document with financial analysis guidelines.",
    "metadata_json": {}
  }'

# Create a variant
curl -X POST http://localhost:8080/v1/contexts/ctx-test/variants \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "var-test",
    "context_id": "ctx-test",
    "domain": "finance",
    "persona": "CFO",
    "task": "analyze",
    "style": "formal",
    "body_text": "This is a test context document with financial analysis guidelines.",
    "constraints_json": {}
  }'

# Run underwriting
curl -X POST "http://localhost:8080/v1/underwrite/run?variant_id=var-test" \
  -H "Authorization: Bearer dev-secret"

# Inspect data
docker-compose run --rm api python scripts/inspect_data.py
```

## View Data

### Using inspect script
```bash
docker-compose run --rm api python scripts/inspect_data.py
```

### Using psql
```bash
docker-compose exec db psql -U postgres -d nex_collector

# Then run:
SELECT * FROM context_docs;
SELECT * FROM context_variants;
SELECT * FROM underwriting_runs;
```

### View files
```bash
# List dataset files
docker-compose exec api ls -la /code/data/

# View manifest
docker-compose exec api cat /code/data/packs/*/manifest.json
```

