"""FastAPI router for Data Dictionary endpoints."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from db_session import get_session
from .db_models import DataDictionaryEntry
from .dictionary_service import get_dictionary_for_tables, format_dictionary_as_context, get_column_versions, activate_version

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


@router.get("/", response_model=List[DictionaryEntryResponse])
def list_dictionary_entries(
    database_name: Optional[str] = Query(None),
    schema_name: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
    active_only: bool = Query(True, description="Only return active versions"),
    session: Session = Depends(get_session)
):
    """
    List dictionary entries with optional filtering.
    
    Query params:
    - database_name: Filter by database
    - schema_name: Filter by schema
    - table_name: Filter by table
    - active_only: Only return active versions (default: true)
    """
    statement = select(DataDictionaryEntry)
    
    if database_name:
        statement = statement.where(DataDictionaryEntry.database_name == database_name)
    if schema_name:
        statement = statement.where(DataDictionaryEntry.schema_name == schema_name)
    if table_name:
        statement = statement.where(DataDictionaryEntry.table_name == table_name)
    if active_only:
        statement = statement.where(DataDictionaryEntry.is_active == True)
    
    statement = statement.order_by(
        DataDictionaryEntry.schema_name,
        DataDictionaryEntry.table_name,
        DataDictionaryEntry.column_name,
        DataDictionaryEntry.version_number.desc()
    )
    
    entries = session.exec(statement).all()
    
    return [
        DictionaryEntryResponse(
            id=entry.id,
            database_name=entry.database_name,
            schema_name=entry.schema_name,
            table_name=entry.table_name,
            column_name=entry.column_name,
            version_number=entry.version_number,
            is_active=entry.is_active,
            version_notes=entry.version_notes,
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
            version_notes=entry.version_notes,
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
    Marks source as 'human_edited' after first human edit.
    """
    entry = session.get(DataDictionaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dictionary entry not found")
    
    # Update fields
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
            version_notes=entry.version_notes,
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
            version_notes=entry.version_notes,
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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

