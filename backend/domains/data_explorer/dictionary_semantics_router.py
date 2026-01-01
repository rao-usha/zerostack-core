"""API router for dictionary semantics, grains, and relationships."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam, BackgroundTasks
from pydantic import BaseModel, Field
from sqlmodel import Session

from db_session import get_session
from .dictionary_semantics_models import (
    DictionaryEntry,
    DictionaryEntrySemantics,
    DictionaryGrain,
    DictionaryRelationship,
    DictionaryInferenceJob,
    DecisionContext,
    SemanticGuarantees,
    ValidationState,
    GrainCompatibility,
    SemanticDefinition,
)
from . import dictionary_semantics_service as service
from .relationship_inference import run_inference_job

router = APIRouter(prefix="/data-dictionary", tags=["Dictionary Semantics"])


# ==================== Request/Response Models ====================

class SemanticsRequest(BaseModel):
    """Request to update semantics."""
    decision_context: Optional[Dict[str, Any]] = None
    semantic_guarantees: Optional[Dict[str, Any]] = None
    validation_state: Optional[Dict[str, Any]] = None
    create_version: bool = False


class SemanticsResponse(BaseModel):
    """Response with semantics."""
    entry_id: UUID
    decision_context: Dict[str, Any]
    semantic_guarantees: Dict[str, Any]
    validation_state: Dict[str, Any]
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GrainRequest(BaseModel):
    """Request to update grain."""
    entity: str
    primary_key: Optional[List[str]] = None
    time_grain: Optional[str] = None
    natural_key: Optional[List[str]] = None
    notes: Optional[str] = None


class GrainResponse(BaseModel):
    """Response with grain."""
    id: UUID
    entry_id: UUID
    entity: str
    primary_key: Optional[List[str]]
    time_grain: Optional[str]
    natural_key: Optional[List[str]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RelationshipCreateRequest(BaseModel):
    """Request to create a relationship."""
    relationship_kind: str  # candidate, semantic
    left_entry_id: UUID
    right_entry_id: UUID
    relationship_type: str
    status: str = "suggested"
    cardinality: Optional[str] = None
    left_ref: Optional[Dict[str, Any]] = None
    right_ref: Optional[Dict[str, Any]] = None
    match_rate_sample: Optional[float] = None
    left_null_rate: Optional[float] = None
    right_unique: Optional[bool] = None
    suggested_join_sql: Optional[str] = None
    grain_compatibility: Optional[Dict[str, Any]] = None
    semantic_definition: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    created_by: Optional[str] = None


class RelationshipUpdateRequest(BaseModel):
    """Request to update a relationship."""
    cardinality: Optional[str] = None
    grain_compatibility: Optional[Dict[str, Any]] = None
    semantic_definition: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    suggested_join_sql: Optional[str] = None
    relationship_type: Optional[str] = None


class RelationshipStatusRequest(BaseModel):
    """Request to update relationship status."""
    status: str  # suggested, approved, rejected, deprecated


class RelationshipResponse(BaseModel):
    """Response with relationship."""
    id: UUID
    relationship_kind: str
    status: str
    left_entry_id: UUID
    right_entry_id: UUID
    left_ref: Optional[Dict[str, Any]]
    right_ref: Optional[Dict[str, Any]]
    relationship_type: str
    cardinality: Optional[str]
    match_rate_sample: Optional[float]
    left_null_rate: Optional[float]
    right_unique: Optional[bool]
    suggested_join_sql: Optional[str]
    grain_compatibility: Dict[str, Any]
    semantic_definition: Dict[str, Any]
    confidence_score: Optional[float]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RelationshipListResponse(BaseModel):
    """Paginated list of relationships."""
    results: List[RelationshipResponse]
    total: int
    limit: int
    offset: int


class InferenceJobRequest(BaseModel):
    """Request to start inference job."""
    connection_id: str = "default"
    schema: Optional[str] = None
    include_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None
    max_samples: int = 1000


class InferenceJobResponse(BaseModel):
    """Response with inference job."""
    id: UUID
    connection_id: str
    schema_name: Optional[str]
    status: str
    progress: int
    current_stage: Optional[str]
    relationships_found: int
    tables_scanned: int
    error_message: Optional[str]
    result_summary: Optional[Dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ContextBlobResponse(BaseModel):
    """Response with full context blob."""
    entry: Dict[str, Any]
    decision_context: Optional[Dict[str, Any]] = None
    semantic_guarantees: Optional[Dict[str, Any]] = None
    validation_state: Optional[Dict[str, Any]] = None
    grain: Optional[Dict[str, Any]] = None
    relationships: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== Semantics Endpoints ====================

@router.get("/entries/{entry_id}/semantics", response_model=SemanticsResponse)
def get_semantics(
    entry_id: UUID,
    session: Session = Depends(get_session)
):
    """Get semantics for an entry."""
    semantics = service.get_semantics(session, entry_id)
    if not semantics:
        # Return empty semantics
        return SemanticsResponse(
            entry_id=entry_id,
            decision_context={},
            semantic_guarantees={},
            validation_state={},
            updated_at=datetime.utcnow()
        )
    
    return SemanticsResponse.from_orm(semantics)


@router.put("/entries/{entry_id}/semantics", response_model=SemanticsResponse)
def update_semantics(
    entry_id: UUID,
    request: SemanticsRequest,
    session: Session = Depends(get_session)
):
    """Update semantics for an entry."""
    # Validate entry exists
    entry = session.get(DictionaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    try:
        semantics = service.upsert_semantics(
            session,
            entry_id,
            decision_context=request.decision_context,
            semantic_guarantees=request.semantic_guarantees,
            validation_state=request.validation_state,
            create_version=request.create_version
        )
        return SemanticsResponse.from_orm(semantics)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Grain Endpoints ====================

@router.get("/entries/{entry_id}/grain", response_model=Optional[GrainResponse])
def get_grain(
    entry_id: UUID,
    session: Session = Depends(get_session)
):
    """Get grain for an entry."""
    grain = service.get_grain(session, entry_id)
    if not grain:
        return None
    return GrainResponse.from_orm(grain)


@router.put("/entries/{entry_id}/grain", response_model=GrainResponse)
def update_grain(
    entry_id: UUID,
    request: GrainRequest,
    session: Session = Depends(get_session)
):
    """Update grain for an entry."""
    # Validate entry exists
    entry = session.get(DictionaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    grain = service.upsert_grain(
        session,
        entry_id,
        entity=request.entity,
        primary_key=request.primary_key,
        time_grain=request.time_grain,
        natural_key=request.natural_key,
        notes=request.notes
    )
    
    return GrainResponse.from_orm(grain)


# ==================== Relationship Endpoints ====================

@router.get("/relationships", response_model=RelationshipListResponse)
def list_relationships(
    entry_id: Optional[UUID] = QueryParam(None),
    database: Optional[str] = QueryParam(None),
    schema: Optional[str] = QueryParam(None),
    table: Optional[str] = QueryParam(None),
    status: Optional[str] = QueryParam(None),
    relationship_kind: Optional[str] = QueryParam(None),
    limit: int = QueryParam(100, le=500),
    offset: int = QueryParam(0, ge=0),
    session: Session = Depends(get_session)
):
    """List relationships with filters."""
    results, total = service.list_relationships(
        session,
        entry_id=entry_id,
        database_name=database,
        schema_name=schema,
        table_name=table,
        status=status,
        relationship_kind=relationship_kind,
        limit=limit,
        offset=offset
    )
    
    return RelationshipListResponse(
        results=[RelationshipResponse.from_orm(r) for r in results],
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/relationships", response_model=RelationshipResponse)
def create_relationship(
    request: RelationshipCreateRequest,
    session: Session = Depends(get_session)
):
    """Create a new relationship."""
    # Validate entries exist
    left_entry = session.get(DictionaryEntry, request.left_entry_id)
    right_entry = session.get(DictionaryEntry, request.right_entry_id)
    
    if not left_entry or not right_entry:
        raise HTTPException(status_code=404, detail="One or both entries not found")
    
    rel = service.create_relationship(
        session,
        relationship_kind=request.relationship_kind,
        left_entry_id=request.left_entry_id,
        right_entry_id=request.right_entry_id,
        relationship_type=request.relationship_type,
        status=request.status,
        cardinality=request.cardinality,
        left_ref=request.left_ref,
        right_ref=request.right_ref,
        match_rate_sample=request.match_rate_sample,
        left_null_rate=request.left_null_rate,
        right_unique=request.right_unique,
        suggested_join_sql=request.suggested_join_sql,
        grain_compatibility=request.grain_compatibility,
        semantic_definition=request.semantic_definition,
        confidence_score=request.confidence_score,
        created_by=request.created_by
    )
    
    return RelationshipResponse.from_orm(rel)


@router.patch("/relationships/{relationship_id}", response_model=RelationshipResponse)
def update_relationship(
    relationship_id: UUID,
    request: RelationshipUpdateRequest,
    session: Session = Depends(get_session)
):
    """Update relationship fields."""
    try:
        updates = request.dict(exclude_unset=True)
        rel = service.update_relationship_fields(session, relationship_id, updates)
        return RelationshipResponse.from_orm(rel)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/relationships/{relationship_id}/status", response_model=RelationshipResponse)
def update_relationship_status(
    relationship_id: UUID,
    request: RelationshipStatusRequest,
    session: Session = Depends(get_session)
):
    """Update relationship status."""
    try:
        rel = service.update_relationship_status(session, relationship_id, request.status)
        return RelationshipResponse.from_orm(rel)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/relationships/{relationship_id}")
def delete_relationship(
    relationship_id: UUID,
    force: bool = QueryParam(False),
    session: Session = Depends(get_session)
):
    """Delete a relationship."""
    try:
        hard_deleted = service.delete_relationship(session, relationship_id, force=force)
        return {
            "status": "deleted" if hard_deleted else "deprecated",
            "message": "Relationship deleted" if hard_deleted else "Relationship deprecated"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Inference Endpoints ====================

@router.post("/relationships/infer", response_model=InferenceJobResponse)
def start_inference_job(
    request: InferenceJobRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Start a relationship inference job."""
    # Create job
    job = DictionaryInferenceJob(
        connection_id=request.connection_id,
        schema_name=request.schema,
        include_tables=request.include_tables,
        exclude_tables=request.exclude_tables,
        max_samples=request.max_samples,
        status="pending"
    )
    
    session.add(job)
    session.commit()
    session.refresh(job)
    
    # Run in background
    background_tasks.add_task(
        run_inference_job,
        session,
        job.id,
        request.connection_id,
        request.schema,
        request.include_tables,
        request.exclude_tables,
        request.max_samples
    )
    
    return InferenceJobResponse.from_orm(job)


@router.get("/relationships/infer/{job_id}", response_model=InferenceJobResponse)
def get_inference_job(
    job_id: UUID,
    session: Session = Depends(get_session)
):
    """Get inference job status."""
    job = session.get(DictionaryInferenceJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return InferenceJobResponse.from_orm(job)


# ==================== Context Blob Endpoint ====================

@router.get("/entries/{entry_id}/context-blob", response_model=ContextBlobResponse)
def get_context_blob(
    entry_id: UUID,
    include_relationships: bool = QueryParam(True),
    max_relationships: int = QueryParam(10),
    session: Session = Depends(get_session)
):
    """Get comprehensive context blob for an entry."""
    try:
        context = service.get_entry_context_blob(
            session,
            entry_id,
            include_relationships=include_relationships,
            max_relationships=max_relationships
        )
        return ContextBlobResponse(**context)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

