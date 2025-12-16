"""FastAPI router for enhanced data dictionary operations."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from pydantic import BaseModel
from sqlmodel import Session

from db_session import get_session
from .dictionary_enhanced_models import (
    DictionaryAsset,
    DictionaryField,
    DictionaryRelationship,
    DictionaryProfile,
    TrustTier,
    EntityRole,
    Cardinality,
    RelationshipConfidence
)
from . import dictionary_enhanced_service as service
from .connection import get_db_connection

router = APIRouter(prefix="/data-dictionary/enhanced", tags=["Enhanced Data Dictionary"])


# ==================== Request/Response Models ====================

class SyncRequest(BaseModel):
    """Request to sync assets from information_schema."""
    connection_id: str = "default"
    schema: Optional[str] = None


class SyncResponse(BaseModel):
    """Response from sync operation."""
    tables_synced: int
    columns_synced: int


class AssetResponse(BaseModel):
    """Response model for a dictionary asset."""
    id: UUID
    connection_id: str
    schema_name: str
    table_name: str
    asset_type: str
    business_name: Optional[str]
    business_definition: Optional[str]
    business_domain: Optional[str]
    grain: Optional[str]
    row_meaning: Optional[str]
    owner: Optional[str]
    steward: Optional[str]
    tags: Optional[List[str]]
    trust_tier: str
    trust_score: int
    approved_for_reporting: bool
    approved_for_ml: bool
    known_issues: Optional[str]
    issue_tags: Optional[List[str]]
    query_count_30d: int
    last_queried_at: Optional[datetime]
    row_count_estimate: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """Paginated list of assets."""
    results: List[AssetResponse]
    total: int
    limit: int
    offset: int


class AssetUpdateRequest(BaseModel):
    """Request to update asset metadata."""
    business_name: Optional[str] = None
    business_definition: Optional[str] = None
    business_domain: Optional[str] = None
    grain: Optional[str] = None
    row_meaning: Optional[str] = None
    owner: Optional[str] = None
    steward: Optional[str] = None
    tags: Optional[List[str]] = None
    trust_tier: Optional[str] = None
    trust_score: Optional[int] = None
    approved_for_reporting: Optional[bool] = None
    approved_for_ml: Optional[bool] = None
    known_issues: Optional[str] = None
    issue_tags: Optional[List[str]] = None


class FieldResponse(BaseModel):
    """Response model for a dictionary field."""
    id: UUID
    asset_id: UUID
    column_name: str
    ordinal_position: Optional[int]
    data_type: Optional[str]
    is_nullable: bool
    default_value: Optional[str]
    business_name: Optional[str]
    business_definition: Optional[str]
    entity_role: str
    tags: Optional[List[str]]
    trust_tier: str
    trust_score: int
    approved_for_reporting: bool
    approved_for_ml: bool
    known_issues: Optional[str]
    issue_tags: Optional[List[str]]
    query_count_30d: int
    last_queried_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FieldUpdateRequest(BaseModel):
    """Request to update field metadata."""
    business_name: Optional[str] = None
    business_definition: Optional[str] = None
    entity_role: Optional[str] = None
    tags: Optional[List[str]] = None
    trust_tier: Optional[str] = None
    trust_score: Optional[int] = None
    approved_for_reporting: Optional[bool] = None
    approved_for_ml: Optional[bool] = None
    known_issues: Optional[str] = None
    issue_tags: Optional[List[str]] = None


class RelationshipResponse(BaseModel):
    """Response model for a relationship."""
    id: UUID
    connection_id: str
    source_schema: str
    source_table: str
    source_column: str
    target_schema: str
    target_table: str
    target_column: str
    cardinality: str
    confidence: str
    notes: Optional[str]
    join_count_30d: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RelationshipCreateRequest(BaseModel):
    """Request to create a relationship."""
    connection_id: str = "default"
    source_schema: str
    source_table: str
    source_column: str
    target_schema: str
    target_table: str
    target_column: str
    cardinality: str = "unknown"
    confidence: str = "assumed"
    notes: Optional[str] = None


class ProfileResponse(BaseModel):
    """Response model for a profile."""
    id: UUID
    connection_id: str
    schema_name: str
    table_name: str
    column_name: str
    row_count_estimate: Optional[int]
    null_count: Optional[int]
    null_fraction: Optional[float]
    distinct_count: Optional[int]
    distinct_count_estimate: Optional[int]
    uniqueness_fraction: Optional[float]
    numeric_min: Optional[float]
    numeric_max: Optional[float]
    numeric_avg: Optional[float]
    numeric_stddev: Optional[float]
    numeric_median: Optional[float]
    top_values: Optional[List[Dict[str, Any]]]
    min_length: Optional[int]
    max_length: Optional[int]
    avg_length: Optional[float]
    earliest_value: Optional[datetime]
    latest_value: Optional[datetime]
    sample_size: Optional[int]
    sample_method: Optional[str]
    profile_version: int
    computed_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Endpoints ====================

@router.post("/sync", response_model=SyncResponse)
def sync_assets(
    request: SyncRequest,
    session: Session = Depends(get_session)
):
    """
    Sync table/column structure from information_schema into dictionary.
    Only updates structural fields, preserves user-authored business metadata.
    """
    try:
        # Get database connection
        db_conn = get_db_connection(request.connection_id)
        
        # Run sync
        stats = service.sync_assets_from_information_schema(
            session=session,
            connection_id=request.connection_id,
            db_connection=db_conn,
            schema_filter=request.schema
        )
        
        return SyncResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/assets", response_model=AssetListResponse)
def list_assets(
    connection_id: str = QueryParam("default"),
    schema: Optional[str] = QueryParam(None),
    search: Optional[str] = QueryParam(None),
    trust_tier: Optional[str] = QueryParam(None),
    business_domain: Optional[str] = QueryParam(None),
    limit: int = QueryParam(100, le=500),
    offset: int = QueryParam(0, ge=0),
    session: Session = Depends(get_session)
):
    """
    List/search dictionary assets with filters and pagination.
    """
    results, total = service.search_assets(
        session=session,
        connection_id=connection_id,
        schema_name=schema,
        search_term=search,
        trust_tier=trust_tier,
        business_domain=business_domain,
        limit=limit,
        offset=offset
    )
    
    return AssetListResponse(
        results=[AssetResponse.from_orm(r) for r in results],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: UUID,
    session: Session = Depends(get_session)
):
    """Get a single asset by ID."""
    asset = session.get(DictionaryAsset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse.from_orm(asset)


@router.patch("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: UUID,
    request: AssetUpdateRequest,
    session: Session = Depends(get_session)
):
    """Update business metadata for an asset."""
    try:
        updates = request.dict(exclude_unset=True)
        asset = service.update_asset_metadata(session, asset_id, updates)
        return AssetResponse.from_orm(asset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/assets/{asset_id}/fields", response_model=List[FieldResponse])
def get_asset_fields(
    asset_id: UUID,
    session: Session = Depends(get_session)
):
    """Get all fields for an asset."""
    fields = service.get_fields_for_asset(session, asset_id)
    return [FieldResponse.from_orm(f) for f in fields]


@router.patch("/fields/{field_id}", response_model=FieldResponse)
def update_field(
    field_id: UUID,
    request: FieldUpdateRequest,
    session: Session = Depends(get_session)
):
    """Update business metadata for a field."""
    try:
        updates = request.dict(exclude_unset=True)
        field = service.update_field_metadata(session, field_id, updates)
        return FieldResponse.from_orm(field)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/relationships", response_model=List[RelationshipResponse])
def list_relationships(
    connection_id: str = QueryParam("default"),
    schema: Optional[str] = QueryParam(None),
    table: Optional[str] = QueryParam(None),
    session: Session = Depends(get_session)
):
    """List relationships, optionally filtered by table."""
    if schema and table:
        rels = service.get_relationships_for_table(session, connection_id, schema, table)
    else:
        # Get all relationships for connection
        from sqlmodel import select
        rels = list(session.exec(
            select(DictionaryRelationship).where(
                DictionaryRelationship.connection_id == connection_id
            )
        ).all())
    
    return [RelationshipResponse.from_orm(r) for r in rels]


@router.post("/relationships", response_model=RelationshipResponse)
def create_relationship(
    request: RelationshipCreateRequest,
    session: Session = Depends(get_session)
):
    """Create a new relationship."""
    try:
        rel = service.create_relationship(
            session=session,
            connection_id=request.connection_id,
            source_schema=request.source_schema,
            source_table=request.source_table,
            source_column=request.source_column,
            target_schema=request.target_schema,
            target_table=request.target_table,
            target_column=request.target_column,
            cardinality=request.cardinality,
            confidence=request.confidence,
            notes=request.notes
        )
        return RelationshipResponse.from_orm(rel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create failed: {str(e)}")


@router.delete("/relationships/{relationship_id}")
def delete_relationship(
    relationship_id: UUID,
    session: Session = Depends(get_session)
):
    """Delete a relationship."""
    rel = session.get(DictionaryRelationship, relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    session.delete(rel)
    session.commit()
    
    return {"status": "deleted"}


@router.get("/profiles", response_model=List[ProfileResponse])
def get_profiles(
    connection_id: str = QueryParam("default"),
    schema: str = QueryParam(...),
    table: str = QueryParam(...),
    latest: bool = QueryParam(True),
    session: Session = Depends(get_session)
):
    """Get profiles for a table's columns."""
    profiles = service.get_profiles_for_table(
        session=session,
        connection_id=connection_id,
        schema_name=schema,
        table_name=table,
        latest_only=latest
    )
    
    return [ProfileResponse.from_orm(p) for p in profiles]


@router.get("/context/{connection_id}/{schema}/{table}")
def get_dictionary_context(
    connection_id: str,
    schema: str,
    table: str,
    session: Session = Depends(get_session)
):
    """
    Get comprehensive dictionary context for a table.
    Suitable for LLM grounding and chat integration.
    """
    context = service.get_dictionary_context(
        session=session,
        connection_id=connection_id,
        schema_name=schema,
        table_name=table
    )
    
    if "error" in context:
        raise HTTPException(status_code=404, detail=context["error"])
    
    return context


