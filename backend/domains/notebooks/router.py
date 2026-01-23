"""Notebooks API router."""
import logging
import time
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from .db_models import notebooks, notebook_cells, notebook_datasets
from .models import (
    NotebookCreate, NotebookUpdate, NotebookResponse, NotebookDetailResponse, NotebookListResponse,
    CellCreate, CellUpdate, CellResponse, CellExecuteRequest, CellExecuteResponse,
    PythonExecuteRequest, PythonExecuteResponse, SessionVariablesResponse, VariableInfo,
    DatasetCreate, DatasetResponse, DatasetListResponse
)
from .executor import SQLExecutor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notebooks", tags=["notebooks"])


# ============================================================================
# SESSION DEPENDENCY
# ============================================================================

async def get_async_session():
    """Get async database session."""
    async_url = settings.database_url.replace('postgresql+psycopg', 'postgresql+asyncpg')
    if 'asyncpg' not in async_url:
        async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(async_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.commit()


# ============================================================================
# NOTEBOOK CRUD
# ============================================================================

@router.get("", response_model=NotebookListResponse)
async def list_notebooks(
    folder: Optional[str] = Query(None, description="Filter by folder"),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session)
):
    """List all notebooks."""
    stmt = select(notebooks)
    
    if folder is not None:
        stmt = stmt.where(notebooks.c.folder == folder)
    if search:
        stmt = stmt.where(notebooks.c.name.ilike(f"%{search}%"))
    
    stmt = stmt.order_by(notebooks.c.updated_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    rows = result.fetchall()
    
    # Get cell counts
    notebook_ids = [r.id for r in rows]
    cell_counts = {}
    if notebook_ids:
        count_stmt = (
            select(notebook_cells.c.notebook_id, func.count(notebook_cells.c.id))
            .where(notebook_cells.c.notebook_id.in_(notebook_ids))
            .group_by(notebook_cells.c.notebook_id)
        )
        count_result = await session.execute(count_stmt)
        cell_counts = dict(count_result.fetchall())
    
    notebooks_list = [
        NotebookResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            folder=r.folder or "",
            tags=r.tags or [],
            default_connection_id=r.default_connection_id,
            created_by=r.created_by,
            created_at=r.created_at,
            updated_at=r.updated_at,
            cell_count=cell_counts.get(r.id, 0)
        )
        for r in rows
    ]
    
    # Get total count
    count_stmt = select(func.count(notebooks.c.id))
    if folder is not None:
        count_stmt = count_stmt.where(notebooks.c.folder == folder)
    if search:
        count_stmt = count_stmt.where(notebooks.c.name.ilike(f"%{search}%"))
    total = await session.scalar(count_stmt)
    
    return NotebookListResponse(notebooks=notebooks_list, total=total or 0)


@router.post("", response_model=NotebookDetailResponse, status_code=201)
async def create_notebook(
    request: NotebookCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new notebook."""
    notebook_id = uuid4()
    
    await session.execute(
        notebooks.insert().values(
            id=notebook_id,
            name=request.name,
            description=request.description,
            folder=request.folder,
            tags=request.tags,
            default_connection_id=request.default_connection_id,
            created_by="user"  # TODO: Get from auth
        )
    )
    await session.commit()
    
    return NotebookDetailResponse(
        id=notebook_id,
        name=request.name,
        description=request.description,
        folder=request.folder,
        tags=request.tags,
        default_connection_id=request.default_connection_id,
        cells=[],
        created_by="user",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


# ============================================================================
# DATASET MANAGEMENT (must be before /{notebook_id} routes)
# ============================================================================

@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets(
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session)
):
    """List all saved datasets."""
    stmt = select(notebook_datasets)
    
    if search:
        stmt = stmt.where(notebook_datasets.c.name.ilike(f"%{search}%"))
    
    stmt = stmt.order_by(notebook_datasets.c.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    rows = result.fetchall()
    
    datasets = [
        DatasetResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            source_notebook_id=r.source_notebook_id,
            source_cell_id=r.source_cell_id,
            source_query=r.source_query,
            storage_uri=r.storage_uri,
            storage_format=r.storage_format or "parquet",
            row_count=r.row_count,
            column_count=r.column_count,
            size_bytes=r.size_bytes,
            columns=r.columns or [],
            created_by=r.created_by,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in rows
    ]
    
    count_stmt = select(func.count(notebook_datasets.c.id))
    if search:
        count_stmt = count_stmt.where(notebook_datasets.c.name.ilike(f"%{search}%"))
    total = await session.scalar(count_stmt)
    
    return DatasetListResponse(datasets=datasets, total=total or 0)


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a single dataset by ID."""
    stmt = select(notebook_datasets).where(notebook_datasets.c.id == dataset_id)
    result = await session.execute(stmt)
    r = result.fetchone()
    
    if not r:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return DatasetResponse(
        id=r.id,
        name=r.name,
        description=r.description,
        source_notebook_id=r.source_notebook_id,
        source_cell_id=r.source_cell_id,
        source_query=r.source_query,
        storage_uri=r.storage_uri,
        storage_format=r.storage_format or "parquet",
        row_count=r.row_count,
        column_count=r.column_count,
        size_bytes=r.size_bytes,
        columns=r.columns or [],
        created_by=r.created_by,
        created_at=r.created_at,
        updated_at=r.updated_at
    )


@router.get("/datasets/{dataset_id}/download")
async def get_dataset_download_url(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a presigned download URL for a dataset."""
    from .dataset_exporter import DatasetExporter
    
    stmt = select(notebook_datasets).where(notebook_datasets.c.id == dataset_id)
    result = await session.execute(stmt)
    r = result.fetchone()
    
    if not r:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not r.storage_uri:
        raise HTTPException(status_code=400, detail="Dataset has no stored data")
    
    exporter = DatasetExporter()
    download_url = exporter.get_download_url(r.storage_uri, expires_in=3600)
    
    return {
        "dataset_id": str(dataset_id),
        "name": r.name,
        "download_url": download_url,
        "format": r.storage_format,
        "size_bytes": r.size_bytes,
        "expires_in": 3600
    }


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: UUID,
    limit: int = Query(100, le=1000),
    session: AsyncSession = Depends(get_async_session)
):
    """Preview rows from a saved dataset."""
    from .dataset_exporter import DatasetExporter
    
    stmt = select(notebook_datasets).where(notebook_datasets.c.id == dataset_id)
    result = await session.execute(stmt)
    r = result.fetchone()
    
    if not r:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not r.storage_uri:
        raise HTTPException(status_code=400, detail="Dataset has no stored data")
    
    exporter = DatasetExporter()
    
    try:
        rows, columns = exporter.read_dataset_sample(
            r.storage_uri,
            r.storage_format or "parquet",
            limit=limit
        )
    except Exception as e:
        logger.error(f"Failed to read dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read dataset: {str(e)}")
    
    return {
        "dataset_id": str(dataset_id),
        "name": r.name,
        "columns": columns,
        "rows": rows,
        "total_rows": r.row_count,
        "showing": len(rows)
    }


@router.delete("/datasets/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a dataset and its stored data."""
    from .dataset_exporter import DatasetExporter
    
    stmt = select(notebook_datasets).where(notebook_datasets.c.id == dataset_id)
    result = await session.execute(stmt)
    r = result.fetchone()
    
    if not r:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Delete from object storage if exists
    if r.storage_uri:
        exporter = DatasetExporter()
        exporter.delete_dataset(r.storage_uri)
    
    # Delete from database
    await session.execute(
        delete(notebook_datasets).where(notebook_datasets.c.id == dataset_id)
    )
    await session.commit()
    
    logger.info(f"Deleted dataset {dataset_id}")


# ============================================================================
# NOTEBOOK CRUD (dynamic paths)
# ============================================================================

@router.get("/{notebook_id}", response_model=NotebookDetailResponse)
async def get_notebook(
    notebook_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a notebook with all its cells."""
    # Get notebook
    stmt = select(notebooks).where(notebooks.c.id == notebook_id)
    result = await session.execute(stmt)
    nb = result.fetchone()
    
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    # Get cells
    cells_stmt = (
        select(notebook_cells)
        .where(notebook_cells.c.notebook_id == notebook_id)
        .order_by(notebook_cells.c.position)
    )
    cells_result = await session.execute(cells_stmt)
    cells = cells_result.fetchall()
    
    cells_list = [
        CellResponse(
            id=c.id,
            notebook_id=c.notebook_id,
            cell_type=c.cell_type,
            content=c.content,
            position=c.position,
            last_run_at=c.last_run_at,
            last_run_duration_ms=c.last_run_duration_ms,
            last_run_status=c.last_run_status,
            last_run_error=c.last_run_error,
            last_run_row_count=c.last_run_row_count,
            cached_results=c.cached_results,
            connection_id=c.connection_id,
            settings=c.settings or {},
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in cells
    ]
    
    return NotebookDetailResponse(
        id=nb.id,
        name=nb.name,
        description=nb.description,
        folder=nb.folder or "",
        tags=nb.tags or [],
        default_connection_id=nb.default_connection_id,
        cells=cells_list,
        created_by=nb.created_by,
        created_at=nb.created_at,
        updated_at=nb.updated_at
    )


@router.patch("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    notebook_id: UUID,
    request: NotebookUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update a notebook."""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await session.execute(
        update(notebooks)
        .where(notebooks.c.id == notebook_id)
        .values(**update_data)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    await session.commit()
    
    # Return updated notebook
    stmt = select(notebooks).where(notebooks.c.id == notebook_id)
    result = await session.execute(stmt)
    nb = result.fetchone()
    
    return NotebookResponse(
        id=nb.id,
        name=nb.name,
        description=nb.description,
        folder=nb.folder or "",
        tags=nb.tags or [],
        default_connection_id=nb.default_connection_id,
        created_by=nb.created_by,
        created_at=nb.created_at,
        updated_at=nb.updated_at,
        cell_count=0
    )


@router.delete("/{notebook_id}", status_code=204)
async def delete_notebook(
    notebook_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a notebook and all its cells."""
    result = await session.execute(
        delete(notebooks).where(notebooks.c.id == notebook_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    await session.commit()


# ============================================================================
# CELL CRUD
# ============================================================================

@router.post("/{notebook_id}/cells", response_model=CellResponse, status_code=201)
async def create_cell(
    notebook_id: UUID,
    request: CellCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Add a new cell to a notebook."""
    # Verify notebook exists
    stmt = select(notebooks).where(notebooks.c.id == notebook_id)
    result = await session.execute(stmt)
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    # Get position
    if request.position is not None:
        position = request.position
        # Shift other cells
        await session.execute(
            update(notebook_cells)
            .where(notebook_cells.c.notebook_id == notebook_id)
            .where(notebook_cells.c.position >= position)
            .values(position=notebook_cells.c.position + 1)
        )
    else:
        # Get max position
        max_pos = await session.scalar(
            select(func.max(notebook_cells.c.position))
            .where(notebook_cells.c.notebook_id == notebook_id)
        )
        position = (max_pos or -1) + 1
    
    cell_id = uuid4()
    await session.execute(
        notebook_cells.insert().values(
            id=cell_id,
            notebook_id=notebook_id,
            cell_type=request.cell_type.value,
            content=request.content,
            position=position,
            connection_id=request.connection_id,
            settings=request.settings
        )
    )
    await session.commit()
    
    return CellResponse(
        id=cell_id,
        notebook_id=notebook_id,
        cell_type=request.cell_type.value,
        content=request.content,
        position=position,
        connection_id=request.connection_id,
        settings=request.settings,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.patch("/{notebook_id}/cells/{cell_id}", response_model=CellResponse)
async def update_cell(
    notebook_id: UUID,
    cell_id: UUID,
    request: CellUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update a cell."""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await session.execute(
        update(notebook_cells)
        .where(notebook_cells.c.id == cell_id)
        .where(notebook_cells.c.notebook_id == notebook_id)
        .values(**update_data)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Cell not found")
    
    await session.commit()
    
    # Return updated cell
    stmt = select(notebook_cells).where(notebook_cells.c.id == cell_id)
    result = await session.execute(stmt)
    c = result.fetchone()
    
    return CellResponse(
        id=c.id,
        notebook_id=c.notebook_id,
        cell_type=c.cell_type,
        content=c.content,
        position=c.position,
        last_run_at=c.last_run_at,
        last_run_duration_ms=c.last_run_duration_ms,
        last_run_status=c.last_run_status,
        last_run_error=c.last_run_error,
        last_run_row_count=c.last_run_row_count,
        cached_results=c.cached_results,
        connection_id=c.connection_id,
        settings=c.settings or {},
        created_at=c.created_at,
        updated_at=c.updated_at
    )


@router.delete("/{notebook_id}/cells/{cell_id}", status_code=204)
async def delete_cell(
    notebook_id: UUID,
    cell_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a cell."""
    # Get cell position first
    stmt = select(notebook_cells.c.position).where(notebook_cells.c.id == cell_id)
    position = await session.scalar(stmt)
    
    if position is None:
        raise HTTPException(status_code=404, detail="Cell not found")
    
    # Delete cell
    await session.execute(
        delete(notebook_cells).where(notebook_cells.c.id == cell_id)
    )
    
    # Shift positions
    await session.execute(
        update(notebook_cells)
        .where(notebook_cells.c.notebook_id == notebook_id)
        .where(notebook_cells.c.position > position)
        .values(position=notebook_cells.c.position - 1)
    )
    
    await session.commit()


# ============================================================================
# CELL EXECUTION
# ============================================================================

@router.post("/{notebook_id}/cells/{cell_id}/execute", response_model=CellExecuteResponse)
async def execute_sql_cell(
    notebook_id: UUID,
    cell_id: UUID,
    request: CellExecuteRequest = CellExecuteRequest(),
    session: AsyncSession = Depends(get_async_session)
):
    """Execute a SQL cell."""
    # Get cell
    stmt = select(notebook_cells).where(
        notebook_cells.c.id == cell_id,
        notebook_cells.c.notebook_id == notebook_id
    )
    result = await session.execute(stmt)
    cell = result.fetchone()
    
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    
    if cell.cell_type != "sql":
        raise HTTPException(status_code=400, detail="Use /execute-python for Python cells")
    
    if not cell.content.strip():
        raise HTTPException(status_code=400, detail="Cell is empty")
    
    # Get connection ID (cell-specific or notebook default)
    connection_id = cell.connection_id
    if not connection_id:
        nb_stmt = select(notebooks.c.default_connection_id).where(notebooks.c.id == notebook_id)
        connection_id = await session.scalar(nb_stmt)
    
    if not connection_id:
        raise HTTPException(status_code=400, detail="No data connection specified")
    
    # Execute SQL
    start_time = time.time()
    executor = SQLExecutor(session)
    rows, columns, row_count, error = await executor.execute_sql(
        connection_id,
        cell.content,
        limit=request.limit,
        timeout_seconds=request.timeout_seconds
    )
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Update cell with results
    status = "error" if error else "success"
    await session.execute(
        update(notebook_cells)
        .where(notebook_cells.c.id == cell_id)
        .values(
            last_run_at=datetime.utcnow(),
            last_run_duration_ms=duration_ms,
            last_run_status=status,
            last_run_error=error,
            last_run_row_count=row_count if not error else None,
            cached_results=rows[:100] if not error else None  # Cache first 100 rows
        )
    )
    await session.commit()
    
    return CellExecuteResponse(
        cell_id=cell_id,
        status=status,
        duration_ms=duration_ms,
        row_count=row_count,
        columns=columns,
        rows=rows,
        truncated=row_count >= request.limit,
        error=error
    )


@router.post("/{notebook_id}/cells/{cell_id}/execute-python", response_model=PythonExecuteResponse)
async def execute_python_cell(
    notebook_id: UUID,
    cell_id: UUID,
    request: PythonExecuteRequest = PythonExecuteRequest(),
    session: AsyncSession = Depends(get_async_session)
):
    """Execute a Python cell."""
    from .python_executor import get_executor
    
    # Get cell
    stmt = select(notebook_cells).where(
        notebook_cells.c.id == cell_id,
        notebook_cells.c.notebook_id == notebook_id
    )
    result = await session.execute(stmt)
    cell = result.fetchone()
    
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    
    if cell.cell_type != "python":
        raise HTTPException(status_code=400, detail="Use /execute for SQL cells")
    
    if not cell.content.strip():
        raise HTTPException(status_code=400, detail="Cell is empty")
    
    # Execute Python
    executor = get_executor(notebook_id)
    exec_result = executor.execute(
        cell.content,
        timeout_seconds=request.timeout_seconds
    )
    
    # Update cell with results
    await session.execute(
        update(notebook_cells)
        .where(notebook_cells.c.id == cell_id)
        .values(
            last_run_at=datetime.utcnow(),
            last_run_duration_ms=exec_result['duration_ms'],
            last_run_status=exec_result['status'],
            last_run_error=exec_result.get('error'),
            cached_results=exec_result.get('outputs')[:10] if exec_result.get('outputs') else None
        )
    )
    await session.commit()
    
    return PythonExecuteResponse(
        cell_id=cell_id,
        status=exec_result['status'],
        duration_ms=exec_result['duration_ms'],
        stdout=exec_result.get('stdout', ''),
        stderr=exec_result.get('stderr', ''),
        result=exec_result.get('result'),
        outputs=exec_result.get('outputs', []),
        variables=exec_result.get('variables', []),
        error=exec_result.get('error'),
        traceback=exec_result.get('traceback')
    )


@router.get("/{notebook_id}/session/variables", response_model=SessionVariablesResponse)
async def get_session_variables(
    notebook_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get all variables in the notebook's Python session."""
    from .python_executor import get_executor
    
    # Verify notebook exists
    stmt = select(notebooks).where(notebooks.c.id == notebook_id)
    result = await session.execute(stmt)
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    executor = get_executor(notebook_id)
    variables = executor.get_variables()
    
    return SessionVariablesResponse(
        notebook_id=notebook_id,
        variables=[VariableInfo(**v) for v in variables]
    )


@router.post("/{notebook_id}/session/reset", status_code=200)
async def reset_session(
    notebook_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Reset the Python session for a notebook (clears all variables)."""
    from .python_executor import get_executor
    
    # Verify notebook exists
    stmt = select(notebooks).where(notebooks.c.id == notebook_id)
    result = await session.execute(stmt)
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    executor = get_executor(notebook_id)
    executor.reset_session()
    
    return {"message": "Session reset successfully", "notebook_id": str(notebook_id)}


# ============================================================================
# SAVE AS DATASET
# ============================================================================

@router.post("/{notebook_id}/cells/{cell_id}/save-dataset", response_model=DatasetResponse, status_code=201)
async def save_cell_as_dataset(
    notebook_id: UUID,
    cell_id: UUID,
    request: DatasetCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Save cell results as a reusable dataset (exports to object storage)."""
    from .dataset_exporter import DatasetExporter
    
    # Get cell
    stmt = select(notebook_cells).where(
        notebook_cells.c.id == cell_id,
        notebook_cells.c.notebook_id == notebook_id
    )
    result = await session.execute(stmt)
    cell = result.fetchone()
    
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    
    if cell.cell_type != "sql":
        raise HTTPException(status_code=400, detail="Only SQL cells can be saved as datasets")
    
    if not cell.content.strip():
        raise HTTPException(status_code=400, detail="Cell is empty")
    
    # Get connection ID
    connection_id = cell.connection_id
    if not connection_id:
        nb_stmt = select(notebooks.c.default_connection_id).where(notebooks.c.id == notebook_id)
        connection_id = await session.scalar(nb_stmt)
    
    if not connection_id:
        raise HTTPException(status_code=400, detail="No data connection specified")
    
    # Re-execute query to get ALL results (up to 100k rows for safety)
    executor = SQLExecutor(session)
    rows, columns, row_count, error = await executor.execute_sql(
        connection_id,
        cell.content,
        limit=100000,  # Max rows for dataset export
        timeout_seconds=300  # Allow longer timeout for large exports
    )
    
    if error:
        raise HTTPException(status_code=400, detail=f"Query failed: {error}")
    
    if not rows:
        raise HTTPException(status_code=400, detail="Query returned no results")
    
    # Generate dataset ID
    dataset_id = uuid4()
    
    # Export to object storage
    exporter = DatasetExporter()
    
    try:
        if request.format == "csv":
            storage_uri, size_bytes = exporter.export_to_csv(dataset_id, rows, columns)
        else:
            storage_uri, size_bytes = exporter.export_to_parquet(dataset_id, rows, columns)
    except Exception as e:
        logger.error(f"Failed to export dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
    
    # Save dataset metadata
    await session.execute(
        notebook_datasets.insert().values(
            id=dataset_id,
            name=request.name,
            description=request.description,
            source_notebook_id=notebook_id,
            source_cell_id=cell_id,
            source_query=cell.content,
            storage_uri=storage_uri,
            storage_format=request.format,
            row_count=row_count,
            column_count=len(columns),
            size_bytes=size_bytes,
            columns=columns,
            created_by="user"
        )
    )
    await session.commit()
    
    logger.info(f"Created dataset {dataset_id}: {request.name} ({row_count} rows, {size_bytes} bytes)")
    
    return DatasetResponse(
        id=dataset_id,
        name=request.name,
        description=request.description,
        source_notebook_id=notebook_id,
        source_cell_id=cell_id,
        source_query=cell.content,
        storage_uri=storage_uri,
        storage_format=request.format,
        row_count=row_count,
        column_count=len(columns),
        size_bytes=size_bytes,
        columns=columns,
        created_by="user",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
