"""
API router for Data Dictionary Relationship Intelligence.

Provides endpoints for discovering, managing, and querying relationships
between data assets.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection
from typing import Optional, List
import uuid
from datetime import datetime

from db.connection import get_db_connection
from .relationship_intelligence_models import (
    DictionaryRelationship,
    DictionaryRelationshipCreate,
    DictionaryRelationshipUpdate,
    RelationshipAcceptRequest,
    RelationshipRejectRequest,
    RelationshipListResponse,
    AssetRelationshipsResponse,
    DiscoveryJob,
    DiscoveryJobCreate,
    DiscoveryJobSummary,
    DiscoveryConfig,
    RelationshipType,
    RelationshipStatus,
    DiscoveryJobStatus,
)
from .relationship_intelligence_service import (
    RelationshipDiscoveryService,
    RelationshipCRUDService,
)
from db.models import dictionary_relationship_discovery_jobs
from sqlalchemy import insert, select, update


router = APIRouter(prefix="/dictionary/relationships", tags=["dictionary-relationships"])


# ============================================================================
# Relationship CRUD Endpoints
# ============================================================================

@router.post("", response_model=DictionaryRelationship, status_code=201)
def create_relationship(
    rel: DictionaryRelationshipCreate,
    conn: Connection = Depends(get_db_connection)
):
    """
    Create a new relationship manually.
    
    This is typically used for curating semantic relationships that are not
    auto-discovered.
    """
    try:
        return RelationshipCRUDService.create_relationship(conn, rel)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rel_id}", response_model=DictionaryRelationship)
def get_relationship(
    rel_id: str,
    conn: Connection = Depends(get_db_connection)
):
    """Get a specific relationship by ID."""
    rel = RelationshipCRUDService.get_relationship(conn, rel_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel


@router.get("", response_model=RelationshipListResponse)
def list_relationships(
    status: Optional[RelationshipStatus] = None,
    relationship_type: Optional[RelationshipType] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    skip: int = 0,
    limit: int = 100,
    conn: Connection = Depends(get_db_connection)
):
    """
    List all relationships with optional filters.
    
    - **status**: Filter by suggestion status (suggested, accepted, rejected)
    - **relationship_type**: Filter by relationship type
    - **min_confidence**: Only return relationships with confidence >= this value
    - **skip**: Pagination offset
    - **limit**: Page size (max 100)
    """
    relationships, total = RelationshipCRUDService.list_relationships(
        conn, status, relationship_type, min_confidence, skip, limit
    )
    
    return RelationshipListResponse(
        relationships=relationships,
        total=total
    )


@router.get("/asset/{database}/{schema}/{table}", response_model=AssetRelationshipsResponse)
def get_table_relationships(
    database: str,
    schema: str,
    table: str,
    conn: Connection = Depends(get_db_connection)
):
    """
    Get all relationships involving a specific table.
    
    Returns both incoming and outgoing relationships.
    """
    incoming, outgoing = RelationshipCRUDService.get_asset_relationships(
        conn, database, schema, table, column=None
    )
    
    return AssetRelationshipsResponse(
        asset_identifier=f"{database}.{schema}.{table}",
        incoming_relationships=incoming,
        outgoing_relationships=outgoing,
        total_incoming=len(incoming),
        total_outgoing=len(outgoing)
    )


@router.get("/asset/{database}/{schema}/{table}/{column}", response_model=AssetRelationshipsResponse)
def get_column_relationships(
    database: str,
    schema: str,
    table: str,
    column: str,
    conn: Connection = Depends(get_db_connection)
):
    """
    Get all relationships involving a specific column.
    
    Returns both incoming and outgoing relationships.
    """
    incoming, outgoing = RelationshipCRUDService.get_asset_relationships(
        conn, database, schema, table, column=column
    )
    
    return AssetRelationshipsResponse(
        asset_identifier=f"{database}.{schema}.{table}.{column}",
        incoming_relationships=incoming,
        outgoing_relationships=outgoing,
        total_incoming=len(incoming),
        total_outgoing=len(outgoing)
    )


@router.post("/{rel_id}/accept", response_model=DictionaryRelationship)
def accept_relationship(
    rel_id: str,
    request: RelationshipAcceptRequest,
    conn: Connection = Depends(get_db_connection)
):
    """
    Accept a suggested relationship.
    
    Moves the relationship from 'suggested' to 'accepted' status, making it
    part of the canonical data dictionary.
    """
    rel = RelationshipCRUDService.accept_relationship(
        conn, rel_id, request.reviewed_by
    )
    
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    return rel


@router.post("/{rel_id}/reject", response_model=DictionaryRelationship)
def reject_relationship(
    rel_id: str,
    request: RelationshipRejectRequest,
    conn: Connection = Depends(get_db_connection)
):
    """
    Reject a suggested relationship.
    
    Moves the relationship to 'rejected' status, removing it from suggestions.
    """
    rel = RelationshipCRUDService.reject_relationship(
        conn, rel_id, request.reviewed_by
    )
    
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    return rel


@router.delete("/{rel_id}")
def delete_relationship(
    rel_id: str,
    conn: Connection = Depends(get_db_connection)
):
    """
    Delete a relationship permanently.
    
    Only suggested and rejected relationships can be deleted. Accepted
    relationships should be rejected first.
    """
    # Check status before deleting
    rel = RelationshipCRUDService.get_relationship(conn, rel_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    if rel.status == RelationshipStatus.accepted:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete accepted relationship. Reject it first."
        )
    
    success = RelationshipCRUDService.delete_relationship(conn, rel_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    return {"message": "Relationship deleted successfully"}


# ============================================================================
# Discovery Job Endpoints
# ============================================================================

@router.post("/discover", response_model=DiscoveryJob, status_code=202)
def start_discovery_job(
    job_create: DiscoveryJobCreate,
    conn: Connection = Depends(get_db_connection)
):
    """
    Start a relationship discovery job.
    
    The job will analyze the specified database/schema/tables and discover
    potential relationships based on:
    - Name similarity
    - Type compatibility
    - Value overlap
    - Cardinality patterns
    
    The job runs asynchronously. Poll /dictionary/relationships/discover/{job_id}
    for status updates.
    
    **Note**: This is a simplified synchronous implementation. In production,
    this should be delegated to a background worker.
    """
    job_id = f"reldisco_{uuid.uuid4().hex[:12]}"
    
    # Create job record
    stmt = insert(dictionary_relationship_discovery_jobs).values(
        id=job_id,
        connection_id=job_create.connection_id,
        scope_database=job_create.scope_database,
        scope_schema=job_create.scope_schema,
        scope_tables=job_create.scope_tables,
        status=DiscoveryJobStatus.pending.value,
        progress=0,
        config=job_create.config.model_dump(),
        started_by=job_create.started_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    conn.execute(stmt)
    conn.commit()
    
    # In a real implementation, this would trigger a background job
    # For now, we'll return the pending job
    
    return get_discovery_job(job_id, conn)


@router.get("/discover/{job_id}", response_model=DiscoveryJob)
def get_discovery_job(
    job_id: str,
    conn: Connection = Depends(get_db_connection)
):
    """
    Get the status and results of a discovery job.
    
    Returns:
    - Job status (pending, running, completed, failed)
    - Progress percentage
    - Results summary (when completed)
    - Error message (if failed)
    """
    stmt = select(dictionary_relationship_discovery_jobs).where(
        dictionary_relationship_discovery_jobs.c.id == job_id
    )
    result = conn.execute(stmt).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Discovery job not found")
    
    return DiscoveryJob(**dict(result._mapping))


@router.post("/discover/{job_id}/run", response_model=DiscoveryJob)
def run_discovery_job(
    job_id: str,
    conn: Connection = Depends(get_db_connection)
):
    """
    Execute a discovery job synchronously (for testing/demo purposes).
    
    **Warning**: This runs synchronously and may take a long time for large schemas.
    In production, use background workers.
    """
    # Get job
    job = get_discovery_job(job_id, conn)
    
    if job.status != DiscoveryJobStatus.pending:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not pending (status: {job.status})"
        )
    
    # Update to running
    update_stmt = update(dictionary_relationship_discovery_jobs).where(
        dictionary_relationship_discovery_jobs.c.id == job_id
    ).values(
        status=DiscoveryJobStatus.running.value,
        started_at=datetime.utcnow(),
        progress=0,
        updated_at=datetime.utcnow()
    )
    conn.execute(update_stmt)
    conn.commit()
    
    try:
        # Parse config
        config = DiscoveryConfig(**job.config)
        
        # Run discovery (only FK-like for now)
        if config.discover_foreign_key_like:
            relationships = RelationshipDiscoveryService.discover_foreign_key_relationships(
                conn,
                job.scope_database or "default",
                job.scope_schema or "public",
                config
            )
            
            # Insert discovered relationships
            for rel in relationships:
                try:
                    RelationshipCRUDService.create_relationship(conn, rel)
                except Exception as e:
                    print(f"Error creating relationship: {e}")
                    continue
            
            # Update job status
            summary = DiscoveryJobSummary(
                tables_scanned=len(set(r.from_table for r in relationships) | set(r.to_table for r in relationships)),
                columns_analyzed=len(relationships) * 2,
                relationships_found=len(relationships),
                relationships_by_type={
                    "foreign_key_like": sum(1 for r in relationships if r.relationship_type == RelationshipType.foreign_key_like)
                },
                avg_confidence=sum(r.confidence for r in relationships) / len(relationships) if relationships else 0.0,
                duration_seconds=0.0
            )
            
            update_stmt = update(dictionary_relationship_discovery_jobs).where(
                dictionary_relationship_discovery_jobs.c.id == job_id
            ).values(
                status=DiscoveryJobStatus.completed.value,
                progress=100,
                results_summary=summary.model_dump(),
                completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            conn.execute(update_stmt)
            conn.commit()
        
        return get_discovery_job(job_id, conn)
        
    except Exception as e:
        # Mark job as failed
        update_stmt = update(dictionary_relationship_discovery_jobs).where(
            dictionary_relationship_discovery_jobs.c.id == job_id
        ).values(
            status=DiscoveryJobStatus.failed.value,
            error_message=str(e),
            completed_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        conn.execute(update_stmt)
        conn.commit()
        
        raise HTTPException(status_code=500, detail=f"Discovery job failed: {e}")


@router.get("/discover", response_model=List[DiscoveryJob])
def list_discovery_jobs(
    connection_id: Optional[str] = None,
    status: Optional[DiscoveryJobStatus] = None,
    limit: int = 20,
    conn: Connection = Depends(get_db_connection)
):
    """
    List discovery jobs.
    
    - **connection_id**: Filter by connection
    - **status**: Filter by job status
    - **limit**: Max number of jobs to return (default 20)
    """
    stmt = select(dictionary_relationship_discovery_jobs)
    
    filters = []
    if connection_id:
        filters.append(dictionary_relationship_discovery_jobs.c.connection_id == connection_id)
    if status:
        filters.append(dictionary_relationship_discovery_jobs.c.status == status.value)
    
    if filters:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*filters))
    
    stmt = stmt.order_by(dictionary_relationship_discovery_jobs.c.created_at.desc()).limit(limit)
    
    results = conn.execute(stmt).fetchall()
    
    return [DiscoveryJob(**dict(row._mapping)) for row in results]


