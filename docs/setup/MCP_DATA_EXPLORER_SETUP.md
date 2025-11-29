# MCP Data Explorer Quick Setup Guide

This guide will get you up and running with the MCP Data Explorer in minutes.

## What You'll Get

After completing this setup, you'll be able to:
- ✅ Ask Claude (or other LLMs) to explore your Postgres databases conversationally
- ✅ Discover schemas, tables, and columns through natural language
- ✅ Profile data and get statistical insights automatically
- ✅ Run read-only queries safely with AI assistance

## Prerequisites

- Python 3.11+ installed
- Postgres database accessible (the dev database at port 5433 is already configured)
- Claude Desktop (for native MCP support) OR any other LLM for HTTP bridge

## Step 1: Install Dependencies (2 minutes)

```bash
cd backend
pip install -r requirements.txt
```

This installs the MCP SDK and all dependencies.

## Step 2: Verify Database Configuration (1 minute)

The database is already configured in your Docker setup. Verify it's running:

```bash
# Start the backend (if not already running)
docker-compose -f docker-compose.dev.yml up -d

# Check database connection
curl http://localhost:8000/api/v1/data-explorer/health
```

Expected response:
```json
{
  "connected": true,
  "database": "nexdata",
  "version": "PostgreSQL ...",
  "host": "localhost",
  "port": 5433
}
```

## Step 3: Test MCP Server (1 minute)

```bash
cd backend
python mcp_server.py
```

You should see:
```
INFO - Starting Postgres Data Explorer MCP Server
INFO - Found 1 database configuration(s):
INFO -   - default: nexdata @ localhost:5433
INFO - MCP Server ready - waiting for client connections
```

Press `Ctrl+C` to stop.

## Step 4: Choose Your Integration Path

### Option A: Claude Desktop (Native MCP) ⭐ Recommended

**1. Configure Claude Desktop**

Edit the Claude Desktop config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "postgres-explorer": {
      "command": "python",
      "args": [
        "C:/Users/awron/projects/Nex/backend/mcp_server.py"
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

**Note:** Adjust the path if your repo is in a different location.

**2. Restart Claude Desktop**

Completely quit and restart Claude Desktop.

**3. Verify Connection**

In Claude Desktop, start a new conversation and type:

```
"What tables are in my database?"
```

Claude should automatically use the MCP tools to explore your database!

### Option B: HTTP Bridge (For xAI, Gemini, ChatGPT, etc.)

**1. Start the FastAPI Backend**

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or use Docker:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**2. Test HTTP Endpoints**

```bash
# List databases
curl -X POST http://localhost:8000/api/v1/data-explorer/tool/list_connections \
  -H "Content-Type: application/json" \
  -d '{}'

# List tables
curl -X POST http://localhost:8000/api/v1/data-explorer/tool/list_tables \
  -H "Content-Type: application/json" \
  -d '{"connection_id": "default", "schema": "public"}'

# Profile a table
curl -X POST http://localhost:8000/api/v1/data-explorer/tool/profile_table \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "default",
    "schema": "public",
    "table": "users",
    "max_distinct": 50
  }'
```

**3. Integrate with Your LLM**

See the [full documentation](docs/mcp-data-explorer.md) for integration examples with:
- xAI (Grok)
- Google Gemini
- OpenAI (ChatGPT)

## Example Use Cases

Once connected, you can ask your LLM:

### Schema Discovery
```
"What schemas and tables exist in my database?"
"Show me the structure of the orders table"
"What columns does the users table have?"
```

### Data Profiling
```
"Profile the orders table and tell me about data quality"
"What are the most common values in the status column?"
"Show me statistics for all numeric columns in the sales table"
```

### Data Exploration
```
"Sample 10 rows from the users table"
"How many orders were placed last month?"
"What's the average order value by customer segment?"
```

### Insights & Analysis
```
"What patterns do you see in the customer data?"
"Are there any data quality issues in the orders table?"
"Compare the distribution of values across different product categories"
```

## Available Tools

The MCP server exposes 7 tools:

1. **list_connections** - List available database connections
2. **list_schemas** - List schemas in a database
3. **list_tables** - List tables and views in a schema
4. **get_table_info** - Get column metadata for a table
5. **sample_rows** - Sample rows from a table (up to 500 rows)
6. **profile_table** - Get comprehensive column statistics
7. **run_query** - Execute read-only SELECT queries safely

## Safety Features

- ✅ **Read-Only Sessions** - All database connections are read-only
- ✅ **Query Validation** - Only SELECT queries allowed, mutations blocked
- ✅ **Resource Limits** - 30-second timeout, 1000 row max per query
- ✅ **Error Handling** - Graceful error responses, no sensitive data exposed

## Troubleshooting

### MCP Server Connection Issues

**Problem:** Claude Desktop doesn't show the MCP server

**Solutions:**
1. Verify the config file path is correct
2. Check that Python path points to your Python installation
3. Completely restart Claude Desktop
4. Check Claude Desktop logs for errors

### Database Connection Issues

**Problem:** "Database Connection Failed"

**Solutions:**
1. Verify Postgres is running: `docker ps | grep postgres`
2. Check environment variables are set correctly
3. Test connection: `psql -h localhost -p 5433 -U nexdata -d nexdata`
4. Verify firewall/network settings

### HTTP Bridge Issues

**Problem:** HTTP endpoints return 500 errors

**Solutions:**
1. Check backend logs: `docker logs nex-backend-dev`
2. Verify database is accessible from backend container
3. Restart backend: `docker-compose -f docker-compose.dev.yml restart backend`

## Next Steps

- 📖 Read the [full documentation](docs/mcp-data-explorer.md) for advanced features
- 🔒 Set up [read-only database roles](docs/mcp-data-explorer.md#read-only-database-role-recommended) for production
- 🗄️ Add [multiple database connections](docs/mcp-data-explorer.md#database-connection-patterns)
- 🧪 Explore the [example queries](docs/mcp-data-explorer.md#example-use-cases)

## Support

- Check the [full documentation](docs/mcp-data-explorer.md)
- Review [Data Explorer docs](backend/DATA_EXPLORER.md)
- See [MCP Protocol docs](https://modelcontextprotocol.io/)

---

**🎉 You're all set! Start exploring your data with AI.**

