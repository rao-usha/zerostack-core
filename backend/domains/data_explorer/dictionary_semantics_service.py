"""Service layer for dictionary semantics, grains, and relationships."""
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlmodel import Session, select, or_, and_
from pydantic import ValidationError

from .dictionary_semantics_models import (
    DictionaryEntry,
    DictionaryEntrySemantics,
    DictionaryGrain,
    DictionaryRelationship,
    DictionaryEntryVersion,
    DecisionContext,
    SemanticGuarantees,
    ValidationState,
    GrainCompatibility,
    SemanticDefinition,
    EntryType,
    RelationshipKind,
    RelationshipStatus,
)


# ==================== Entry Management ====================

def get_or_create_entry(
    session: Session,
    entry_type: str,
    title: str,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    table_name: Optional[str] = None,
    column_name: Optional[str] = None,
    concept_name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> DictionaryEntry:
    """Get or create a dictionary entry."""
    # Try to find existing
    query = select(DictionaryEntry).where(
        DictionaryEntry.entry_type == entry_type
    )
    
    if database_name:
        query = query.where(DictionaryEntry.database_name == database_name)
    if schema_name:
        query = query.where(DictionaryEntry.schema_name == schema_name)
    if table_name:
        query = query.where(DictionaryEntry.table_name == table_name)
    if column_name:
        query = query.where(DictionaryEntry.column_name == column_name)
    if concept_name:
        query = query.where(DictionaryEntry.concept_name == concept_name)
    
    existing = session.exec(query).first()
    
    if existing:
        return existing
    
    # Create new
    entry = DictionaryEntry(
        entry_type=entry_type,
        database_name=database_name,
        schema_name=schema_name,
        table_name=table_name,
        column_name=column_name,
        concept_name=concept_name,
        title=title,
        description=description,
        tags=tags or []
    )
    
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    return entry


def find_entry(
    session: Session,
    entry_type: Optional[str] = None,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    table_name: Optional[str] = None,
    column_name: Optional[str] = None,
    concept_name: Optional[str] = None
) -> Optional[DictionaryEntry]:
    """Find a dictionary entry by coordinates."""
    query = select(DictionaryEntry)
    
    if entry_type:
        query = query.where(DictionaryEntry.entry_type == entry_type)
    if database_name:
        query = query.where(DictionaryEntry.database_name == database_name)
    if schema_name:
        query = query.where(DictionaryEntry.schema_name == schema_name)
    if table_name:
        query = query.where(DictionaryEntry.table_name == table_name)
    if column_name:
        query = query.where(DictionaryEntry.column_name == column_name)
    if concept_name:
        query = query.where(DictionaryEntry.concept_name == concept_name)
    
    return session.exec(query).first()


# ==================== Semantics Management ====================

def get_semantics(session: Session, entry_id: UUID) -> Optional[DictionaryEntrySemantics]:
    """Get semantics for an entry."""
    return session.get(DictionaryEntrySemantics, entry_id)


def upsert_semantics(
    session: Session,
    entry_id: UUID,
    decision_context: Optional[Dict[str, Any]] = None,
    semantic_guarantees: Optional[Dict[str, Any]] = None,
    validation_state: Optional[Dict[str, Any]] = None,
    create_version: bool = False
) -> DictionaryEntrySemantics:
    """Upsert semantics for an entry."""
    # Validate blocks
    if decision_context:
        try:
            DecisionContext(**decision_context)
        except ValidationError as e:
            raise ValueError(f"Invalid decision_context: {e}")
    
    if semantic_guarantees:
        try:
            SemanticGuarantees(**semantic_guarantees)
        except ValidationError as e:
            raise ValueError(f"Invalid semantic_guarantees: {e}")
    
    if validation_state:
        try:
            ValidationState(**validation_state)
        except ValidationError as e:
            raise ValueError(f"Invalid validation_state: {e}")
    
    # Get or create semantics
    semantics = session.get(DictionaryEntrySemantics, entry_id)
    
    if semantics:
        # Update existing
        if decision_context is not None:
            semantics.decision_context = decision_context
        if semantic_guarantees is not None:
            semantics.semantic_guarantees = semantic_guarantees
        if validation_state is not None:
            semantics.validation_state = validation_state
        semantics.updated_at = datetime.utcnow()
    else:
        # Create new
        semantics = DictionaryEntrySemantics(
            entry_id=entry_id,
            decision_context=decision_context or {},
            semantic_guarantees=semantic_guarantees or {},
            validation_state=validation_state or {}
        )
        session.add(semantics)
    
    # Update entry timestamp
    entry = session.get(DictionaryEntry, entry_id)
    if entry:
        entry.updated_at = datetime.utcnow()
        session.add(entry)
    
    session.commit()
    session.refresh(semantics)
    
    # Optionally create version snapshot
    if create_version and entry:
        create_entry_version(session, entry)
    
    return semantics


def validate_semantics_blocks(
    decision_context: Optional[Dict[str, Any]] = None,
    semantic_guarantees: Optional[Dict[str, Any]] = None,
    validation_state: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """Validate semantics blocks. Returns (is_valid, errors)."""
    errors = []
    
    if decision_context:
        try:
            DecisionContext(**decision_context)
        except ValidationError as e:
            errors.append(f"decision_context: {str(e)}")
    
    if semantic_guarantees:
        try:
            SemanticGuarantees(**semantic_guarantees)
        except ValidationError as e:
            errors.append(f"semantic_guarantees: {str(e)}")
    
    if validation_state:
        try:
            ValidationState(**validation_state)
        except ValidationError as e:
            errors.append(f"validation_state: {str(e)}")
    
    return len(errors) == 0, errors


# ==================== Grain Management ====================

def get_grain(session: Session, entry_id: UUID) -> Optional[DictionaryGrain]:
    """Get grain for an entry."""
    return session.exec(
        select(DictionaryGrain).where(DictionaryGrain.entry_id == entry_id)
    ).first()


def upsert_grain(
    session: Session,
    entry_id: UUID,
    entity: str,
    primary_key: Optional[List[str]] = None,
    time_grain: Optional[str] = None,
    natural_key: Optional[List[str]] = None,
    notes: Optional[str] = None
) -> DictionaryGrain:
    """Upsert grain for an entry."""
    existing = get_grain(session, entry_id)
    
    if existing:
        existing.entity = entity
        existing.primary_key = primary_key
        existing.time_grain = time_grain
        existing.natural_key = natural_key
        existing.notes = notes
        existing.updated_at = datetime.utcnow()
        grain = existing
    else:
        grain = DictionaryGrain(
            entry_id=entry_id,
            entity=entity,
            primary_key=primary_key,
            time_grain=time_grain,
            natural_key=natural_key,
            notes=notes
        )
        session.add(grain)
    
    session.commit()
    session.refresh(grain)
    
    return grain


def list_grains(
    session: Session,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    table_name: Optional[str] = None
) -> List[Tuple[DictionaryGrain, DictionaryEntry]]:
    """List grains with their entries."""
    query = select(DictionaryGrain, DictionaryEntry).join(
        DictionaryEntry,
        DictionaryGrain.entry_id == DictionaryEntry.id
    )
    
    if database_name:
        query = query.where(DictionaryEntry.database_name == database_name)
    if schema_name:
        query = query.where(DictionaryEntry.schema_name == schema_name)
    if table_name:
        query = query.where(DictionaryEntry.table_name == table_name)
    
    return list(session.exec(query).all())


# ==================== Relationship Management ====================

def list_relationships(
    session: Session,
    entry_id: Optional[UUID] = None,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    table_name: Optional[str] = None,
    status: Optional[str] = None,
    relationship_kind: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[DictionaryRelationship], int]:
    """List relationships with filters."""
    query = select(DictionaryRelationship)
    
    if entry_id:
        query = query.where(
            or_(
                DictionaryRelationship.left_entry_id == entry_id,
                DictionaryRelationship.right_entry_id == entry_id
            )
        )
    
    if database_name or schema_name or table_name:
        # Join with entries to filter by coordinates
        query = query.join(
            DictionaryEntry,
            or_(
                DictionaryRelationship.left_entry_id == DictionaryEntry.id,
                DictionaryRelationship.right_entry_id == DictionaryEntry.id
            )
        )
        
        if database_name:
            query = query.where(DictionaryEntry.database_name == database_name)
        if schema_name:
            query = query.where(DictionaryEntry.schema_name == schema_name)
        if table_name:
            query = query.where(DictionaryEntry.table_name == table_name)
    
    if status:
        query = query.where(DictionaryRelationship.status == status)
    
    if relationship_kind:
        query = query.where(DictionaryRelationship.relationship_kind == relationship_kind)
    
    # Get total count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    
    # Get paginated results
    results = session.exec(
        query.order_by(DictionaryRelationship.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    
    return list(results), total


def create_relationship(
    session: Session,
    relationship_kind: str,
    left_entry_id: UUID,
    right_entry_id: UUID,
    relationship_type: str,
    status: str = "suggested",
    cardinality: Optional[str] = None,
    left_ref: Optional[Dict[str, Any]] = None,
    right_ref: Optional[Dict[str, Any]] = None,
    match_rate_sample: Optional[float] = None,
    left_null_rate: Optional[float] = None,
    right_unique: Optional[bool] = None,
    suggested_join_sql: Optional[str] = None,
    grain_compatibility: Optional[Dict[str, Any]] = None,
    semantic_definition: Optional[Dict[str, Any]] = None,
    confidence_score: Optional[float] = None,
    created_by: Optional[str] = None
) -> DictionaryRelationship:
    """Create a new relationship."""
    rel = DictionaryRelationship(
        relationship_kind=relationship_kind,
        status=status,
        left_entry_id=left_entry_id,
        right_entry_id=right_entry_id,
        left_ref=left_ref,
        right_ref=right_ref,
        relationship_type=relationship_type,
        cardinality=cardinality,
        match_rate_sample=match_rate_sample,
        left_null_rate=left_null_rate,
        right_unique=right_unique,
        suggested_join_sql=suggested_join_sql,
        grain_compatibility=grain_compatibility or {},
        semantic_definition=semantic_definition or {},
        confidence_score=confidence_score,
        created_by=created_by
    )
    
    session.add(rel)
    session.commit()
    session.refresh(rel)
    
    return rel


def update_relationship_status(
    session: Session,
    relationship_id: UUID,
    status: str
) -> DictionaryRelationship:
    """Update relationship status."""
    rel = session.get(DictionaryRelationship, relationship_id)
    if not rel:
        raise ValueError(f"Relationship {relationship_id} not found")
    
    rel.status = status
    rel.updated_at = datetime.utcnow()
    
    session.add(rel)
    session.commit()
    session.refresh(rel)
    
    return rel


def update_relationship_fields(
    session: Session,
    relationship_id: UUID,
    updates: Dict[str, Any]
) -> DictionaryRelationship:
    """Update editable relationship fields."""
    rel = session.get(DictionaryRelationship, relationship_id)
    if not rel:
        raise ValueError(f"Relationship {relationship_id} not found")
    
    # Editable fields
    editable = [
        'cardinality', 'grain_compatibility', 'semantic_definition',
        'confidence_score', 'suggested_join_sql', 'relationship_type'
    ]
    
    for field in editable:
        if field in updates:
            setattr(rel, field, updates[field])
    
    rel.updated_at = datetime.utcnow()
    
    session.add(rel)
    session.commit()
    session.refresh(rel)
    
    return rel


def delete_relationship(
    session: Session,
    relationship_id: UUID,
    force: bool = False
) -> bool:
    """Delete a relationship. Only allowed for suggested/rejected unless forced."""
    rel = session.get(DictionaryRelationship, relationship_id)
    if not rel:
        raise ValueError(f"Relationship {relationship_id} not found")
    
    if not force and rel.status not in ['suggested', 'rejected']:
        # Soft delete by deprecating
        rel.status = 'deprecated'
        rel.updated_at = datetime.utcnow()
        session.add(rel)
        session.commit()
        return False
    else:
        # Hard delete
        session.delete(rel)
        session.commit()
        return True


# ==================== Versioning ====================

def create_entry_version(session: Session, entry: DictionaryEntry) -> DictionaryEntryVersion:
    """Create a version snapshot of an entry."""
    # Get current version number
    latest_version = session.exec(
        select(DictionaryEntryVersion)
        .where(DictionaryEntryVersion.entry_id == entry.id)
        .order_by(DictionaryEntryVersion.version.desc())
    ).first()
    
    version_num = (latest_version.version + 1) if latest_version else 1
    
    # Build snapshot
    snapshot = {
        "entry": entry.dict(),
        "semantics": None,
        "grain": None
    }
    
    # Include semantics if exists
    semantics = get_semantics(session, entry.id)
    if semantics:
        snapshot["semantics"] = {
            "decision_context": semantics.decision_context,
            "semantic_guarantees": semantics.semantic_guarantees,
            "validation_state": semantics.validation_state
        }
    
    # Include grain if exists
    grain = get_grain(session, entry.id)
    if grain:
        snapshot["grain"] = grain.dict()
    
    version = DictionaryEntryVersion(
        entry_id=entry.id,
        version=version_num,
        snapshot=snapshot
    )
    
    session.add(version)
    session.commit()
    session.refresh(version)
    
    return version


# ==================== Context Blob ====================

def get_entry_context_blob(
    session: Session,
    entry_id: UUID,
    include_relationships: bool = True,
    max_relationships: int = 10
) -> Dict[str, Any]:
    """Get comprehensive context blob for an entry."""
    entry = session.get(DictionaryEntry, entry_id)
    if not entry:
        raise ValueError(f"Entry {entry_id} not found")
    
    # Base entry
    context = {
        "entry": {
            "id": str(entry.id),
            "type": entry.entry_type,
            "title": entry.title,
            "description": entry.description,
            "database": entry.database_name,
            "schema": entry.schema_name,
            "table": entry.table_name,
            "column": entry.column_name,
            "concept": entry.concept_name,
            "tags": entry.tags or []
        }
    }
    
    # Semantics
    semantics = get_semantics(session, entry_id)
    if semantics:
        context["decision_context"] = semantics.decision_context
        context["semantic_guarantees"] = semantics.semantic_guarantees
        context["validation_state"] = semantics.validation_state
    
    # Grain
    grain = get_grain(session, entry_id)
    if grain:
        context["grain"] = {
            "entity": grain.entity,
            "primary_key": grain.primary_key,
            "time_grain": grain.time_grain,
            "natural_key": grain.natural_key,
            "notes": grain.notes
        }
    
    # Relationships
    if include_relationships:
        rels, _ = list_relationships(
            session,
            entry_id=entry_id,
            status="approved",
            limit=max_relationships
        )
        
        context["relationships"] = []
        for rel in rels:
            left_entry = session.get(DictionaryEntry, rel.left_entry_id)
            right_entry = session.get(DictionaryEntry, rel.right_entry_id)
            
            context["relationships"].append({
                "id": str(rel.id),
                "kind": rel.relationship_kind,
                "type": rel.relationship_type,
                "cardinality": rel.cardinality,
                "left": {
                    "id": str(left_entry.id) if left_entry else None,
                    "title": left_entry.title if left_entry else None
                },
                "right": {
                    "id": str(right_entry.id) if right_entry else None,
                    "title": right_entry.title if right_entry else None
                },
                "confidence": rel.confidence_score
            })
    
    return context

