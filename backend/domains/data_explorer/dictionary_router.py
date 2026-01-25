"""FastAPI router for Data Dictionary endpoints."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from db_session import get_session
from .db_models import DataDictionaryEntry
from .dictionary_service import (
    get_dictionary_for_tables, 
    format_dictionary_as_context, 
    get_column_versions, 
    activate_version,
    submit_for_approval,
    approve_entry,
    reject_entry,
    publish_draft_directly
)

router = APIRouter(prefix="/data-dictionary", tags=["Data Dictionary"])


# Response Models
class DictionaryEntryResponse(BaseModel):
    """Response model for a dictionary entry."""
    id: int
    database_name: str
    schema_name: str
    table_name: str
    column_name: str
    version_number: int
    is_active: bool
    state: str  # "draft", "pending_approval", "published"
    version_notes: Optional[str] = None
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    technical_description: Optional[str] = None
    data_type: Optional[str] = None
    examples: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    source: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class DictionaryEntryUpdate(BaseModel):
    """Update model for a dictionary entry."""
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    technical_description: Optional[str] = None
    tags: Optional[List[str]] = None
    create_new_version: bool = False
    version_notes: Optional[str] = None


@router.get("/", response_model=List[DictionaryEntryResponse])
def list_dictionary_entries(
    database_name: Optional[str] = Query(None),
    schema_name: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
    active_only: bool = Query(True, description="Only return working versions (draft if exists, otherwise published)"),
    session: Session = Depends(get_session)
):
    """
    List dictionary entries with optional filtering.
    
    Query params:
    - database_name: Filter by database
    - schema_name: Filter by schema
    - table_name: Filter by table
    - active_only: Return working versions - draft if exists, otherwise active/published (default: true)
    """
    statement = select(DataDictionaryEntry)
    
    if database_name:
        statement = statement.where(DataDictionaryEntry.database_name == database_name)
    if schema_name:
        statement = statement.where(DataDictionaryEntry.schema_name == schema_name)
    if table_name:
        statement = statement.where(DataDictionaryEntry.table_name == table_name)
    
    # If active_only, we want the "working version" for each column:
    # - Draft version if one exists (for editing)
    # - Otherwise, the published/active version
    if active_only:
        statement = statement.where(
            (DataDictionaryEntry.state == "draft") |  # Include drafts
            (DataDictionaryEntry.is_active == True)    # Include active/published versions
        )
    
    statement = statement.order_by(
        DataDictionaryEntry.schema_name,
        DataDictionaryEntry.table_name,
        DataDictionaryEntry.column_name,
        DataDictionaryEntry.version_number.desc()
    )
    
    all_entries = session.exec(statement).all()
    
    # Filter to get only one version per column (draft if exists, otherwise active)
    if active_only:
        seen_columns = set()
        entries = []
        for entry in all_entries:
            column_key = (entry.database_name, entry.schema_name, entry.table_name, entry.column_name)
            if column_key not in seen_columns:
                seen_columns.add(column_key)
                entries.append(entry)
    else:
        entries = all_entries
    
    return [
        DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
        for entry in entries
    ]


@router.get("/tables/{database_name}/{schema_name}/{table_name}", response_model=List[DictionaryEntryResponse])
def get_table_dictionary(
    database_name: str,
    schema_name: str,
    table_name: str,
    session: Session = Depends(get_session)
):
    """Get all dictionary entries for a specific table (active versions only)."""
    entries = get_dictionary_for_tables(
        session=session,
        database_name=database_name,
        schema_name=schema_name,
        table_names=[table_name],
        active_only=True
    )
    
    return [
        DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
        for entry in entries
    ]


@router.get("/{entry_id}", response_model=DictionaryEntryResponse)
def get_dictionary_entry(
    entry_id: int,
    session: Session = Depends(get_session)
):
    """Get a single dictionary entry by ID."""
    entry = session.get(DataDictionaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dictionary entry not found")
    
    return DictionaryEntryResponse(
        id=entry.id,
        database_name=entry.database_name,
        schema_name=entry.schema_name,
        table_name=entry.table_name,
        column_name=entry.column_name,
        version_number=entry.version_number,
        is_active=entry.is_active,
        version_notes=entry.version_notes,
        state=entry.state,
        business_name=entry.business_name,
        business_description=entry.business_description,
        technical_description=entry.technical_description,
        data_type=entry.data_type,
        examples=entry.examples or [],
        tags=entry.tags or [],
        source=entry.source,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat(),
    )


@router.patch("/{entry_id}", response_model=DictionaryEntryResponse)
def update_dictionary_entry(
    entry_id: int,
    update: DictionaryEntryUpdate,
    session: Session = Depends(get_session)
):
    """
    Update a dictionary entry.
    
    Allows editing business_name, business_description, technical_description, and tags.
    If create_new_version=True, deactivates current version and creates a new one.
    Otherwise, updates the entry in place.
    Marks source as 'human_edited' after first human edit.
    """
    entry = session.get(DataDictionaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dictionary entry not found")
    
    if update.create_new_version:
        # When creating a new version from a published entry, check if there's already a draft
        # If there is, update it instead of creating a duplicate
        from sqlmodel import select
        
        existing_draft = session.exec(
            select(DataDictionaryEntry).where(
                DataDictionaryEntry.database_name == entry.database_name,
                DataDictionaryEntry.schema_name == entry.schema_name,
                DataDictionaryEntry.table_name == entry.table_name,
                DataDictionaryEntry.column_name == entry.column_name,
                DataDictionaryEntry.state == "draft"
            )
        ).first()
        
        if existing_draft:
            # Update the existing draft instead of creating a new one
            if update.business_name is not None:
                existing_draft.business_name = update.business_name
            if update.business_description is not None:
                existing_draft.business_description = update.business_description
            if update.technical_description is not None:
                existing_draft.technical_description = update.technical_description
            if update.tags is not None:
                existing_draft.tags = update.tags
            
            existing_draft.source = "human_edited"
            existing_draft.updated_at = datetime.utcnow()
            if update.version_notes:
                existing_draft.version_notes = update.version_notes
            
            session.add(existing_draft)
            session.commit()
            session.refresh(existing_draft)
            entry = existing_draft
        else:
            # No existing draft - create a new draft version
            # IMPORTANT: Do NOT deactivate the published entry - it stays active until the draft is published
            
            # Find the highest version number for this column to avoid duplicates
            from sqlmodel import func
            max_version = session.exec(
                select(func.max(DataDictionaryEntry.version_number)).where(
                    DataDictionaryEntry.database_name == entry.database_name,
                    DataDictionaryEntry.schema_name == entry.schema_name,
                    DataDictionaryEntry.table_name == entry.table_name,
                    DataDictionaryEntry.column_name == entry.column_name
                )
            ).first()
            
            new_version_number = (max_version or 0) + 1
            
            # Create new draft version (NOT active - only published versions are active)
            new_entry = DataDictionaryEntry(
                database_name=entry.database_name,
                schema_name=entry.schema_name,
                table_name=entry.table_name,
                column_name=entry.column_name,
                version_number=new_version_number,
                is_active=False,  # Drafts are NOT active - only published versions are active
                state="draft",
                version_notes=update.version_notes or "Edited published entry - new draft created",
                business_name=update.business_name if update.business_name is not None else entry.business_name,
                business_description=update.business_description if update.business_description is not None else entry.business_description,
                technical_description=update.technical_description if update.technical_description is not None else entry.technical_description,
                data_type=entry.data_type,
                examples=entry.examples,
                tags=update.tags if update.tags is not None else entry.tags,
                source="human_edited"
            )
            session.add(new_entry)
            session.commit()
            session.refresh(new_entry)
            entry = new_entry
    else:
        # Update in place
        if update.business_name is not None:
            entry.business_name = update.business_name
        if update.business_description is not None:
            entry.business_description = update.business_description
        if update.technical_description is not None:
            entry.technical_description = update.technical_description
        if update.tags is not None:
            entry.tags = update.tags
        
        # Mark as human-edited
        if entry.source.startswith("llm"):
            entry.source = "human_edited"
        
        entry.updated_at = datetime.utcnow()
        
        session.add(entry)
        session.commit()
        session.refresh(entry)
    
    return DictionaryEntryResponse(
        id=entry.id,
        database_name=entry.database_name,
        schema_name=entry.schema_name,
        table_name=entry.table_name,
        column_name=entry.column_name,
        version_number=entry.version_number,
        is_active=entry.is_active,
        version_notes=entry.version_notes,
        state=entry.state,
        business_name=entry.business_name,
        business_description=entry.business_description,
        technical_description=entry.technical_description,
        data_type=entry.data_type,
        examples=entry.examples or [],
        tags=entry.tags or [],
        source=entry.source,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat(),
    )


@router.get("/context/{database_name}/{schema_name}", response_model=dict)
def get_dictionary_context(
    database_name: str,
    schema_name: str,
    table_names: str = Query(..., description="Comma-separated list of table names"),
    session: Session = Depends(get_session)
):
    """
    Get formatted dictionary context for inclusion in LLM prompts.
    
    Returns:
        {"context": "formatted markdown string"}
    """
    table_list = [t.strip() for t in table_names.split(",") if t.strip()]
    
    entries = get_dictionary_for_tables(
        session=session,
        database_name=database_name,
        schema_name=schema_name,
        table_names=table_list
    )
    
    context = format_dictionary_as_context(entries)
    
    return {"context": context, "entry_count": len(entries)}


@router.get("/versions/{database_name}/{schema_name}/{table_name}/{column_name}", response_model=List[DictionaryEntryResponse])
def get_column_version_history(
    database_name: str,
    schema_name: str,
    table_name: str,
    column_name: str,
    session: Session = Depends(get_session)
):
    """
    Get all versions of a specific column's documentation.
    Returns versions ordered by version_number descending (newest first).
    """
    versions = get_column_versions(
        session=session,
        database_name=database_name,
        schema_name=schema_name,
        table_name=table_name,
        column_name=column_name
    )
    
    if not versions:
        raise HTTPException(status_code=404, detail="No versions found for this column")
    
    return [
        DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
        for entry in versions
    ]


@router.post("/activate/{entry_id}", response_model=DictionaryEntryResponse)
def activate_dictionary_version(
    entry_id: int,
    session: Session = Depends(get_session)
):
    """
    Activate a specific version of a dictionary entry.
    Deactivates all other versions of the same column.
    """
    try:
        entry = activate_version(session=session, entry_id=entry_id)
        
        return DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Approval Workflow Endpoints
# ============================================================================

class WorkflowActionRequest(BaseModel):
    """Request model for workflow actions."""
    notes: Optional[str] = None


@router.post("/{entry_id}/submit-for-approval", response_model=DictionaryEntryResponse)
def submit_entry_for_approval(
    entry_id: int,
    session: Session = Depends(get_session)
):
    """
    Submit a draft entry for approval.
    Changes state from 'draft' to 'pending_approval'.
    """
    try:
        entry = submit_for_approval(session, entry_id)
        return DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/approve", response_model=DictionaryEntryResponse)
def approve_dictionary_entry(
    entry_id: int,
    request: WorkflowActionRequest,
    session: Session = Depends(get_session)
):
    """
    Approve a pending entry and publish it.
    Changes state from 'pending_approval' to 'published'.
    """
    try:
        entry = approve_entry(session, entry_id, request.notes)
        return DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/reject", response_model=DictionaryEntryResponse)
def reject_dictionary_entry(
    entry_id: int,
    request: WorkflowActionRequest,
    session: Session = Depends(get_session)
):
    """
    Reject a pending entry and return it to draft state.
    Changes state from 'pending_approval' back to 'draft'.
    """
    try:
        entry = reject_entry(session, entry_id, request.notes)
        return DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/publish", response_model=DictionaryEntryResponse)
def publish_entry_directly(
    entry_id: int,
    request: WorkflowActionRequest,
    session: Session = Depends(get_session)
):
    """
    Publish a draft entry directly without approval workflow.
    Useful for auto-approved changes or admin overrides.
    """
    try:
        entry = publish_draft_directly(session, entry_id, request.notes)
        return DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            state=entry.state,
            version_notes=entry.version_notes,
            business_name=entry.business_name,
            business_description=entry.business_description,
            technical_description=entry.technical_description,
            data_type=entry.data_type,
            examples=[str(e) for e in (entry.examples or [])],
            tags=entry.tags or [],
            source=entry.source,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Data Sources Endpoints
# ============================================================================

class DataSourceSummary(BaseModel):
    """Summary of a data source (database)."""
    source_name: str
    table_count: int
    column_count: int
    documented_columns: int
    documentation_percentage: float
    schemas: List[str]
    sample_tables: List[str]
    last_updated: Optional[str] = None
    description: Optional[str] = None


@router.get("/sources", response_model=List[DataSourceSummary])
def list_data_sources(
    database_name: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """
    List all data sources (databases) with summary statistics.

    Returns aggregated information about each database including:
    - Number of tables and columns
    - Documentation coverage percentage
    - List of schemas
    - Sample table names
    """
    from sqlmodel import func, distinct

    # Build query to aggregate by database_name
    if database_name:
        statement = select(DataDictionaryEntry).where(
            DataDictionaryEntry.database_name == database_name,
            DataDictionaryEntry.is_active == True
        )
    else:
        statement = select(DataDictionaryEntry).where(
            DataDictionaryEntry.is_active == True
        )

    entries = session.exec(statement).all()

    # Aggregate by database
    databases = {}
    for entry in entries:
        db_name = entry.database_name
        if db_name not in databases:
            databases[db_name] = {
                'tables': set(),
                'columns': 0,
                'documented': 0,
                'schemas': set(),
                'last_updated': None,
            }

        databases[db_name]['tables'].add(f"{entry.schema_name}.{entry.table_name}")
        databases[db_name]['columns'] += 1
        databases[db_name]['schemas'].add(entry.schema_name)

        # Count as documented if has business_name or business_description
        if entry.business_name or entry.business_description:
            databases[db_name]['documented'] += 1

        # Track last updated
        if databases[db_name]['last_updated'] is None or entry.updated_at > databases[db_name]['last_updated']:
            databases[db_name]['last_updated'] = entry.updated_at

    # Convert to response format
    result = []
    for db_name, stats in databases.items():
        table_list = list(stats['tables'])
        result.append(DataSourceSummary(
            source_name=db_name,
            table_count=len(stats['tables']),
            column_count=stats['columns'],
            documented_columns=stats['documented'],
            documentation_percentage=round(stats['documented'] / stats['columns'] * 100, 1) if stats['columns'] > 0 else 0,
            schemas=sorted(list(stats['schemas'])),
            sample_tables=sorted(table_list)[:5],  # First 5 tables as sample
            last_updated=stats['last_updated'].isoformat() if stats['last_updated'] else None,
        ))

    return result


@router.post("/sources/{source_name}/quick-analysis")
def quick_analyze_source(
    source_name: str,
    database_name: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Perform quick analysis on a data source schema.
    Returns a text description of the source.
    """
    # Get entries for the source
    statement = select(DataDictionaryEntry).where(
        DataDictionaryEntry.database_name == (database_name or source_name),
        DataDictionaryEntry.is_active == True
    )
    entries = session.exec(statement).all()

    if not entries:
        return {
            "source_name": source_name,
            "description": f"No documented tables found for source '{source_name}'.",
            "table_count": 0
        }

    # Build simple description
    tables = set()
    schemas = set()
    for entry in entries:
        tables.add(f"{entry.schema_name}.{entry.table_name}")
        schemas.add(entry.schema_name)

    description = f"Database '{source_name}' contains {len(tables)} tables across {len(schemas)} schema(s): {', '.join(sorted(schemas))}."

    return {
        "source_name": source_name,
        "description": description,
        "table_count": len(tables),
        "schema_count": len(schemas)
    }

