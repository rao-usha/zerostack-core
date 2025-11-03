# Quick Start - Database Setup

## 1. Start Database

```bash
# Start Postgres with Docker Compose
docker compose up -d db

# Or for development
docker compose -f docker-compose.dev.yml up -d db
```

## 2. Install Dependencies & Run Migrations

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

## 3. Seed Test Data (Optional)

```bash
python scripts/seed_minimal.py
```

## 4. Verify Setup

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"NEX.AI API","database":"connected"}
```

## What Was Created

- ✅ Postgres database with pgvector support
- ✅ Database schema with all tables (orgs, users, connectors, datasets, contexts, personas, evaluations, policies, jobs, etc.)
- ✅ Alembic migrations setup
- ✅ Seed script for test data
- ✅ Health check endpoint with DB connectivity test

## Database Location

- **From host machine**: `localhost:5432`
- **From containers**: `db:5432`
- **Credentials**: `nex/nex`
- **Database**: `nex`

See `DB_SETUP.md` for detailed documentation.

