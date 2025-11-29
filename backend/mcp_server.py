#!/usr/bin/env python3
"""
MCP Data Explorer Server for Postgres

This MCP (Model Context Protocol) server exposes Postgres database exploration 
capabilities as tools that any LLM can use conversationally.

Framework: FastAPI backend with psycopg for Postgres
DB Logic: Reuses existing domains/data_explorer/ infrastructure
MCP SDK: Official Anthropic MCP SDK for Python

Tools provided:
- list_connections: List available database connections
- list_schemas: List schemas in a database
- list_tables: List tables/views in a schema
- get_table_info: Get column metadata for a table
- sample_rows: Sample rows from a table with pagination
- profile_table: Get comprehensive column profiles and statistics
- run_query: Execute read-only SELECT queries with safety validation

Safety features:
- Read-only database sessions
- Query validation (SELECT only, no mutating operations)
- Query timeouts and row limits
- Structured error handling
"""

import asyncio
import json
import os
import sys
import logging
from typing import Any, Dict, List

# Add parent directory to path to import from domains
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from domains.data_explorer.db_configs import get_database_configs, get_database_config_by_id
from domains.data_explorer.service import DataExplorerService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_postgres_server")

# Initialize MCP server
app = Server("postgres-data-explorer")


def serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format."""
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    else:
        return obj


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="list_connections",
            description=(
                "List all available database connections configured in the system. "
                "Each connection has an ID, name, host, and database. "
                "Use this first to discover which databases you can explore."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_schemas",
            description=(
                "List all schemas in a database (excluding system schemas). "
                "Returns schema names with table counts. "
                "Use this after selecting a connection to see available schemas."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_tables",
            description=(
                "List all tables and views in a schema. "
                "Returns table names, types (table/view), and row estimates. "
                "Use this to discover tables before inspecting their structure."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name (default: 'public')",
                        "default": "public"
                    }
                },
                "required": ["schema"]
            }
        ),
        Tool(
            name="get_table_info",
            description=(
                "Get detailed column metadata for a specific table. "
                "Returns column names, data types, nullable status, defaults, and positions. "
                "Use this before querying or sampling to understand table structure."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name"
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    }
                },
                "required": ["schema", "table"]
            }
        ),
        Tool(
            name="sample_rows",
            description=(
                "Sample rows from a table with pagination support. "
                "Returns column names, data rows, and pagination info. "
                "Default limit is 50 rows, maximum is 500. "
                "Use this to preview actual data before running complex queries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name"
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of rows to return (default: 50, max: 500)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of rows to skip (default: 0)",
                        "default": 0,
                        "minimum": 0
                    }
                },
                "required": ["schema", "table"]
            }
        ),
        Tool(
            name="profile_table",
            description=(
                "Generate comprehensive statistical profile for a table. "
                "Returns per-column statistics including: "
                "- Data type and nullable status "
                "- Null counts and null fraction "
                "- Approximate distinct value counts "
                "- For numeric columns: min, max, average "
                "- For categorical columns: top K values with counts (capped by max_distinct). "
                "Use this to understand data distribution and quality before analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name"
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    },
                    "max_distinct": {
                        "type": "integer",
                        "description": "Maximum distinct values to return for categorical columns (default: 50)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200
                    }
                },
                "required": ["schema", "table"]
            }
        ),
        Tool(
            name="run_query",
            description=(
                "Execute a custom SQL query (SELECT only, read-only). "
                "Enforces safety: only SELECT/WITH queries allowed, no mutations. "
                "Returns columns, rows, execution time, and row count. "
                "Query timeout is 30 seconds. Maximum page size is 1000 rows. "
                "Use this for custom analysis after exploring table structures."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    },
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only)"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1,
                        "minimum": 1
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Rows per page (default: 100, max: 1000)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["sql"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool execution."""
    
    try:
        logger.info(f"Executing tool: {name} with arguments: {arguments}")
        
        if name == "list_connections":
            result = handle_list_connections()
            
        elif name == "list_schemas":
            connection_id = arguments.get("connection_id", "default")
            result = handle_list_schemas(connection_id)
            
        elif name == "list_tables":
            connection_id = arguments.get("connection_id", "default")
            schema = arguments.get("schema", "public")
            result = handle_list_tables(connection_id, schema)
            
        elif name == "get_table_info":
            connection_id = arguments.get("connection_id", "default")
            schema = arguments["schema"]
            table = arguments["table"]
            result = handle_get_table_info(connection_id, schema, table)
            
        elif name == "sample_rows":
            connection_id = arguments.get("connection_id", "default")
            schema = arguments["schema"]
            table = arguments["table"]
            limit = arguments.get("limit", 50)
            offset = arguments.get("offset", 0)
            result = handle_sample_rows(connection_id, schema, table, limit, offset)
            
        elif name == "profile_table":
            connection_id = arguments.get("connection_id", "default")
            schema = arguments["schema"]
            table = arguments["table"]
            max_distinct = arguments.get("max_distinct", 50)
            result = handle_profile_table(connection_id, schema, table, max_distinct)
            
        elif name == "run_query":
            connection_id = arguments.get("connection_id", "default")
            sql = arguments["sql"]
            page = arguments.get("page", 1)
            page_size = arguments.get("page_size", 100)
            result = handle_run_query(connection_id, sql, page, page_size)
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, default=str)
        
        return [TextContent(
            type="text",
            text=result_json
        )]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_result = {
            "error": {
                "message": str(e),
                "code": type(e).__name__
            }
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


def handle_list_connections() -> List[Dict[str, Any]]:
    """Handle list_connections tool."""
    configs = get_database_configs()
    return [
        {
            "id": config.id,
            "label": f"{config.name} ({config.description})",
            "host": config.host,
            "port": config.port,
            "database": config.database
        }
        for config in configs
    ]


def handle_list_schemas(connection_id: str) -> List[Dict[str, Any]]:
    """Handle list_schemas tool."""
    schemas = DataExplorerService.get_schemas(db_id=connection_id)
    return [serialize_for_json(schema) for schema in schemas]


def handle_list_tables(connection_id: str, schema: str) -> List[Dict[str, Any]]:
    """Handle list_tables tool."""
    tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
    return [serialize_for_json(table) for table in tables]


def handle_get_table_info(connection_id: str, schema: str, table: str) -> Dict[str, Any]:
    """Handle get_table_info tool."""
    columns = DataExplorerService.get_columns(schema=schema, table=table, db_id=connection_id)
    return {
        "schema": schema,
        "table": table,
        "columns": [serialize_for_json(col) for col in columns]
    }


def handle_sample_rows(
    connection_id: str,
    schema: str,
    table: str,
    limit: int,
    offset: int
) -> Dict[str, Any]:
    """Handle sample_rows tool."""
    # Convert limit/offset to page/page_size for the service
    page = (offset // limit) + 1
    page_size = min(limit, 500)
    
    result = DataExplorerService.get_table_rows(
        schema=schema,
        table=table,
        page=page,
        page_size=page_size,
        db_id=connection_id
    )
    return serialize_for_json(result)


def handle_profile_table(
    connection_id: str,
    schema: str,
    table: str,
    max_distinct: int
) -> Dict[str, Any]:
    """Handle profile_table tool."""
    result = DataExplorerService.profile_table(
        schema=schema,
        table=table,
        max_distinct=max_distinct,
        db_id=connection_id
    )
    return result


def handle_run_query(
    connection_id: str,
    sql: str,
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """Handle run_query tool."""
    result = DataExplorerService.execute_query(
        sql=sql,
        page=page,
        page_size=page_size,
        db_id=connection_id
    )
    
    response = serialize_for_json(result)
    
    # Add optional summary if no error
    if not response.get('error'):
        row_count = len(response.get('rows', []))
        total_rows = response.get('total_rows_estimate', row_count)
        response['summary'] = (
            f"Query returned {row_count} row(s) (total: {total_rows}) "
            f"in {response.get('execution_time_ms', 0):.2f}ms"
        )
    
    return response


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Postgres Data Explorer MCP Server")
    
    # Verify database configuration exists
    try:
        configs = get_database_configs()
        if not configs:
            logger.error("No database configurations found! Check environment variables.")
            logger.error("Required: EXPLORER_DB_HOST, EXPLORER_DB_PORT, EXPLORER_DB_USER, EXPLORER_DB_PASSWORD, EXPLORER_DB_NAME")
            sys.exit(1)
        
        logger.info(f"Found {len(configs)} database configuration(s):")
        for config in configs:
            logger.info(f"  - {config.id}: {config.database} @ {config.host}:{config.port}")
    except Exception as e:
        logger.error(f"Error loading database configurations: {e}")
        sys.exit(1)
    
    # Start the stdio server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server ready - waiting for client connections")
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

