# Environment Setup & Configuration

This guide covers environment variables, database configuration, and network setup.

## Environment Variables

### Required Variables

#### OPENAI_API_KEY

**Required** for LLM operations (context generation, teacher runs).

**Option 1: Use Root .env File (Recommended)**

The service automatically reads `OPENAI_API_KEY` from the root `.env` file:

```bash
# Root .env file (C:\Users\awron\projects\Nex\.env)
OPENAI_API_KEY=sk-your-key-here
```

The `start.bat` script automatically loads this.

**Option 2: Create nex-collector/.env**

Create `nex-collector/.env`:

```bash
OPENAI_API_KEY=sk-your-key-here
```

Docker Compose will automatically read this file.

**Option 3: Set Environment Variable**

```powershell
# PowerShell (temporary)
$env:OPENAI_API_KEY = "sk-your-key-here"

# PowerShell (permanent - User level)
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-your-key-here", "User")
```

### Optional Variables

#### NEX_WRITE_TOKEN

API authentication token (default: `dev-secret`).

```bash
NEX_WRITE_TOKEN=your-secret-token
```

#### DATA_DIR

Directory for dataset files (default: `./data`).

```bash
DATA_DIR=/path/to/custom/data
```

#### EMBEDDINGS_ENABLED

Enable text embeddings (default: `false`).

```bash
EMBEDDINGS_ENABLED=true
```

#### AGGREGATOR_INTERVAL_SECS

Interval for continuous aggregation in seconds (default: `3600`).

```bash
AGGREGATOR_INTERVAL_SECS=3600
```

## Database Configuration

### Shared Database Architecture

nex-collector **shares** the PostgreSQL database with the main NEX service:

- **Shared Container**: `nex_db` (from main NEX)
- **Separate Database**: `nex_collector` (vs `nex` for main NEX)
- **Same Credentials**: User `nex`, Password `nex`

### Database Connection

| Service | Database Name | User | Password | Container |
|---------|--------------|------|----------|-----------|
| Main NEX | `nex` | `nex` | `nex` | `nex_db` |
| nex-collector | `nex_collector` | `nex` | `nex` | `nex_db` (shared) |

Both use the **same PostgreSQL instance** but different database names for data isolation.

### Automatic Database Creation

The `db_check` service automatically:
1. Waits for `nex_db` to be ready
2. Creates the `nex_collector` database if it doesn't exist
3. Exits (one-time setup)

### Manual Database Creation

If needed, create manually:

```powershell
docker exec -it nex_db psql -U nex -d postgres -c "CREATE DATABASE nex_collector;"
```

### Database Access

```powershell
# Connect to nex_collector database
docker exec -it nex_db psql -U nex -d nex_collector

# List all databases
docker exec -it nex_db psql -U nex -d postgres -c "\l"

# List tables
docker exec -it nex_db psql -U nex -d nex_collector -c "\dt"
```

## Redis Configuration

nex-collector runs its own Redis instance to avoid conflicts:

- **Container**: `nex-collector_redis`
- **External Port**: `6380` (to avoid conflict with main NEX on `6379`)
- **Internal Port**: `6379`
- **Queue Name**: `nex_queue`

### Redis Connection

From host machine:
```powershell
redis-cli -p 6380
```

From Docker container:
```bash
redis-cli -h redis -p 6379
```

## Network Configuration

### Docker Network

Both services use the `nex-network` Docker network:

- **Created by**: Main NEX service (when you run `docker-compose up -d db`)
- **Purpose**: Allows services to communicate
- **Network Type**: Bridge network

### Manual Network Creation

If the network doesn't exist:

```powershell
docker network create nex-network
```

### Verify Network

```powershell
# List networks
docker network ls | findstr nex-network

# Inspect network
docker network inspect nex-network
```

## Port Configuration

### Port Assignments

To avoid conflicts with the main NEX service:

| Service | External Port | Internal Port | Notes |
|---------|--------------|---------------|-------|
| API | `8080` | `8080` | No conflict |
| Redis | `6380` | `6379` | Main NEX uses `6379` |
| Database | Shared | `5432` | Uses main NEX's `nex_db` |

### Changing Ports

To change the API port, edit `nex-collector/docker-compose.yml`:

```yaml
api:
  ports:
    - "8081:8080"  # Change external port to 8081
```

## Data Storage

### Database Storage

- **Location**: Docker volume (managed by Docker)
- **Access**: Via `docker exec` commands (see Database Access above)
- **Backup**: Use `pg_dump` (see below)

### File Storage

- **Location**: `nex-collector/data/` (local filesystem)
- **Structure**: See [DATA_STORAGE.md](DATA_STORAGE.md)
- **Persistent**: Files persist even if containers are removed

### Backup Database

```powershell
# Backup nex_collector database
docker exec nex_db pg_dump -U nex nex_collector > backup.sql

# Restore from backup
docker exec -i nex_db psql -U nex nex_collector < backup.sql
```

## Configuration Files

### docker-compose.yml

Main service configuration:
- Service definitions
- Port mappings
- Volume mounts
- Environment variables
- Network configuration

### .env Files

Environment variables can be set in:
1. Root `.env` (recommended)
2. `nex-collector/.env` (local override)
3. Environment variables (system level)

**Priority**: System env vars > `nex-collector/.env` > Root `.env`

## Troubleshooting

### Environment Variables Not Loading

1. **Check file location**: Ensure `.env` is in the correct location
2. **Check syntax**: No spaces around `=` sign: `KEY=value` not `KEY = value`
3. **Restart services**: `docker-compose restart`
4. **Check logs**: `docker-compose logs api | findstr OPENAI`

### Database Connection Issues

1. **Verify database exists**: `docker exec nex_db psql -U nex -d postgres -c "\l"`
2. **Check network**: `docker network inspect nex-network`
3. **Check credentials**: User `nex`, Password `nex`
4. **Check container**: `docker ps | findstr nex_db`

### Redis Connection Issues

1. **Check Redis is running**: `docker-compose ps redis`
2. **Check port**: Should be `6380` externally
3. **Check logs**: `docker-compose logs redis`

### Network Issues

1. **Verify network exists**: `docker network ls | findstr nex-network`
2. **Check containers on network**: `docker network inspect nex-network`
3. **Recreate network**: `docker network rm nex-network && docker network create nex-network`

## Summary

**Recommended Setup:**

1. ✅ Set `OPENAI_API_KEY` in root `.env` file
2. ✅ Start main NEX database: `docker-compose up -d db`
3. ✅ Run `.\nex-collector\start.bat` (handles everything else)

**Key Points:**

- Database is **shared** with main NEX (separate database name)
- Redis is **separate** (different port to avoid conflicts)
- Network is **shared** (`nex-network`)
- Environment variables load from root `.env` automatically

