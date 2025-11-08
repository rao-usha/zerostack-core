# Getting Started with NEX Context Aggregator

This guide will help you get the service up and running quickly.

## Prerequisites

Before starting, ensure you have:

1. ✅ **Docker Desktop** installed and running
2. ✅ **Main NEX database** running (nex-collector shares this database)
3. ✅ **OPENAI_API_KEY** set in your root `.env` file (see [SETUP.md](SETUP.md) for details)

## Quick Start (Easiest Method)

### Step 1: Start Main NEX Database

```powershell
# From project root directory
docker-compose up -d db
```

Wait a few seconds for the database to be ready. Verify it's running:

```powershell
docker ps | findstr nex_db
```

### Step 2: Start nex-collector

```powershell
# From project root directory
.\nex-collector\start.bat
```

That's it! The script will:
- ✅ Check if main NEX database is running
- ✅ Create the `nex_collector` database if needed
- ✅ Start Redis
- ✅ Run database migrations
- ✅ Start API and worker services

### Step 3: Verify It's Running

```powershell
# Check health endpoint
curl http://localhost:8080/healthz

# Should return: {"ok": true}

# View API documentation
# Open in browser: http://localhost:8080/docs
```

## Manual Setup (If Needed)

If you prefer to run commands manually or troubleshoot:

### Step 1: Start Main NEX Database

```powershell
# From project root
docker-compose up -d db

# Verify it's running
docker ps | findstr nex_db
```

### Step 2: Navigate to nex-collector

```powershell
cd nex-collector
```

### Step 3: Start Redis and Database Setup

```powershell
docker-compose up -d redis db_check
```

The `db_check` service will create the `nex_collector` database automatically.

### Step 4: Run Migrations (First Time Only)

```powershell
# Apply migrations
docker-compose run --rm api alembic upgrade head
```

### Step 5: Start API and Worker

```powershell
docker-compose up -d api worker
```

### Step 6: Verify Services

```powershell
# Check all services
docker-compose ps

# You should see:
# - nex-collector_api_1 (Up)
# - nex-collector_worker_1 (Up)
# - nex-collector_redis_1 (Up)
```

## Access Points

Once running, you can access:

- **API**: http://localhost:8080
- **Swagger Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/healthz

## Running Seed Scripts

### Create Insurance Underwriter Context

```powershell
cd nex-collector
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_insurance_underwriter.py
```

### Generate Synthetic Dataset

```powershell
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_insurance_dataset.py
```

## Viewing Logs

```powershell
cd nex-collector

# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api
docker-compose logs -f worker
```

## Stopping Services

```powershell
cd nex-collector
docker-compose down
```

**Note**: This stops nex-collector but keeps the main NEX database running.

## Troubleshooting

### Error: "nex_db not found"

**Solution**: Start main NEX database first:

```powershell
# From project root
docker-compose up -d db
```

### Error: "network nex-network not found"

**Solution**: Start main NEX first (it creates the network):

```powershell
docker-compose up -d db
```

Or create it manually:

```powershell
docker network create nex-network
```

### Error: "OPENAI_API_KEY not set"

**Solution**: See [SETUP.md](SETUP.md) for environment variable setup.

### Port Already in Use

If port 8080 is already in use, edit `nex-collector/docker-compose.yml`:

```yaml
ports:
  - "8081:8080"  # Change to different port
```

### Services Won't Start

1. Check Docker Desktop is running
2. Check main NEX database is running: `docker ps | findstr nex_db`
3. Check logs: `docker-compose logs api`
4. Try restarting: `docker-compose restart`

## Next Steps

- 📖 Read [SETUP.md](SETUP.md) for environment configuration
- 📊 See [DATA_STRUCTURE.md](DATA_STRUCTURE.md) to understand the data model
- 🔧 Check [USAGE_GUIDE.md](USAGE_GUIDE.md) for API usage examples

## Summary

**Easiest way to run:**

```powershell
# 1. Start main NEX database
docker-compose up -d db

# 2. Start nex-collector
.\nex-collector\start.bat

# 3. Test it
curl http://localhost:8080/healthz
```

Done! 🎉

