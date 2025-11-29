"""
Data Explorer API router.

Provides endpoints for browsing database schemas, tables, and executing read-only queries.
All endpoints are prefixed with /api/v1/data-explorer.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel

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

