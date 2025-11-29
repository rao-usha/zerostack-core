"""
Data Explorer API router.

Provides endpoints for browsing database schemas, tables, and executing read-only queries.
All endpoints are prefixed with /api/v1/data-explorer.

Includes MCP-compatible HTTP bridge endpoints for non-MCP LLMs (xAI, Gemini, ChatGPT).
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .models import (
    SchemaInfo, TableInfo, ColumnInfo, TableRowsResponse,
    QueryRequest, QueryResponse, TableSummaryResponse
)
from .service import DataExplorerService
from .connection import test_connection
from .db_configs import get_database_configs


class DatabaseInfo(BaseModel):
    """Database configuration info (without password)."""
    id: str
    name: str
    description: str
    host: str
    port: int


router = APIRouter(prefix="/data-explorer", tags=["data-explorer"])


@router.get("/databases", response_model=List[DatabaseInfo])
async def list_databases():
    """
    Get list of available databases for exploration.
    
    Returns:
        List of database configurations (without passwords)
    """
    try:
        configs = get_database_configs()
        return [
            DatabaseInfo(
                id=config.id,
                name=config.name,
                description=config.description,
                host=config.host,
                port=config.port
            )
            for config in configs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list databases: {str(e)}")


@router.get("/health")
async def health_check(db_id: str = Query(default="default", description="Database ID")):
    """
    Check if the data explorer database connection is working.
    
    Args:
        db_id: Database configuration ID
    
    Returns:
        Connection status and database info
    """
    return test_connection(db_id)


@router.get("/schemas", response_model=List[SchemaInfo])
async def get_schemas(db_id: str = Query(default="default", description="Database ID")):
    """
    Get list of all schemas in the database.
    
    Args:
        db_id: Database configuration ID
    
    Returns:
        List of schemas with table counts
    """
    try:
        return DataExplorerService.get_schemas(db_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schemas: {str(e)}")


@router.get("/tables", response_model=List[TableInfo])
async def get_tables(
    schema: str = Query(default="public", description="Schema name"),
    db_id: str = Query(default="default", description="Database ID")
):
    """
    Get list of tables and views in a schema.
    
    Args:
        schema: Schema name (default: public)
        db_id: Database configuration ID
        
    Returns:
        List of tables and views with metadata
    """
    try:
        return DataExplorerService.get_tables(schema, db_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tables: {str(e)}")


@router.get("/tables/{schema}/{table}/columns", response_model=List[ColumnInfo])
async def get_table_columns(
    schema: str,
    table: str,
    db_id: str = Query(default="default", description="Database ID")
):
    """
    Get column information for a specific table.
    
    Args:
        schema: Schema name
        table: Table name
        db_id: Database configuration ID
        
    Returns:
        List of columns with metadata (name, type, nullable, etc.)
    """
    try:
        columns = DataExplorerService.get_columns(schema, table, db_id)
        if not columns:
            raise HTTPException(status_code=404, detail=f"Table {schema}.{table} not found")
        return columns
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch columns: {str(e)}")


@router.get("/tables/{schema}/{table}/rows", response_model=TableRowsResponse)
async def get_table_rows(
    schema: str,
    table: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=500, description="Rows per page"),
    db_id: str = Query(default="default", description="Database ID")
):
    """
    Get paginated rows from a table.
    
    Args:
        schema: Schema name
        table: Table name
        page: Page number (1-indexed)
        page_size: Number of rows per page (max 500)
        db_id: Database configuration ID
        
    Returns:
        Paginated table data with column names and row values
    """
    try:
        return DataExplorerService.get_table_rows(schema, table, page, page_size, db_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch rows: {str(e)}")


@router.get("/tables/{schema}/{table}/summary", response_model=TableSummaryResponse)
async def get_table_summary(
    schema: str,
    table: str,
    db_id: str = Query(default="default", description="Database ID")
):
    """
    Get summary statistics for a table.
    
    Computes basic statistics for numeric columns (min, max, avg)
    and distinct counts for all columns.
    
    Args:
        schema: Schema name
        table: Table name
        db_id: Database configuration ID
        
    Returns:
        Column statistics including min/max/avg for numeric columns
    """
    try:
        return DataExplorerService.get_table_summary(schema, table, db_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    db_id: str = Query(default="default", description="Database ID")
):
    """
    Execute a read-only SQL query.
    
    Only SELECT queries are allowed. The query is validated for safety
    and will be rejected if it contains any mutating operations.
    
    Args:
        request: Query request with SQL, pagination params
        db_id: Database configuration ID
        
    Returns:
        Query results with columns, rows, execution time, or error details
    """
    try:
        return DataExplorerService.execute_query(
            request.sql,
            request.page,
            request.page_size,
            db_id
        )
    except Exception as e:
        # Return error in structured format rather than raising exception
        return QueryResponse(
            columns=[],
            rows=[],
            total_rows_estimate=None,
            execution_time_ms=0,
            error={"message": str(e), "code": "INTERNAL_ERROR"}
        )


# =====================================================================
# MCP HTTP Bridge Endpoints for Non-MCP LLMs (xAI, Gemini, ChatGPT)
# =====================================================================
# These endpoints mirror the MCP tools but over HTTP POST.
# They accept JSON request bodies and return JSON responses.
# Compatible with function calling / tools in xAI, Gemini, OpenAI APIs.
# =====================================================================


class ListConnectionsRequest(BaseModel):
    """Request for list_connections tool."""
    pass  # No parameters needed


class ListSchemasRequest(BaseModel):
    """Request for list_schemas tool."""
    connection_id: str = Field(default="default", description="Database connection ID")


class ListTablesRequest(BaseModel):
    """Request for list_tables tool."""
    connection_id: str = Field(default="default", description="Database connection ID")
    schema: str = Field(default="public", description="Schema name")


class GetTableInfoRequest(BaseModel):
    """Request for get_table_info tool."""
    connection_id: str = Field(default="default", description="Database connection ID")
    schema: str = Field(..., description="Schema name")
    table: str = Field(..., description="Table name")


class SampleRowsRequest(BaseModel):
    """Request for sample_rows tool."""
    connection_id: str = Field(default="default", description="Database connection ID")
    schema: str = Field(..., description="Schema name")
    table: str = Field(..., description="Table name")
    limit: int = Field(default=50, ge=1, le=500, description="Number of rows")
    offset: int = Field(default=0, ge=0, description="Offset")


class ProfileTableRequest(BaseModel):
    """Request for profile_table tool."""
    connection_id: str = Field(default="default", description="Database connection ID")
    schema: str = Field(..., description="Schema name")
    table: str = Field(..., description="Table name")
    max_distinct: int = Field(default=50, ge=1, le=200, description="Max distinct values for categorical columns")


class RunQueryRequest(BaseModel):
    """Request for run_query tool."""
    connection_id: str = Field(default="default", description="Database connection ID")
    sql: str = Field(..., description="SQL query to execute")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=100, ge=1, le=1000, description="Rows per page")


@router.post("/tool/list_connections")
async def tool_list_connections(request: ListConnectionsRequest = Body(...)):
    """
    MCP Bridge: List all available database connections.
    
    Returns list of connection IDs with metadata (host, port, database).
    Use this first to discover which databases you can explore.
    
    Compatible with: xAI, Gemini, ChatGPT function calling.
    """
    try:
        configs = get_database_configs()
        return {
            "success": True,
            "data": [
                {
                    "id": config.id,
                    "label": f"{config.name} ({config.description})",
                    "host": config.host,
                    "port": config.port,
                    "database": config.database
                }
                for config in configs
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }


@router.post("/tool/list_schemas")
async def tool_list_schemas(request: ListSchemasRequest = Body(...)):
    """
    MCP Bridge: List all schemas in a database.
    
    Returns schema names with table counts.
    Use after selecting a connection to see available schemas.
    
    Compatible with: xAI, Gemini, ChatGPT function calling.
    """
    try:
        schemas = DataExplorerService.get_schemas(db_id=request.connection_id)
        return {
            "success": True,
            "data": [
                {"name": s.name, "table_count": s.table_count}
                for s in schemas
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }


@router.post("/tool/list_tables")
async def tool_list_tables(request: ListTablesRequest = Body(...)):
    """
    MCP Bridge: List all tables and views in a schema.
    
    Returns table names, types (table/view), and row estimates.
    Use to discover tables before inspecting structure.
    
    Compatible with: xAI, Gemini, ChatGPT function calling.
    """
    try:
        tables = DataExplorerService.get_tables(
            schema=request.schema,
            db_id=request.connection_id
        )
        return {
            "success": True,
            "data": [
                {
                    "schema": t.schema,
                    "name": t.name,
                    "type": t.type,
                    "row_estimate": t.row_estimate
                }
                for t in tables
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }


@router.post("/tool/get_table_info")
async def tool_get_table_info(request: GetTableInfoRequest = Body(...)):
    """
    MCP Bridge: Get detailed column metadata for a table.
    
    Returns column names, data types, nullable status, defaults, and positions.
    Use before querying or sampling to understand table structure.
    
    Compatible with: xAI, Gemini, ChatGPT function calling.
    """
    try:
        columns = DataExplorerService.get_columns(
            schema=request.schema,
            table=request.table,
            db_id=request.connection_id
        )
        return {
            "success": True,
            "data": {
                "schema": request.schema,
                "table": request.table,
                "columns": [
                    {
                        "name": c.name,
                        "data_type": c.data_type,
                        "is_nullable": c.is_nullable,
                        "default": c.default,
                        "ordinal_position": c.ordinal_position
                    }
                    for c in columns
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }


@router.post("/tool/sample_rows")
async def tool_sample_rows(request: SampleRowsRequest = Body(...)):
    """
    MCP Bridge: Sample rows from a table with pagination.
    
    Returns column names, data rows, and pagination info.
    Default limit is 50 rows, maximum is 500.
    Use to preview actual data before running complex queries.
    
    Compatible with: xAI, Gemini, ChatGPT function calling.
    """
    try:
        # Convert limit/offset to page/page_size
        page = (request.offset // request.limit) + 1
        page_size = min(request.limit, 500)
        
        result = DataExplorerService.get_table_rows(
            schema=request.schema,
            table=request.table,
            page=page,
            page_size=page_size,
            db_id=request.connection_id
        )
        return {
            "success": True,
            "data": {
                "schema": result.schema,
                "table": result.table,
                "columns": result.columns,
                "rows": result.rows,
                "page": result.page,
                "page_size": result.page_size,
                "total_rows": result.total_rows
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }


@router.post("/tool/profile_table")
async def tool_profile_table(request: ProfileTableRequest = Body(...)):
    """
    MCP Bridge: Generate comprehensive statistical profile for a table.
    
    Returns per-column statistics including:
    - Data type and nullable status
    - Null counts and null fraction
    - Approximate distinct value counts
    - For numeric columns: min, max, average
    - For categorical columns: top K values with counts
    
    Use to understand data distribution and quality before analysis.
    
    Compatible with: xAI, Gemini, ChatGPT function calling.
    """
    try:
        result = DataExplorerService.profile_table(
            schema=request.schema,
            table=request.table,
            max_distinct=request.max_distinct,
            db_id=request.connection_id
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }


@router.post("/tool/run_query")
async def tool_run_query(request: RunQueryRequest = Body(...)):
    """
    MCP Bridge: Execute a custom SQL query (SELECT only, read-only).
    
    Enforces safety: only SELECT/WITH queries allowed, no mutations.
    Returns columns, rows, execution time, and row count.
    Query timeout is 30 seconds. Maximum page size is 1000 rows.
    
    Use for custom analysis after exploring table structures.
    
    Compatible with: xAI, Gemini, ChatGPT function calling.
    """
    try:
        result = DataExplorerService.execute_query(
            sql=request.sql,
            page=request.page,
            page_size=request.page_size,
            db_id=request.connection_id
        )
        
        response_data = {
            "columns": result.columns,
            "rows": result.rows,
            "total_rows_estimate": result.total_rows_estimate,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error
        }
        
        # Add summary if no error
        if not result.error:
            row_count = len(result.rows)
            total_rows = result.total_rows_estimate or row_count
            response_data["summary"] = (
                f"Query returned {row_count} row(s) (total: {total_rows}) "
                f"in {result.execution_time_ms:.2f}ms"
            )
        
        return {
            "success": not bool(result.error),
            "data": response_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"message": str(e), "code": "INTERNAL_ERROR"}
        }

