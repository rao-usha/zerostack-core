"""Query Workbench API router.

Provides endpoints for saving, managing, and executing reusable SQL queries.
All endpoints are prefixed with /api/v1/data-explorer/workbench.
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional

from .query_workbench_models import (
    SavedQueryCreate,
    SavedQueryUpdate,
    SavedQueryResponse,
    SavedQueryListItem,
    SavedQueryListResponse,
    ExecuteQueryRequest,
    QueryExecutionResponse,
    QueryExecutionListResponse,
    QueryResultResponse,
    FolderInfo
)
from .query_workbench_service import get_query_workbench_service


router = APIRouter(prefix="/data-explorer/workbench", tags=["query-workbench"])


# ========================================
# Saved Query CRUD
# ========================================

@router.post("/queries", response_model=SavedQueryResponse)
async def create_query(request: SavedQueryCreate):
    """
    Create a new saved query.

    Args:
        request: Query details including name, SQL, and optional metadata

    Returns:
        The created saved query with ID
    """
    try:
        service = get_query_workbench_service()
        result = service.create_query(
            name=request.name,
            sql=request.sql,
            db_id=request.db_id,
            description=request.description,
            folder=request.folder,
            tags=request.tags,
            parameters=[p.model_dump() for p in request.parameters] if request.parameters else None,
            is_public=request.is_public
        )
        return SavedQueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create query: {str(e)}")


@router.get("/queries", response_model=SavedQueryListResponse)
async def list_queries(
    db_id: Optional[str] = Query(None, description="Filter by database ID"),
    folder: Optional[str] = Query(None, description="Filter by folder"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    search: Optional[str] = Query(None, description="Search in name, description, SQL"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Results per page")
):
    """
    List saved queries with optional filtering.

    Args:
        db_id: Filter by database ID
        folder: Filter by folder name
        tags: Filter by tags (comma-separated)
        search: Search term for name/description/SQL
        is_public: Filter by public/private status
        page: Page number (1-indexed)
        page_size: Results per page (max 100)

    Returns:
        Paginated list of saved queries
    """
    try:
        service = get_query_workbench_service()
        tag_list = [t.strip() for t in tags.split(",")] if tags else None

        queries, total = service.list_queries(
            db_id=db_id,
            folder=folder,
            tags=tag_list,
            search=search,
            is_public=is_public,
            page=page,
            page_size=page_size
        )

        return SavedQueryListResponse(
            queries=[SavedQueryListItem(**q) for q in queries],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list queries: {str(e)}")


@router.get("/queries/{query_id}", response_model=SavedQueryResponse)
async def get_query(query_id: str):
    """
    Get a saved query by ID.

    Args:
        query_id: The query UUID

    Returns:
        The saved query details
    """
    try:
        service = get_query_workbench_service()
        result = service.get_query(query_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

        return SavedQueryResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query: {str(e)}")


@router.put("/queries/{query_id}", response_model=SavedQueryResponse)
async def update_query(query_id: str, request: SavedQueryUpdate):
    """
    Update a saved query.

    Args:
        query_id: The query UUID
        request: Fields to update (only provided fields are changed)

    Returns:
        The updated saved query
    """
    try:
        service = get_query_workbench_service()

        # Build update kwargs from non-None fields
        update_data = request.model_dump(exclude_unset=True)
        if 'parameters' in update_data and update_data['parameters']:
            update_data['parameters'] = [p.model_dump() if hasattr(p, 'model_dump') else p for p in update_data['parameters']]

        result = service.update_query(query_id, **update_data)

        if not result:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

        return SavedQueryResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update query: {str(e)}")


@router.delete("/queries/{query_id}")
async def delete_query(query_id: str):
    """
    Delete a saved query.

    Args:
        query_id: The query UUID

    Returns:
        Success message
    """
    try:
        service = get_query_workbench_service()
        deleted = service.delete_query(query_id)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

        return {"message": "Query deleted successfully", "id": query_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete query: {str(e)}")


@router.post("/queries/{query_id}/clone", response_model=SavedQueryResponse)
async def clone_query(
    query_id: str,
    new_name: str = Query(..., description="Name for the cloned query")
):
    """
    Clone a saved query.

    Args:
        query_id: The query UUID to clone
        new_name: Name for the new cloned query

    Returns:
        The newly created clone
    """
    try:
        service = get_query_workbench_service()
        result = service.clone_query(query_id, new_name)
        return SavedQueryResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clone query: {str(e)}")


# ========================================
# Query Execution
# ========================================

@router.post("/queries/{query_id}/execute", response_model=QueryResultResponse)
async def execute_saved_query(query_id: str, request: ExecuteQueryRequest = Body(default=None)):
    """
    Execute a saved query.

    Args:
        query_id: The query UUID to execute
        request: Optional parameters and pagination settings

    Returns:
        Query results with execution metadata
    """
    try:
        service = get_query_workbench_service()

        if request is None:
            request = ExecuteQueryRequest()

        result = service.execute_query(
            query_id=query_id,
            parameters=request.parameters,
            page=request.page,
            page_size=request.page_size,
            source='manual'
        )

        return QueryResultResponse(
            execution_id=result['execution_id'],
            columns=result['columns'],
            rows=result['rows'],
            total_rows=result['total_rows'],
            execution_time_ms=result['execution_time_ms'],
            page=result['page'],
            page_size=result['page_size']
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.post("/execute", response_model=QueryResultResponse)
async def execute_adhoc_query(
    sql: str = Body(..., embed=True, description="SQL query to execute"),
    db_id: str = Body("default", embed=True, description="Database ID"),
    parameters: Optional[dict] = Body(None, embed=True, description="Query parameters"),
    page: int = Body(1, embed=True, ge=1, description="Page number"),
    page_size: int = Body(100, embed=True, ge=1, le=1000, description="Results per page")
):
    """
    Execute an ad-hoc query (not saved).

    Args:
        sql: The SQL query to execute
        db_id: Database ID to run against
        parameters: Optional {{param}} substitutions
        page: Page number for results
        page_size: Results per page

    Returns:
        Query results with execution metadata
    """
    try:
        service = get_query_workbench_service()

        result = service.execute_adhoc_query(
            sql=sql,
            db_id=db_id,
            parameters=parameters,
            page=page,
            page_size=page_size
        )

        return QueryResultResponse(
            execution_id=result['execution_id'],
            columns=result['columns'],
            rows=result['rows'],
            total_rows=result['total_rows'],
            execution_time_ms=result['execution_time_ms'],
            page=result['page'],
            page_size=result['page_size']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


# ========================================
# Execution History
# ========================================

@router.get("/queries/{query_id}/executions", response_model=QueryExecutionListResponse)
async def get_query_executions(
    query_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return")
):
    """
    Get execution history for a saved query.

    Args:
        query_id: The query UUID
        limit: Maximum number of executions to return

    Returns:
        List of execution records for the query
    """
    try:
        service = get_query_workbench_service()
        executions = service.get_query_executions(query_id, limit=limit)

        return QueryExecutionListResponse(
            executions=[QueryExecutionResponse(**e) for e in executions],
            total=len(executions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get executions: {str(e)}")


@router.get("/executions/{execution_id}", response_model=QueryExecutionResponse)
async def get_execution(execution_id: str):
    """
    Get a specific execution record.

    Args:
        execution_id: The execution UUID

    Returns:
        The execution record with results preview
    """
    try:
        service = get_query_workbench_service()
        result = service.get_execution(execution_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        return QueryExecutionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")


@router.get("/executions", response_model=QueryExecutionListResponse)
async def list_recent_executions(
    db_id: Optional[str] = Query(None, description="Filter by database ID"),
    status: Optional[str] = Query(None, description="Filter by status (running, success, error)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return")
):
    """
    Get recent executions across all queries.

    Args:
        db_id: Filter by database ID
        status: Filter by execution status
        limit: Maximum number of executions to return

    Returns:
        List of recent execution records
    """
    try:
        service = get_query_workbench_service()
        executions = service.get_recent_executions(
            db_id=db_id,
            status=status,
            limit=limit
        )

        return QueryExecutionListResponse(
            executions=[QueryExecutionResponse(**e) for e in executions],
            total=len(executions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get executions: {str(e)}")


# ========================================
# Folders
# ========================================

@router.get("/folders", response_model=List[FolderInfo])
async def list_folders(
    db_id: Optional[str] = Query(None, description="Filter by database ID")
):
    """
    Get list of folders with query counts.

    Args:
        db_id: Optional database ID filter

    Returns:
        List of folders with the number of queries in each
    """
    try:
        service = get_query_workbench_service()
        folders = service.get_folders(db_id=db_id)
        return [FolderInfo(**f) for f in folders]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get folders: {str(e)}")
