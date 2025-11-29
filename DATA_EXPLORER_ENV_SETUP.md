# Data Explorer - Environment Setup Reference

Quick reference for setting up Data Explorer database connection.

## Environment Variables

Add these to your backend environment:

```bash
EXPLORER_DB_HOST=localhost
EXPLORER_DB_PORT=5433
EXPLORER_DB_USER=nexdata
EXPLORER_DB_PASSWORD=nexdata_dev_password
EXPLORER_DB_NAME=nexdata
```

## Setup Options

### Option 1: .env File (Recommended for Local Development)

Create `backend/.env`:

```bash
# Copy these lines
EXPLORER_DB_HOST=localhost
EXPLORER_DB_PORT=5433
EXPLORER_DB_USER=nexdata
EXPLORER_DB_PASSWORD=nexdata_dev_password
EXPLORER_DB_NAME=nexdata
```

Then start normally:
```bash
cd backend
uvicorn main:app --reload
```

### Option 2: Shell Export (Linux/Mac)

```bash
export EXPLORER_DB_HOST=localhost
export EXPLORER_DB_PORT=5433
export EXPLORER_DB_USER=nexdata
export EXPLORER_DB_PASSWORD=nexdata_dev_password
export EXPLORER_DB_NAME=nexdata

# Then start
cd backend
uvicorn main:app --reload
```

### Option 3: PowerShell (Windows)

```powershell
$env:EXPLORER_DB_HOST="localhost"
$env:EXPLORER_DB_PORT="5433"
$env:EXPLORER_DB_USER="nexdata"
$env:EXPLORER_DB_PASSWORD="nexdata_dev_password"
$env:EXPLORER_DB_NAME="nexdata"

# Then start
cd backend
uvicorn main:app --reload
```

### Option 4: Inline with uvicorn (Linux/Mac)

```bash
cd backend
EXPLORER_DB_HOST=localhost \
EXPLORER_DB_PORT=5433 \
EXPLORER_DB_USER=nexdata \
EXPLORER_DB_PASSWORD=nexdata_dev_password \
EXPLORER_DB_NAME=nexdata \
uvicorn main:app --reload
```

### Option 5: Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - EXPLORER_DB_HOST=postgres
      - EXPLORER_DB_PORT=5432
      - EXPLORER_DB_USER=nexdata
      - EXPLORER_DB_PASSWORD=nexdata_dev_password
      - EXPLORER_DB_NAME=nexdata
```

## Quick Test

After setting variables, test connection:

```bash
curl http://localhost:8000/api/v1/data-explorer/health
```

Expected output (if connected):
```json
{
  "connected": true,
  "database": "nexdata",
  "version": "PostgreSQL ...",
  "host": "localhost",
  "port": 5433
}
```

## Database Setup (PostgreSQL)

If you need to create the database and user:

```sql
-- As postgres superuser
CREATE DATABASE nexdata;
CREATE USER nexdata WITH PASSWORD 'nexdata_dev_password';
GRANT CONNECT ON DATABASE nexdata TO nexdata;
GRANT USAGE ON SCHEMA public TO nexdata;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nexdata;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO nexdata;
```

## Production Setup

For production, create a read-only role:

```sql
-- As database superuser
CREATE ROLE explorer_readonly WITH LOGIN PASSWORD 'SECURE_PASSWORD_HERE';
GRANT CONNECT ON DATABASE your_database TO explorer_readonly;
GRANT USAGE ON SCHEMA public TO explorer_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO explorer_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO explorer_readonly;
```

Then use:
```bash
EXPLORER_DB_USER=explorer_readonly
EXPLORER_DB_PASSWORD=SECURE_PASSWORD_HERE
```

## Troubleshooting

### "Database Connection Failed"

1. **Check PostgreSQL is running:**
   ```bash
   pg_isready -h localhost -p 5433
   ```

2. **Test connection manually:**
   ```bash
   psql -h localhost -p 5433 -U nexdata -d nexdata
   ```

3. **Verify environment variables are set:**
   ```bash
   # Linux/Mac
   echo $EXPLORER_DB_HOST
   
   # Windows PowerShell
   echo $env:EXPLORER_DB_HOST
   ```

### "Permission denied"

Grant SELECT permissions:
```sql
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nexdata;
```

### Variables not loading

Make sure you're using the correct method:
- If using `.env` file, ensure it's in the `backend/` directory
- If using shell exports, run them in the same terminal before starting uvicorn
- If using Docker, ensure environment variables are in the correct service

## Complete Startup Command

One-liner for local development (Linux/Mac):

```bash
cd backend && \
EXPLORER_DB_HOST=localhost \
EXPLORER_DB_PORT=5433 \
EXPLORER_DB_USER=nexdata \
EXPLORER_DB_PASSWORD=nexdata_dev_password \
EXPLORER_DB_NAME=nexdata \
uvicorn main:app --reload --port 8000
```

Windows PowerShell:

```powershell
cd backend
$env:EXPLORER_DB_HOST="localhost"; $env:EXPLORER_DB_PORT="5433"; $env:EXPLORER_DB_USER="nexdata"; $env:EXPLORER_DB_PASSWORD="nexdata_dev_password"; $env:EXPLORER_DB_NAME="nexdata"
uvicorn main:app --reload --port 8000
```

## Configuration Defaults

If not set, the following defaults are used:

| Variable | Default Value |
|----------|--------------|
| EXPLORER_DB_HOST | `localhost` |
| EXPLORER_DB_PORT | `5433` |
| EXPLORER_DB_USER | `nexdata` |
| EXPLORER_DB_PASSWORD | `nexdata_dev_password` |
| EXPLORER_DB_NAME | `nexdata` |

**Note:** For security, all values should be explicitly set in production.

## Next Steps

After configuration:

1. Start backend: `uvicorn main:app --reload`
2. Start frontend: `npm run dev` (in frontend directory)
3. Navigate to: http://localhost:5173/data-explorer

For more details, see:
- [DATA_EXPLORER_QUICKSTART.md](DATA_EXPLORER_QUICKSTART.md)
- [backend/DATA_EXPLORER.md](backend/DATA_EXPLORER.md)

