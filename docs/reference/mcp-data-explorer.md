# MCP Data Explorer for Postgres

A Model Context Protocol (MCP) server that exposes Postgres database exploration capabilities as tools for conversational AI. Compatible with Claude Desktop (native MCP) and other LLMs via HTTP bridge (xAI, Gemini, ChatGPT).

## 🎯 Overview

The MCP Data Explorer allows any LLM to:

- **Discover** database schemas, tables, and columns
- **Inspect** table structures and metadata
- **Profile** data with comprehensive statistics
- **Query** databases safely with read-only SELECT queries
- **Build context** across conversations for insights

### Key Features

- ✅ **Native MCP Support** - Direct integration with Claude Desktop
- ✅ **HTTP Bridge** - REST API for non-MCP LLMs (xAI, Gemini, ChatGPT)
- ✅ **Multi-Database** - Support for multiple Postgres connections
- ✅ **Read-Only Safety** - Enforced read-only sessions with query validation
- ✅ **Comprehensive Profiling** - Statistical analysis and data quality insights
- ✅ **Reusable Logic** - Built on existing Data Explorer backend

## 📋 Prerequisites

- Python 3.11+
- Postgres database(s) to explore
- FastAPI backend (already part of this repo)
- MCP SDK (automatically installed)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs the MCP SDK and all required dependencies.

### 2. Configure Environment Variables

Create or update your `.env` file with database credentials:

```bash
# Primary database (default)
EXPLORER_DB_HOST=localhost
EXPLORER_DB_PORT=5433
EXPLORER_DB_USER=nexdata
EXPLORER_DB_PASSWORD=nexdata_dev_password
EXPLORER_DB_NAME=nexdata

# Additional databases (optional)
EXPLORER2_DB_HOST=localhost
EXPLORER2_DB_PORT=5434
EXPLORER2_DB_USER=analytics
EXPLORER2_DB_PASSWORD=analytics_password
EXPLORER2_DB_NAME=analytics_db

# Or use alternate naming scheme
EXPLORER_DB_2_HOST=localhost
EXPLORER_DB_2_PORT=5435
EXPLORER_DB_2_USER=warehouse
EXPLORER_DB_2_PASSWORD=warehouse_password
EXPLORER_DB_2_NAME=warehouse_db
```

**Security Best Practices:**
- Use read-only database roles in production
- Store passwords in secrets management (AWS Secrets Manager, Vault, etc.)
- Never commit credentials to source control
- Rotate passwords regularly

### 3. Test Database Connection

```bash
cd backend
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

### 4. Start the MCP Server

```bash
cd backend
python mcp_server.py
```

The server will:
- Load database configurations from environment variables
- Start listening on stdio for MCP client connections
- Log available databases and ready status

## 🔧 Configuration

### Database Connection Patterns

The system auto-detects database configurations from environment variables:

| Pattern | Example | Connection ID |
|---------|---------|---------------|
| `EXPLORER_DB_*` | `EXPLORER_DB_HOST=localhost` | `default` |
| `EXPLORER2_DB_*` | `EXPLORER2_DB_HOST=localhost` | `db2` |
| `EXPLORER3_DB_*` | `EXPLORER3_DB_HOST=localhost` | `db3` |
| `EXPLORER_DB_2_*` | `EXPLORER_DB_2_HOST=localhost` | `db2` |

### Read-Only Database Role (Recommended)

Create a read-only role in Postgres:

```sql
-- Create read-only role
CREATE ROLE explorer_readonly WITH LOGIN PASSWORD 'secure_password';

-- Grant connect to database
GRANT CONNECT ON DATABASE your_database TO explorer_readonly;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA public TO explorer_readonly;

-- Grant select on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO explorer_readonly;

-- Grant select on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT SELECT ON TABLES TO explorer_readonly;
```

Then use this role in your environment variables:
```bash
EXPLORER_DB_USER=explorer_readonly
EXPLORER_DB_PASSWORD=secure_password
```

## 🧰 MCP Tools

The server exposes 7 tools for database exploration:

### 1. `list_connections`

List all available database connections.

**Input:** None

**Output:**
```json
[
  {
    "id": "default",
    "label": "nexdata (localhost:5433)",
    "host": "localhost",
    "port": 5433,
    "database": "nexdata"
  }
]
```

### 2. `list_schemas`

List schemas in a database.

**Input:**
```json
{
  "connection_id": "default"  // optional, defaults to "default"
}
```

**Output:**
```json
[
  {"name": "public", "table_count": 15},
  {"name": "analytics", "table_count": 8}
]
```

### 3. `list_tables`

List tables and views in a schema.

**Input:**
```json
{
  "connection_id": "default",  // optional
  "schema": "public"
}
```

**Output:**
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

### 4. `get_table_info`

Get column metadata for a table.

**Input:**
```json
{
  "connection_id": "default",  // optional
  "schema": "public",
  "table": "users"
}
```

**Output:**
```json
{
  "schema": "public",
  "table": "users",
  "columns": [
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
}
```

### 5. `sample_rows`

Sample rows from a table with pagination.

**Input:**
```json
{
  "connection_id": "default",  // optional
  "schema": "public",
  "table": "users",
  "limit": 50,    // optional, default 50, max 500
  "offset": 0     // optional, default 0
}
```

**Output:**
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

### 6. `profile_table`

Generate comprehensive statistical profile for a table.

**Input:**
```json
{
  "connection_id": "default",  // optional
  "schema": "public",
  "table": "orders",
  "max_distinct": 50  // optional, max categorical values to return
}
```

**Output:**
```json
{
  "schema": "public",
  "table": "orders",
  "total_rows": 45321,
  "column_profiles": {
    "id": {
      "data_type": "integer",
      "nullable": false,
      "null_count": 0,
      "null_fraction": 0.0,
      "approx_distinct_count": 45321,
      "min": 1,
      "max": 45321,
      "avg": 22661.0
    },
    "status": {
      "data_type": "character varying",
      "nullable": false,
      "null_count": 0,
      "null_fraction": 0.0,
      "approx_distinct_count": 5,
      "top_values": [
        {"value": "completed", "count": 30000},
        {"value": "pending", "count": 10000},
        {"value": "cancelled", "count": 5321}
      ]
    }
  }
}
```

### 7. `run_query`

Execute a read-only SQL query.

**Input:**
```json
{
  "connection_id": "default",  // optional
  "sql": "SELECT status, COUNT(*) FROM public.orders GROUP BY status",
  "page": 1,       // optional, default 1
  "page_size": 100 // optional, default 100, max 1000
}
```

**Output (Success):**
```json
{
  "columns": ["status", "count"],
  "rows": [
    ["completed", 30000],
    ["pending", 10000],
    ["cancelled", 5321]
  ],
  "total_rows_estimate": 3,
  "execution_time_ms": 12.34,
  "summary": "Query returned 3 row(s) (total: 3) in 12.34ms",
  "error": null
}
```

**Output (Error):**
```json
{
  "columns": [],
  "rows": [],
  "total_rows_estimate": null,
  "execution_time_ms": 0,
  "summary": null,
  "error": {
    "message": "Query contains forbidden keyword: DELETE",
    "code": "UNSAFE_QUERY"
  }
}
```

## 🔌 Using with Claude Desktop

### Configure MCP Server in Claude Desktop

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "postgres-explorer": {
      "command": "python",
      "args": [
        "C:/Users/YourName/projects/Nex/backend/mcp_server.py"
      ],
      "env": {
        "EXPLORER_DB_HOST": "localhost",
        "EXPLORER_DB_PORT": "5433",
        "EXPLORER_DB_USER": "nexdata",
        "EXPLORER_DB_PASSWORD": "nexdata_dev_password",
        "EXPLORER_DB_NAME": "nexdata"
      }
    }
  }
}
```

**Note:** Adjust the path to match your installation directory.

### Example Conversation with Claude

```
You: "What tables are in the public schema of my database?"

Claude: [Calls list_tables tool]
I found 15 tables in the public schema:
- users (1,523 rows)
- orders (45,321 rows)
- products (856 rows)
...

You: "Show me a sample of the users table and profile it"

Claude: [Calls sample_rows and profile_table tools]
Here's a sample of the users table showing 5 rows...

Based on the profile:
- The table has 1,523 users
- Email column has 100% unique values (1,523 distinct)
- 12% of users have null phone numbers
- Average user_id is 762
...

You: "How many orders were placed in the last month?"

Claude: [Calls run_query tool with appropriate SQL]
There were 3,456 orders placed in the last month.
```

## 🌐 Using with Non-MCP LLMs (xAI, Gemini, ChatGPT)

For LLMs that don't natively support MCP, use the HTTP bridge endpoints.

### Start the FastAPI Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### HTTP Bridge Endpoints

All endpoints are under `/api/v1/data-explorer/tool/`:

- `POST /api/v1/data-explorer/tool/list_connections`
- `POST /api/v1/data-explorer/tool/list_schemas`
- `POST /api/v1/data-explorer/tool/list_tables`
- `POST /api/v1/data-explorer/tool/get_table_info`
- `POST /api/v1/data-explorer/tool/sample_rows`
- `POST /api/v1/data-explorer/tool/profile_table`
- `POST /api/v1/data-explorer/tool/run_query`

### Response Format

All endpoints return:
```json
{
  "success": true,
  "data": { /* tool-specific result */ }
}
```

Or on error:
```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE"
  }
}
```

### Example: xAI (Grok) Integration

Define functions for xAI API:

```python
import requests
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_XAI_API_KEY",
    base_url="https://api.x.ai/v1"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all tables in a database schema",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "default": "public"}
                },
                "required": ["schema"]
            }
        }
    },
    # ... define other tools similarly
]

def call_tool(tool_name, arguments):
    """Execute a tool via HTTP bridge."""
    url = f"http://localhost:8000/api/v1/data-explorer/tool/{tool_name}"
    response = requests.post(url, json=arguments)
    return response.json()

# Use with xAI
response = client.chat.completions.create(
    model="grok-beta",
    messages=[
        {"role": "user", "content": "What tables are in my database?"}
    ],
    tools=tools
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        result = call_tool(tool_call.function.name, tool_call.function.arguments)
        print(result)
```

### Example: OpenAI (ChatGPT) Integration

Define actions in GPT:

```yaml
openapi: 3.0.0
info:
  title: Postgres Data Explorer API
  version: 1.0.0
servers:
  - url: http://localhost:8000/api/v1/data-explorer
paths:
  /tool/list_tables:
    post:
      operationId: listTables
      summary: List tables in a schema
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                connection_id:
                  type: string
                  default: default
                schema:
                  type: string
                  default: public
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: array
```

### Example: Google Gemini Integration

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Define function declarations
list_tables_func = {
    "name": "list_tables",
    "description": "List all tables in a database schema",
    "parameters": {
        "type": "object",
        "properties": {
            "connection_id": {"type": "string"},
            "schema": {"type": "string"}
        }
    }
}

model = genai.GenerativeModel('gemini-pro', tools=[list_tables_func])

response = model.generate_content(
    "What tables are in the public schema?",
    generation_config=genai.GenerationConfig(
        temperature=0.1
    )
)

# Handle function calls
for part in response.parts:
    if fn_call := part.function_call:
        result = call_tool(fn_call.name, dict(fn_call.args))
        print(result)
```

## 🔒 Security & Safety

### Query Safety Features

1. **Read-Only Sessions**
   - All database sessions are set to `READ ONLY` mode
   - Prevents accidental data modification

2. **Query Validation**
   - Server-side validation rejects non-SELECT queries
   - Forbidden keywords: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, etc.
   - Multiple statements (semicolon-separated) are blocked

3. **Resource Limits**
   - Query timeout: 30 seconds
   - Maximum rows per query: 1,000 (configurable)
   - Default page size: 50-100 rows

4. **Error Handling**
   - Structured error responses
   - No sensitive stack traces exposed
   - Connection failures handled gracefully

### Production Recommendations

1. **Use Read-Only Database Role** (see Configuration section)
2. **Network Security**
   - Restrict database access to application servers only
   - Use SSL/TLS for database connections
   - Consider database proxy for additional security
3. **Secrets Management**
   - Store credentials in AWS Secrets Manager, HashiCorp Vault, etc.
   - Never commit credentials to source control
   - Rotate passwords regularly
4. **Monitoring**
   - Log query patterns and execution times
   - Alert on failed authentication attempts
   - Monitor for suspicious query patterns

## 🧪 Testing

### Test MCP Server Locally

```bash
# Start the MCP server in test mode
cd backend
python mcp_server.py
```

In another terminal, test with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python backend/mcp_server.py
```

### Test HTTP Bridge

```bash
# Start FastAPI backend
cd backend
uvicorn main:app --port 8000

# Test list_connections
curl -X POST http://localhost:8000/api/v1/data-explorer/tool/list_connections \
  -H "Content-Type: application/json" \
  -d '{}'

# Test list_tables
curl -X POST http://localhost:8000/api/v1/data-explorer/tool/list_tables \
  -H "Content-Type: application/json" \
  -d '{"connection_id": "default", "schema": "public"}'

# Test run_query
curl -X POST http://localhost:8000/api/v1/data-explorer/tool/run_query \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "default",
    "sql": "SELECT COUNT(*) FROM public.users",
    "page": 1,
    "page_size": 100
  }'
```

## 📊 Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────┐
│                    LLM Clients                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Claude   │  │   xAI    │  │ Gemini / ChatGPT │  │
│  │ Desktop  │  │  (Grok)  │  │                  │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
└───────┼─────────────┼─────────────────┼────────────┘
        │             │                 │
        │ MCP         │ HTTP            │ HTTP
        │ stdio       │ REST            │ REST
        │             │                 │
┌───────▼─────────────▼─────────────────▼────────────┐
│              Backend Services                       │
│  ┌──────────────┐      ┌─────────────────────────┐ │
│  │  MCP Server  │      │  FastAPI Backend        │ │
│  │              │      │  (HTTP Bridge)          │ │
│  │mcp_server.py │      │  /tool/* endpoints      │ │
│  └──────┬───────┘      └────────┬────────────────┘ │
│         │                       │                   │
│         └───────────┬───────────┘                   │
│                     │                               │
│         ┌───────────▼────────────┐                  │
│         │  Data Explorer Service │                  │
│         │  - Query validation    │                  │
│         │  - Schema introspection│                  │
│         │  - Safe query execution│                  │
│         │  - Statistical profiling                  │
│         └───────────┬────────────┘                  │
└─────────────────────┼───────────────────────────────┘
                      │
                      │ psycopg
                      │ READ ONLY
                      │
┌─────────────────────▼───────────────────────────────┐
│              Postgres Databases                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │nexdata DB│  │analytics │  │ warehouse DB     │  │
│  │:5433     │  │DB :5434  │  │ :5435            │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### File Structure

```
Nex/
├── backend/
│   ├── mcp_server.py                  # MCP server (new)
│   ├── requirements.txt                # Updated with mcp SDK
│   ├── domains/
│   │   └── data_explorer/
│   │       ├── service.py             # Enhanced with profile_table
│   │       ├── router.py              # Enhanced with HTTP bridge tools
│   │       ├── connection.py          # DB connection management
│   │       ├── db_configs.py          # Multi-DB config support
│   │       └── models.py              # Pydantic models
│   └── main.py                        # FastAPI app
└── docs/
    └── mcp-data-explorer.md           # This file
```

### Key Design Decisions

1. **Reuse Existing Logic**
   - MCP server calls the same `DataExplorerService` as HTTP API
   - Centralized query validation and safety checks
   - No code duplication

2. **Multi-Database Support**
   - Auto-detects database configs from environment variables
   - Each tool accepts `connection_id` parameter
   - Easy to add new databases without code changes

3. **LLM-Agnostic Design**
   - MCP protocol for native support (Claude)
   - HTTP bridge for universal compatibility
   - Consistent tool schemas across both interfaces

4. **Safety First**
   - Read-only database sessions
   - Server-side query validation
   - Timeouts and row limits
   - Structured error handling

## 🐛 Troubleshooting

### MCP Server Won't Start

**Problem:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
cd backend
pip install -r requirements.txt --upgrade
```

**Problem:** `No database configurations found`

**Solution:** Check environment variables are set:
```bash
echo $EXPLORER_DB_HOST
echo $EXPLORER_DB_PORT
```

If empty, create/update `.env` file and source it.

### Claude Desktop Can't Connect

**Problem:** MCP server not appearing in Claude Desktop

**Solution:**
1. Check config file path is correct for your OS
2. Verify Python path in config points to correct Python
3. Ensure environment variables are set in the config
4. Restart Claude Desktop completely
5. Check Claude Desktop logs for errors

**Problem:** "Connection failed" in Claude Desktop

**Solution:**
1. Test MCP server standalone: `python backend/mcp_server.py`
2. Check database connection: `curl http://localhost:8000/api/v1/data-explorer/health`
3. Verify firewall allows database connection
4. Check database credentials are correct

### HTTP Bridge Returns Errors

**Problem:** `500 Internal Server Error`

**Solution:**
1. Check FastAPI logs: `docker logs nex-backend-dev`
2. Verify database is running and accessible
3. Test database connection directly with psql
4. Check environment variables in container

**Problem:** `"Query contains forbidden keyword: INSERT"`

**Solution:** This is expected behavior. The Data Explorer only allows SELECT queries. Remove any mutating operations from your SQL.

### Query Timeout

**Problem:** `Query execution timeout after 30 seconds`

**Solution:**
1. Optimize your query (add indexes, limit result set)
2. Use LIMIT clause to restrict rows
3. Break complex queries into smaller parts
4. Consider creating a view for complex aggregations

## 📚 Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Claude Desktop MCP Guide](https://modelcontextprotocol.io/quickstart/user)
- [Data Explorer Documentation](../backend/DATA_EXPLORER.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Postgres Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This is a prototype application for demonstration and research purposes.

---

**Ready to explore your data with AI?**

Start the MCP server and connect your favorite LLM!

