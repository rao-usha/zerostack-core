# Database Setup Guide

This document describes the database setup for Nex using PostgreSQL with pgvector.

## Quick Start

### 1. Start the Database

Using Docker Compose (recommended):

```bash
# Production/standard setup
docker compose up -d db

# Development setup
docker compose -f docker-compose.dev.yml up -d db
```

The database will be available at:
- **Host**: `localhost` (from host) or `db` (from containers)
- **Port**: `5432`
- **Database**: `nex`
- **User**: `nex`
- **Password**: `nex`

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key dependencies:
- `sqlalchemy` - ORM
- `alembic` - Database migrations
- `psycopg[binary]` - PostgreSQL driver
- `sqlmodel` - Optional ORM layer

### 3. Run Migrations

```bash
cd backend
alembic upgrade head
```

This will create all database tables defined in `backend/db/models.py`.

### 4. Seed Test Data (Optional)

```bash
cd backend
python scripts/seed_minimal.py
```

This creates:
- A demo organization ("Demo Org")
- A demo user (demo@nex.ai with admin role)

## Database Schema

The database includes the following main tables:

### Core Tables
- **orgs** - Organizations/tenants
- **users** - User accounts
- **connectors** - Data source connectors (Postgres, Snowflake, S3, HTTP, etc.)
- **datasets** - Dataset registry
- **dataset_versions** - Version tracking for datasets

### Context & Personas
- **contexts** - Context definitions
- **context_versions** - Versioned contexts with data references
- **personas** - User personas with constraints

### Evaluation & Governance
- **eval_scenarios** - Evaluation test scenarios
- **eval_runs** - Evaluation run results
- **policies** - Governance policies
- **audit_log** - Audit trail

### Jobs
- **jobs** - Async job queue

## Working with Migrations

### Create a New Migration

```bash
cd backend
alembic revision -m "description_of_changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1  # Rollback one version
alembic downgrade base  # Rollback all
```

### View Migration History

```bash
alembic history
```

### Check Current Database Version

```bash
alembic current
```

## Configuration

Database connection is configured in `backend/core/config.py`:

```python
database_url: str = "postgresql+psycopg://nex:nex@localhost:5432/nex"
```

You can override this with environment variables:
```bash
export DATABASE_URL=postgresql+psycopg://user:password@host:port/dbname
```

Or in a `.env` file:
```
DATABASE_URL=postgresql+psycopg://nex:nex@localhost:5432/nex
```

## Health Check

Test database connectivity:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "NEX.AI API",
  "database": "connected"
}
```

## Local Development (without Docker)

### Install PostgreSQL

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-16 postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

### Create Database

```bash
psql -U postgres
CREATE DATABASE nex;
CREATE USER nex WITH PASSWORD 'nex';
GRANT ALL PRIVILEGES ON DATABASE nex TO nex;
\q
```

### Install pgvector Extension

```bash
psql -U nex -d nex -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Production Considerations

1. **Change default credentials** - Update `POSTGRES_USER`, `POSTGRES_PASSWORD` in docker-compose.yml
2. **Use managed PostgreSQL** - Consider AWS RDS, Google Cloud SQL, or Azure Database
3. **Enable SSL/TLS** - Use connection strings with SSL parameters
4. **Set up backups** - Configure automated backups
5. **Connection pooling** - Add pgBouncer for high-traffic scenarios
6. **Monitoring** - Set up slow query logging and metrics collection

## Troubleshooting

### Database Connection Errors

1. **Check if database is running:**
   ```bash
   docker compose ps db
   ```

2. **Check logs:**
   ```bash
   docker compose logs db
   ```

3. **Test connection manually:**
   ```bash
   psql -h localhost -U nex -d nex
   ```

### Migration Errors

1. **Check Alembic configuration:**
   - Verify `alembic.ini` has correct `sqlalchemy.url`
   - Ensure `migrations/env.py` imports models correctly

2. **Reset database (⚠️ DESTRUCTIVE):**
   ```bash
   docker compose down -v  # Removes volumes
   docker compose up -d db
   alembic upgrade head
   ```

### Port Already in Use

If port 5432 is already in use:
1. Change port mapping in docker-compose.yml: `"5433:5432"`
2. Update `DATABASE_URL` accordingly

## Next Steps

- Implement service layer to interact with database tables
- Add indexes for performance
- Set up data retention policies for audit logs
- Configure connection pooling for production

