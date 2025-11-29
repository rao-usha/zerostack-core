# Data Explorer - Quick Start Guide

Get up and running with Data Explorer in 5 minutes.

## Prerequisites

- NEX.AI backend and frontend installed
- PostgreSQL database running and accessible
- Database credentials

## Step 1: Configure Environment Variables

Add the following environment variables to your backend configuration:

### Option A: Using .env file (Recommended for Development)

Create or edit `backend/.env`:

```bash
# Data Explorer Database Configuration
EXPLORER_DB_HOST=localhost
EXPLORER_DB_PORT=5433
EXPLORER_DB_USER=nexdata
EXPLORER_DB_PASSWORD=nexdata_dev_password
EXPLORER_DB_NAME=nexdata
```

### Option B: Using Shell Environment

```bash
export EXPLORER_DB_HOST=localhost
export EXPLORER_DB_PORT=5433
export EXPLORER_DB_USER=nexdata
export EXPLORER_DB_PASSWORD=nexdata_dev_password
export EXPLORER_DB_NAME=nexdata
```

### Option C: Using Docker Compose

Add to your `docker-compose.yml`:

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

## Step 2: Start the Application

### Terminal 1: Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

## Step 3: Verify Connection

Test the database connection:

```bash
curl http://localhost:8000/api/v1/data-explorer/health
```

Expected response:
```json
{
  "connected": true,
  "database": "nexdata",
  "version": "PostgreSQL 15.3...",
  "host": "localhost",
  "port": 5433
}
```

## Step 4: Access the UI

1. Open http://localhost:5173 in your browser
2. Click **"Data Explorer"** in the left navigation
3. You should see your schemas and tables in the left sidebar

## Step 5: Explore Your Data

### Browse Tables
1. Expand a schema in the left sidebar (e.g., "public")
2. Click on any table name
3. View the data in the Preview tab

### View Column Details
1. Select a table
2. Click the **"Columns"** tab
3. See column names, types, and constraints

### Run Custom Queries
1. Select a table
2. Click the **"Query"** tab
3. Edit the SQL query (or write your own)
4. Click **"Run Query"**

Example queries to try:
```sql
-- Count rows
SELECT COUNT(*) FROM public.users;

-- Get recent records
SELECT * FROM public.orders 
WHERE created_at > NOW() - INTERVAL '7 days'
LIMIT 50;

-- Aggregate data
SELECT status, COUNT(*) as count
FROM public.orders
GROUP BY status;
```

### View Summary Statistics
1. Select a table
2. Click the **"Summary"** tab
3. View automatic statistics for all columns

## Troubleshooting

### "Database Connection Failed"

**Check 1: Verify PostgreSQL is running**
```bash
psql -h localhost -p 5433 -U nexdata -d nexdata
```

**Check 2: Verify environment variables**
```bash
# Backend must have access to these variables
echo $EXPLORER_DB_HOST
echo $EXPLORER_DB_PORT
echo $EXPLORER_DB_USER
```

**Check 3: Check firewall/network**
- Ensure PostgreSQL accepts connections from your application
- Check `pg_hba.conf` for connection permissions

### "Permission denied for table"

**Solution: Grant SELECT permissions**
```sql
-- Connect as superuser
psql -U postgres -d nexdata

-- Grant read access
GRANT CONNECT ON DATABASE nexdata TO nexdata;
GRANT USAGE ON SCHEMA public TO nexdata;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nexdata;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO nexdata;
```

### "Query contains forbidden keyword"

Data Explorer only allows `SELECT` queries for safety. Remove any:
- `INSERT`, `UPDATE`, `DELETE`
- `DROP`, `CREATE`, `ALTER`
- `TRUNCATE`, `GRANT`, `REVOKE`

## Production Setup

For production deployments:

1. **Create a read-only database role:**
```sql
CREATE ROLE explorer_readonly WITH LOGIN PASSWORD 'secure_password_here';
GRANT CONNECT ON DATABASE your_database TO explorer_readonly;
GRANT USAGE ON SCHEMA public TO explorer_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO explorer_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO explorer_readonly;
```

2. **Use the read-only role:**
```bash
EXPLORER_DB_USER=explorer_readonly
EXPLORER_DB_PASSWORD=secure_password_here
```

3. **Enable SSL connections:**
```bash
EXPLORER_DB_SSLMODE=require
# Update connection.py to add sslmode parameter if needed
```

4. **Use secrets management:**
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets
- Environment variable injection

## Next Steps

- Read the [full Data Explorer documentation](backend/DATA_EXPLORER.md)
- Explore the API at http://localhost:8000/docs
- Try complex queries and aggregations
- Export query results (coming soon)

## Example Use Cases

### 1. Data Quality Checks
```sql
-- Find null values
SELECT 
    COUNT(*) as total_rows,
    COUNT(email) as non_null_emails,
    COUNT(*) - COUNT(email) as null_emails
FROM public.users;
```

### 2. Business Analytics
```sql
-- Revenue by month
SELECT 
    DATE_TRUNC('month', created_at) as month,
    SUM(amount) as total_revenue,
    COUNT(*) as order_count
FROM public.orders
WHERE created_at >= NOW() - INTERVAL '1 year'
GROUP BY month
ORDER BY month DESC;
```

### 3. User Behavior
```sql
-- Most active users
SELECT 
    user_id,
    COUNT(*) as action_count,
    MAX(created_at) as last_activity
FROM public.user_actions
GROUP BY user_id
ORDER BY action_count DESC
LIMIT 10;
```

## Support

For more help:
- Check the [full documentation](backend/DATA_EXPLORER.md)
- Review API docs at http://localhost:8000/docs
- Check the main README.md

