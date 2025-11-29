# Data Explorer

The Data Explorer feature provides a secure, read-only interface for browsing and querying your Postgres databases directly from the NEX.AI platform.

## Overview

Data Explorer allows you to:
- **Browse database schemas and tables** - Explore your database structure interactively
- **Inspect table metadata** - View column information including types, nullable status, and defaults
- **Preview table data** - Paginate through table rows with an intuitive UI
- **Execute ad-hoc queries** - Run custom SELECT queries with built-in safety validation
- **View summary statistics** - Get automatic statistics for numeric and categorical columns

## Security & Safety

The Data Explorer is designed with security as a top priority:

### Read-Only Access
- All database sessions are set to `READ ONLY` mode
- Only `SELECT` queries are allowed (enforced server-side)
- Queries containing mutating keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.) are rejected

### Query Limits
- Maximum row limit per query: **1,000 rows**
- Default page size: **50-100 rows**
- Query timeout: **30 seconds** (configurable via statement_timeout)
- Multiple statements are not allowed (no semicolon-separated queries)

### Error Handling
- All database errors are caught and returned as structured error objects
- No sensitive stack traces are exposed to the client
- Connection failures are handled gracefully

## Configuration

### Environment Variables

Data Explorer uses separate environment variables from the main application database:

```bash
# Data Explorer Database Configuration
EXPLORER_DB_HOST=localhost          # Database host (default: localhost)
EXPLORER_DB_PORT=5433              # Database port (default: 5433)
EXPLORER_DB_USER=nexdata           # Database user (default: nexdata)
EXPLORER_DB_PASSWORD=nexdata_dev_password  # Database password (required)
EXPLORER_DB_NAME=nexdata           # Database name (default: nexdata)
```

### Production Setup

For production deployments, we recommend:

1. **Use a read-only database role:**
   ```sql
   CREATE ROLE explorer_readonly WITH LOGIN PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE your_database TO explorer_readonly;
   GRANT USAGE ON SCHEMA public TO explorer_readonly;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO explorer_readonly;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO explorer_readonly;
   ```

2. **Set environment variables securely:**
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)
   - Never commit credentials to source control
   - Rotate passwords regularly

3. **Network security:**
   - Restrict database access to application servers only
   - Use SSL/TLS for database connections
   - Consider using a database proxy for additional security

## API Endpoints

All Data Explorer endpoints are under the `/api/v1/data-explorer` prefix.

### Health Check
```http
GET /api/v1/data-explorer/health
```

Returns connection status and database information.

**Response:**
```json
{
  "connected": true,
  "database": "nexdata",
  "version": "PostgreSQL 15.3...",
  "host": "localhost",
  "port": 5433
}
```

### List Schemas
```http
GET /api/v1/data-explorer/schemas
```

Returns all schemas (excluding system schemas).

**Response:**
```json
[
  {
    "name": "public",
    "table_count": 15
  },
  {
    "name": "analytics",
    "table_count": 8
  }
]
```

### List Tables
```http
GET /api/v1/data-explorer/tables?schema=public
```

Returns tables and views in a schema.

**Response:**
```json
[
  {
    "schema": "public",
    "name": "users",
    "type": "table",
    "row_estimate": 1523
  },
  {
    "schema": "public",
    "name": "orders",
    "type": "table",
    "row_estimate": 45321
  }
]
```

### Get Table Columns
```http
GET /api/v1/data-explorer/tables/{schema}/{table}/columns
```

Returns column metadata for a table.

**Response:**
```json
[
  {
    "name": "id",
    "data_type": "integer",
    "is_nullable": false,
    "default": "nextval('users_id_seq'::regclass)",
    "ordinal_position": 1
  },
  {
    "name": "email",
    "data_type": "character varying",
    "is_nullable": false,
    "default": null,
    "ordinal_position": 2
  }
]
```

### Get Table Rows
```http
GET /api/v1/data-explorer/tables/{schema}/{table}/rows?page=1&page_size=50
```

Returns paginated table data.

**Response:**
```json
{
  "schema": "public",
  "table": "users",
  "columns": ["id", "email", "created_at"],
  "rows": [
    [1, "user@example.com", "2024-01-15T10:30:00"],
    [2, "admin@example.com", "2024-01-16T11:45:00"]
  ],
  "page": 1,
  "page_size": 50,
  "total_rows": 1523
}
```

### Get Table Summary
```http
GET /api/v1/data-explorer/tables/{schema}/{table}/summary
```

Returns summary statistics for all columns.

**Response:**
```json
{
  "schema": "public",
  "table": "orders",
  "column_stats": {
    "id": {
      "data_type": "integer",
      "distinct_count": 45321,
      "min": 1,
      "max": 45321,
      "avg": 22661.0,
      "count": 45321
    },
    "status": {
      "data_type": "character varying",
      "distinct_count": 5
    }
  }
}
```

### Execute Query
```http
POST /api/v1/data-explorer/query
Content-Type: application/json

{
  "sql": "SELECT * FROM public.users WHERE created_at > '2024-01-01' LIMIT 100",
  "page": 1,
  "page_size": 100
}
```

Execute a custom SQL query (SELECT only).

**Response (Success):**
```json
{
  "columns": ["id", "email", "created_at"],
  "rows": [
    [1, "user@example.com", "2024-01-15T10:30:00"]
  ],
  "total_rows_estimate": 156,
  "execution_time_ms": 12.34,
  "error": null
}
```

**Response (Error):**
```json
{
  "columns": [],
  "rows": [],
  "total_rows_estimate": null,
  "execution_time_ms": 0,
  "error": {
    "message": "Query contains forbidden keyword: DELETE",
    "code": "UNSAFE_QUERY"
  }
}
```

## Usage Examples

### Using curl

**Check connection:**
```bash
curl http://localhost:8000/api/v1/data-explorer/health
```

**List schemas:**
```bash
curl http://localhost:8000/api/v1/data-explorer/schemas
```

**List tables in public schema:**
```bash
curl http://localhost:8000/api/v1/data-explorer/tables?schema=public
```

**Get table columns:**
```bash
curl http://localhost:8000/api/v1/data-explorer/tables/public/users/columns
```

**Get table rows (page 1):**
```bash
curl "http://localhost:8000/api/v1/data-explorer/tables/public/users/rows?page=1&page_size=50"
```

**Execute a query:**
```bash
curl -X POST http://localhost:8000/api/v1/data-explorer/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) FROM public.users",
    "page": 1,
    "page_size": 100
  }'
```

### Using the Web UI

1. **Start the application:**
   ```bash
   # Backend
   cd backend
   uvicorn main:app --reload --port 8000
   
   # Frontend (in another terminal)
   cd frontend
   npm run dev
   ```

2. **Navigate to Data Explorer:**
   - Open http://localhost:5173 in your browser
   - Click "Data Explorer" in the left sidebar

3. **Explore your data:**
   - Browse schemas in the left sidebar
   - Click on a table to view its data
   - Use the tabs to switch between Preview, Columns, Query, and Summary views
   - Write and execute custom SQL queries in the Query tab

## Development

### Running Locally

1. **Set up environment variables:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and add your database credentials
   ```

2. **Install dependencies:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

3. **Start the services:**
   ```bash
   # Backend (terminal 1)
   cd backend
   uvicorn main:app --reload --port 8000
   
   # Frontend (terminal 2)
   cd frontend
   npm run dev
   ```

4. **Access the application:**
   - Backend API: http://localhost:8000
   - Frontend UI: http://localhost:5173
   - API Docs: http://localhost:8000/docs

### Testing the Backend

```bash
# Test connection
curl http://localhost:8000/api/v1/data-explorer/health

# List schemas
curl http://localhost:8000/api/v1/data-explorer/schemas

# Test query validation (should fail)
curl -X POST http://localhost:8000/api/v1/data-explorer/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "DELETE FROM users", "page": 1, "page_size": 100}'
```

## Architecture

### Backend Structure

```
backend/
└── domains/
    └── data_explorer/
        ├── __init__.py          # Package initialization
        ├── models.py            # Pydantic models for requests/responses
        ├── connection.py        # Database connection management
        ├── service.py           # Business logic and query validation
        └── router.py            # FastAPI route handlers
```

### Key Components

1. **connection.py** - Manages database connections with context managers
   - Loads config from environment variables
   - Sets sessions to READ ONLY mode
   - Provides connection pooling-ready structure

2. **service.py** - Implements core functionality
   - `QueryValidator` - Validates SQL queries for safety
   - `DataExplorerService` - Contains all business logic
   - Schema/table introspection using information_schema
   - Safe query execution with error handling

3. **router.py** - FastAPI endpoints
   - RESTful API design
   - Proper HTTP status codes
   - Comprehensive error handling

4. **models.py** - Data models
   - Request/response schemas using Pydantic
   - Input validation
   - Type safety

### Frontend Structure

```
frontend/
└── src/
    ├── api/
    │   └── client.ts          # API client functions
    └── pages/
        └── DataExplorer.tsx   # Main Data Explorer component
```

## Troubleshooting

### Connection Issues

**Problem:** "Database Connection Failed"

**Solutions:**
1. Verify environment variables are set correctly
2. Check that PostgreSQL is running and accessible
3. Verify network connectivity (firewall, security groups)
4. Test connection manually:
   ```bash
   psql -h localhost -p 5433 -U nexdata -d nexdata
   ```

### Permission Issues

**Problem:** "Permission denied for table X"

**Solutions:**
1. Ensure the database user has SELECT permissions:
   ```sql
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO nexdata;
   ```
2. For new tables, set default privileges:
   ```sql
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO nexdata;
   ```

### Query Errors

**Problem:** "Query contains forbidden keyword: X"

**Solution:** The Data Explorer only allows SELECT queries. Remove any INSERT, UPDATE, DELETE, or DDL statements.

**Problem:** "Query timeout"

**Solution:** Optimize your query or reduce the result set size. Complex queries may exceed the 30-second timeout.

## Future Enhancements

Potential improvements for future versions:

- [ ] Export query results to CSV/JSON
- [ ] Query history and favorites
- [ ] Visual query builder
- [ ] Data visualization (charts/graphs)
- [ ] Support for database functions and views
- [ ] Query performance analysis
- [ ] Schema comparison tools
- [ ] Multiple database connections
- [ ] Collaborative features (shared queries)

## Support

For issues, questions, or feature requests:
- Check the main README.md
- Review existing documentation
- Open an issue in the project repository

