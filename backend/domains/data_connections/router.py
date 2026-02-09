"""Data Connections API router."""
import logging
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.encryption import encrypt_password
from core.rbac import require_role, require_admin
from domains.auth.models import User, Role
from .db_models import data_connections, table_scans
from .models import (
    DataConnectionCreate, DataConnectionUpdate, DataConnectionResponse,
    DataConnectionListResponse, ScanRequest, ConnectionScanResponse,
    TableScanResponse, TableScanSummary, TableScanDetail,
    RecipeCompatibilityResponse, TableCompatibilityResponse
)
from .scanner import DataScanner
from .compatibility import RecipeCompatibilityChecker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data-connections", tags=["data-connections"])


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
# STATIC ROUTES (must come before dynamic /{connection_id} routes)
# ============================================================================

@router.get("/recipes", response_model=List[dict])
async def list_recipes():
    """List all available recipes that can be checked for compatibility."""
    checker = RecipeCompatibilityChecker(None)  # Session not needed for this
    return checker.get_available_recipes()


@router.post("/quick-scan")
async def quick_scan(
    host: str = Query(..., description="Database host"),
    port: int = Query(5432, description="Database port"),
    database: str = Query(..., description="Database name"),
    username: str = Query(..., description="Username"),
    password: str = Query(..., description="Password"),
    table: Optional[str] = Query(None, description="Specific table to scan (schema.table)"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Quick scan without creating a persistent connection.
    
    Useful for one-off data exploration.
    """
    import asyncpg
    
    try:
        pg_conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=10
        )
        
        if table:
            # Scan specific table
            parts = table.split('.')
            schema = parts[0] if len(parts) > 1 else 'public'
            name = parts[-1]
            
            # Get row count
            row_count = await pg_conn.fetchval(f'SELECT COUNT(*) FROM "{schema}"."{name}"')
            
            # Get columns
            columns = await pg_conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """, schema, name)
            
            # Get sample
            sample = await pg_conn.fetch(f'SELECT * FROM "{schema}"."{name}" LIMIT 5')
            
            await pg_conn.close()
            
            return {
                "table": f"{schema}.{name}",
                "row_count": row_count,
                "columns": [
                    {"name": c["column_name"], "type": c["data_type"], "nullable": c["is_nullable"] == "YES"}
                    for c in columns
                ],
                "sample": [dict(r) for r in sample]
            }
        else:
            # List all tables
            tables = await pg_conn.fetch("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """)
            
            await pg_conn.close()
            
            return {
                "database": database,
                "tables": [f"{t['table_schema']}.{t['table_name']}" for t in tables],
                "count": len(tables)
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {e}")


@router.get("/scans/{scan_id}", response_model=TableScanDetail)
async def get_table_scan(
    scan_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get detailed scan results for a table."""
    scanner = DataScanner(session)
    detail = await scanner.get_table_scan_detail(scan_id)
    
    if not detail:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return detail


@router.get("/scans/{scan_id}/compatibility", response_model=TableCompatibilityResponse)
async def check_all_compatibility(
    scan_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Check table compatibility against all available recipes."""
    scanner = DataScanner(session)
    checker = RecipeCompatibilityChecker(session)
    
    # Get the scan
    detail = await scanner.get_table_scan_detail(scan_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return await checker.check_all_recipes(detail)


@router.get("/scans/{scan_id}/compatibility/{recipe_id}", response_model=RecipeCompatibilityResponse)
async def check_recipe_compatibility(
    scan_id: UUID,
    recipe_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Check table compatibility against a specific recipe."""
    scanner = DataScanner(session)
    checker = RecipeCompatibilityChecker(session)
    
    # Get the scan
    detail = await scanner.get_table_scan_detail(scan_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    try:
        return await checker.check_compatibility(detail, recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# CONNECTION CRUD
# ============================================================================

@router.get("", response_model=DataConnectionListResponse)
async def list_connections(
    connection_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_async_session)
):
    """List all data connections."""
    stmt = select(data_connections)
    
    if connection_type:
        stmt = stmt.where(data_connections.c.connection_type == connection_type)
    if status:
        stmt = stmt.where(data_connections.c.status == status)
    
    stmt = stmt.order_by(data_connections.c.name)
    result = await session.execute(stmt)
    rows = result.fetchall()
    
    connections = [
        DataConnectionResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            connection_type=r.connection_type,
            host=r.host,
            port=r.port,
            database=r.database,
            username=r.username,
            status=r.status,
            last_connected_at=r.last_connected_at,
            last_error=r.last_error,
            last_scan_at=r.last_scan_at,
            scan_status=r.scan_status,
            tables_count=r.tables_count or 0,
            total_rows=r.total_rows or 0,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in rows
    ]
    
    return DataConnectionListResponse(connections=connections, total=len(connections))


@router.post("", response_model=DataConnectionResponse, status_code=201)
async def create_connection(
    request: DataConnectionCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(Role.DATA_SCIENTIST))
):
    """Create a new data connection.

    Requires data_scientist role or higher.
    """
    conn_id = uuid4()
    
    # Encrypt the password before storage
    password_encrypted = encrypt_password(request.password)
    
    await session.execute(
        data_connections.insert().values(
            id=conn_id,
            name=request.name,
            description=request.description,
            connection_type=request.connection_type.value,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password_encrypted=password_encrypted,
            extra_config=request.extra_config,
            status="pending"
        )
    )
    await session.commit()
    
    # Fetch and return
    stmt = select(data_connections).where(data_connections.c.id == conn_id)
    result = await session.execute(stmt)
    r = result.fetchone()
    
    return DataConnectionResponse(
        id=r.id,
        name=r.name,
        description=r.description,
        connection_type=r.connection_type,
        host=r.host,
        port=r.port,
        database=r.database,
        username=r.username,
        status=r.status,
        last_connected_at=r.last_connected_at,
        last_error=r.last_error,
        last_scan_at=r.last_scan_at,
        scan_status=r.scan_status or "never",
        tables_count=r.tables_count or 0,
        total_rows=r.total_rows or 0,
        created_at=r.created_at,
        updated_at=r.updated_at
    )


@router.get("/{connection_id}", response_model=DataConnectionResponse)
async def get_connection(
    connection_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific data connection."""
    stmt = select(data_connections).where(data_connections.c.id == connection_id)
    result = await session.execute(stmt)
    r = result.fetchone()
    
    if not r:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return DataConnectionResponse(
        id=r.id,
        name=r.name,
        description=r.description,
        connection_type=r.connection_type,
        host=r.host,
        port=r.port,
        database=r.database,
        username=r.username,
        status=r.status,
        last_connected_at=r.last_connected_at,
        last_error=r.last_error,
        last_scan_at=r.last_scan_at,
        scan_status=r.scan_status or "never",
        tables_count=r.tables_count or 0,
        total_rows=r.total_rows or 0,
        created_at=r.created_at,
        updated_at=r.updated_at
    )


@router.patch("/{connection_id}", response_model=DataConnectionResponse)
async def update_connection(
    connection_id: UUID,
    request: DataConnectionUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(Role.DATA_SCIENTIST))
):
    """Update a data connection.

    Requires data_scientist role or higher.
    All fields are optional. Password will be encrypted before storage.
    """
    from datetime import datetime
    from sqlalchemy import update

    # Check connection exists
    stmt = select(data_connections).where(data_connections.c.id == connection_id)
    result = await session.execute(stmt)
    existing = result.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Build update values
    update_values = {"updated_at": datetime.utcnow()}

    if request.name is not None:
        update_values["name"] = request.name
    if request.description is not None:
        update_values["description"] = request.description
    if request.host is not None:
        update_values["host"] = request.host
    if request.port is not None:
        update_values["port"] = request.port
    if request.database is not None:
        update_values["database"] = request.database
    if request.username is not None:
        update_values["username"] = request.username
    if request.password is not None:
        # Encrypt password before storing
        update_values["password_encrypted"] = encrypt_password(request.password)
    if request.extra_config is not None:
        update_values["extra_config"] = request.extra_config

    # Update the connection
    await session.execute(
        update(data_connections)
        .where(data_connections.c.id == connection_id)
        .values(**update_values)
    )
    await session.commit()

    # Fetch updated connection
    result = await session.execute(stmt)
    r = result.fetchone()

    logger.info(f"Updated connection {connection_id}")

    return DataConnectionResponse(
        id=r.id,
        name=r.name,
        description=r.description,
        connection_type=r.connection_type,
        host=r.host,
        port=r.port,
        database=r.database,
        username=r.username,
        status=r.status,
        last_connected_at=r.last_connected_at,
        last_error=r.last_error,
        last_scan_at=r.last_scan_at,
        scan_status=r.scan_status or "never",
        tables_count=r.tables_count or 0,
        total_rows=r.total_rows or 0,
        created_at=r.created_at,
        updated_at=r.updated_at
    )


@router.delete("/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """Delete a data connection and its scans.

    Requires admin role.
    """
    # Delete scans first (cascade should handle this, but be explicit)
    await session.execute(
        delete(table_scans).where(table_scans.c.connection_id == connection_id)
    )
    
    result = await session.execute(
        delete(data_connections).where(data_connections.c.id == connection_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    await session.commit()


# ============================================================================
# CONNECTION TESTING & SCANNING
# ============================================================================

@router.post("/{connection_id}/test")
async def test_connection(
    connection_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Test if a connection is working."""
    scanner = DataScanner(session)
    success, error = await scanner.test_connection(connection_id)
    
    return {
        "connection_id": str(connection_id),
        "success": success,
        "error": error
    }


@router.post("/{connection_id}/scan", response_model=ConnectionScanResponse)
async def scan_connection(
    connection_id: UUID,
    request: ScanRequest = ScanRequest(),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Scan all tables in a connection.
    
    This discovers tables, counts rows, and detects column types.
    """
    scanner = DataScanner(session)
    
    try:
        result = await scanner.scan_connection(
            connection_id,
            full_scan=request.full_scan,
            sample_size=request.sample_size
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")


@router.get("/{connection_id}/tables", response_model=List[TableScanSummary])
async def list_tables(
    connection_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get all scanned tables for a connection."""
    scanner = DataScanner(session)
    return await scanner.get_table_scans(connection_id)


@router.post("/{connection_id}/tables/{table_name:path}/scan", response_model=TableScanResponse)
async def scan_table(
    connection_id: UUID,
    table_name: str,
    request: ScanRequest = ScanRequest(),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Deep scan a specific table.
    
    Analyzes all columns with statistics, quality issues, and sample data.
    """
    scanner = DataScanner(session)
    
    try:
        result = await scanner.scan_table(
            connection_id,
            table_name,
            sample_size=request.sample_size,
            include_sample=request.include_sample_data
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Table scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")
