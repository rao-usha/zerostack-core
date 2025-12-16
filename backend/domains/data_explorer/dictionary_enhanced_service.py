"""Service layer for enhanced data dictionary operations."""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlmodel import Session, select, func, or_, and_
from sqlalchemy import text

from .dictionary_enhanced_models import (
    DictionaryAsset,
    DictionaryField,
    DictionaryRelationship,
    DictionaryProfile,
    DictionaryUsageLog,
    TrustTier,
    EntityRole,
    Cardinality,
    RelationshipConfidence
)


def sync_assets_from_information_schema(
    session: Session,
    connection_id: str,
    db_connection: Any,
    schema_filter: Optional[str] = None
) -> Dict[str, int]:
    """
    Sync table/view structure from information_schema into dictionary_assets and dictionary_fields.
    Only updates structural fields, preserves user-authored business metadata.
    
    Returns: {"tables_synced": N, "columns_synced": M}
    """
    stats = {"tables_synced": 0, "columns_synced": 0}
    
    # Query information_schema for tables
    schema_clause = f"AND table_schema = '{schema_filter}'" if schema_filter else ""
    tables_query = f"""
        SELECT 
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        {schema_clause}
        ORDER BY table_schema, table_name
    """
    
    tables_result = db_connection.execute(text(tables_query))
    
    for row in tables_result:
        schema_name = row[0]
        table_name = row[1]
        table_type = 'view' if row[2] == 'VIEW' else 'table'
        
        # Upsert asset
        existing_asset = session.exec(
            select(DictionaryAsset).where(
                DictionaryAsset.connection_id == connection_id,
                DictionaryAsset.schema_name == schema_name,
                DictionaryAsset.table_name == table_name
            )
        ).first()
        
        if existing_asset:
            # Update only structural fields
            existing_asset.asset_type = table_type
            existing_asset.updated_at = datetime.utcnow()
            session.add(existing_asset)
        else:
            # Create new asset with defaults
            new_asset = DictionaryAsset(
                connection_id=connection_id,
                schema_name=schema_name,
                table_name=table_name,
                asset_type=table_type,
                business_name=table_name.replace('_', ' ').title(),  # Default friendly name
                trust_tier="experimental",
                trust_score=50
            )
            session.add(new_asset)
            session.flush()  # Get ID
            existing_asset = new_asset
        
        stats["tables_synced"] += 1
        
        # Query columns for this table
        columns_query = f"""
            SELECT 
                column_name,
                ordinal_position,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        
        columns_result = db_connection.execute(text(columns_query))
        
        for col_row in columns_result:
            column_name = col_row[0]
            ordinal_position = col_row[1]
            data_type = col_row[2]
            is_nullable = col_row[3] == 'YES'
            default_value = col_row[4]
            
            # Upsert field
            existing_field = session.exec(
                select(DictionaryField).where(
                    DictionaryField.asset_id == existing_asset.id,
                    DictionaryField.column_name == column_name
                )
            ).first()
            
            if existing_field:
                # Update only structural fields
                existing_field.ordinal_position = ordinal_position
                existing_field.data_type = data_type
                existing_field.is_nullable = is_nullable
                existing_field.default_value = default_value
                existing_field.updated_at = datetime.utcnow()
                session.add(existing_field)
            else:
                # Create new field with defaults
                new_field = DictionaryField(
                    asset_id=existing_asset.id,
                    column_name=column_name,
                    ordinal_position=ordinal_position,
                    data_type=data_type,
                    is_nullable=is_nullable,
                    default_value=default_value,
                    business_name=column_name.replace('_', ' ').title(),
                    entity_role="other",
                    trust_tier="experimental",
                    trust_score=50
                )
                session.add(new_field)
            
            stats["columns_synced"] += 1
    
    session.commit()
    return stats


def get_asset_by_table(
    session: Session,
    connection_id: str,
    schema_name: str,
    table_name: str
) -> Optional[DictionaryAsset]:
    """Get asset by connection/schema/table."""
    return session.exec(
        select(DictionaryAsset).where(
            DictionaryAsset.connection_id == connection_id,
            DictionaryAsset.schema_name == schema_name,
            DictionaryAsset.table_name == table_name
        )
    ).first()


def get_fields_for_asset(
    session: Session,
    asset_id: UUID
) -> List[DictionaryField]:
    """Get all fields for an asset."""
    return list(session.exec(
        select(DictionaryField)
        .where(DictionaryField.asset_id == asset_id)
        .order_by(DictionaryField.ordinal_position)
    ).all())


def search_assets(
    session: Session,
    connection_id: str,
    schema_name: Optional[str] = None,
    search_term: Optional[str] = None,
    trust_tier: Optional[str] = None,
    business_domain: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[DictionaryAsset], int]:
    """Search assets with filters. Returns (results, total_count)."""
    query = select(DictionaryAsset).where(DictionaryAsset.connection_id == connection_id)
    
    if schema_name:
        query = query.where(DictionaryAsset.schema_name == schema_name)
    
    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.where(
            or_(
                DictionaryAsset.table_name.ilike(search_pattern),
                DictionaryAsset.business_name.ilike(search_pattern),
                DictionaryAsset.business_definition.ilike(search_pattern)
            )
        )
    
    if trust_tier:
        query = query.where(DictionaryAsset.trust_tier == trust_tier)
    
    if business_domain:
        query = query.where(DictionaryAsset.business_domain == business_domain)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    
    # Get paginated results
    results = session.exec(
        query.order_by(DictionaryAsset.schema_name, DictionaryAsset.table_name)
        .limit(limit)
        .offset(offset)
    ).all()
    
    return list(results), total


def update_asset_metadata(
    session: Session,
    asset_id: UUID,
    updates: Dict[str, Any]
) -> DictionaryAsset:
    """Update business metadata for an asset."""
    asset = session.get(DictionaryAsset, asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")
    
    # Update allowed fields
    updateable_fields = [
        'business_name', 'business_definition', 'business_domain',
        'grain', 'row_meaning', 'owner', 'steward', 'tags',
        'trust_tier', 'trust_score', 'approved_for_reporting',
        'approved_for_ml', 'known_issues', 'issue_tags'
    ]
    
    for field in updateable_fields:
        if field in updates:
            setattr(asset, field, updates[field])
    
    asset.updated_at = datetime.utcnow()
    session.add(asset)
    session.commit()
    session.refresh(asset)
    
    return asset


def update_field_metadata(
    session: Session,
    field_id: UUID,
    updates: Dict[str, Any]
) -> DictionaryField:
    """Update business metadata for a field."""
    field = session.get(DictionaryField, field_id)
    if not field:
        raise ValueError(f"Field {field_id} not found")
    
    # Update allowed fields
    updateable_fields = [
        'business_name', 'business_definition', 'entity_role', 'tags',
        'trust_tier', 'trust_score', 'approved_for_reporting',
        'approved_for_ml', 'known_issues', 'issue_tags'
    ]
    
    for field in updateable_fields:
        if field in updates:
            setattr(field, field, updates[field])
    
    field.updated_at = datetime.utcnow()
    session.add(field)
    session.commit()
    session.refresh(field)
    
    return field


def create_relationship(
    session: Session,
    connection_id: str,
    source_schema: str,
    source_table: str,
    source_column: str,
    target_schema: str,
    target_table: str,
    target_column: str,
    cardinality: str = "unknown",
    confidence: str = "assumed",
    notes: Optional[str] = None
) -> DictionaryRelationship:
    """Create a new relationship."""
    rel = DictionaryRelationship(
        connection_id=connection_id,
        source_schema=source_schema,
        source_table=source_table,
        source_column=source_column,
        target_schema=target_schema,
        target_table=target_table,
        target_column=target_column,
        cardinality=cardinality,
        confidence=confidence,
        notes=notes
    )
    
    session.add(rel)
    session.commit()
    session.refresh(rel)
    
    return rel


def get_relationships_for_table(
    session: Session,
    connection_id: str,
    schema_name: str,
    table_name: str
) -> List[DictionaryRelationship]:
    """Get all relationships where table is source or target."""
    return list(session.exec(
        select(DictionaryRelationship).where(
            DictionaryRelationship.connection_id == connection_id,
            or_(
                and_(
                    DictionaryRelationship.source_schema == schema_name,
                    DictionaryRelationship.source_table == table_name
                ),
                and_(
                    DictionaryRelationship.target_schema == schema_name,
                    DictionaryRelationship.target_table == table_name
                )
            )
        )
    ).all())


def get_latest_profile(
    session: Session,
    connection_id: str,
    schema_name: str,
    table_name: str,
    column_name: str
) -> Optional[DictionaryProfile]:
    """Get the most recent profile for a column."""
    return session.exec(
        select(DictionaryProfile)
        .where(
            DictionaryProfile.connection_id == connection_id,
            DictionaryProfile.schema_name == schema_name,
            DictionaryProfile.table_name == table_name,
            DictionaryProfile.column_name == column_name
        )
        .order_by(DictionaryProfile.computed_at.desc())
    ).first()


def get_profiles_for_table(
    session: Session,
    connection_id: str,
    schema_name: str,
    table_name: str,
    latest_only: bool = True
) -> List[DictionaryProfile]:
    """Get profiles for all columns in a table."""
    if latest_only:
        # Get latest profile for each column
        # This is a bit complex - need to group by column and get max computed_at
        subquery = (
            select(
                DictionaryProfile.column_name,
                func.max(DictionaryProfile.computed_at).label('max_computed_at')
            )
            .where(
                DictionaryProfile.connection_id == connection_id,
                DictionaryProfile.schema_name == schema_name,
                DictionaryProfile.table_name == table_name
            )
            .group_by(DictionaryProfile.column_name)
            .subquery()
        )
        
        query = select(DictionaryProfile).join(
            subquery,
            and_(
                DictionaryProfile.column_name == subquery.c.column_name,
                DictionaryProfile.computed_at == subquery.c.max_computed_at
            )
        ).where(
            DictionaryProfile.connection_id == connection_id,
            DictionaryProfile.schema_name == schema_name,
            DictionaryProfile.table_name == table_name
        )
        
        return list(session.exec(query).all())
    else:
        # Get all profiles
        return list(session.exec(
            select(DictionaryProfile)
            .where(
                DictionaryProfile.connection_id == connection_id,
                DictionaryProfile.schema_name == schema_name,
                DictionaryProfile.table_name == table_name
            )
            .order_by(DictionaryProfile.column_name, DictionaryProfile.computed_at.desc())
        ).all())


def log_usage_event(
    session: Session,
    connection_id: str,
    event_type: str,
    schemas_used: Optional[List[str]] = None,
    tables_used: Optional[List[str]] = None,
    columns_used: Optional[List[str]] = None,
    query_text: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> DictionaryUsageLog:
    """Log a usage event."""
    import hashlib
    
    query_hash = None
    if query_text:
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:64]
    
    log_entry = DictionaryUsageLog(
        connection_id=connection_id,
        event_type=event_type,
        schemas_used=schemas_used,
        tables_used=tables_used,
        columns_used=columns_used,
        query_text=query_text,
        query_hash=query_hash,
        user_id=user_id,
        session_id=session_id,
        event_at=datetime.utcnow()
    )
    
    session.add(log_entry)
    session.commit()
    
    return log_entry


def aggregate_usage_stats(
    session: Session,
    connection_id: str,
    days: int = 30
) -> Dict[str, int]:
    """
    Aggregate usage logs into dictionary_assets and dictionary_fields usage counters.
    Returns stats about what was updated.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    stats = {"assets_updated": 0, "fields_updated": 0}
    
    # Aggregate table-level usage
    table_usage_query = text("""
        SELECT 
            UNNEST(tables_used) as table_name,
            COUNT(*) as usage_count,
            MAX(event_at) as last_used
        FROM dictionary_usage_logs
        WHERE connection_id = :connection_id
        AND event_at >= :cutoff_date
        AND tables_used IS NOT NULL
        GROUP BY UNNEST(tables_used)
    """)
    
    table_results = session.execute(
        table_usage_query,
        {"connection_id": connection_id, "cutoff_date": cutoff_date}
    )
    
    for row in table_results:
        # Parse table_name (format: "schema.table")
        parts = row[0].split('.')
        if len(parts) != 2:
            continue
        
        schema_name, table_name = parts
        
        asset = get_asset_by_table(session, connection_id, schema_name, table_name)
        if asset:
            asset.query_count_30d = row[1]
            asset.last_queried_at = row[2]
            session.add(asset)
            stats["assets_updated"] += 1
    
    session.commit()
    
    # TODO: Similar logic for column-level usage
    
    return stats


def get_dictionary_context(
    session: Session,
    connection_id: str,
    schema_name: str,
    table_name: str
) -> Dict[str, Any]:
    """
    Get comprehensive dictionary context for a table, suitable for LLM grounding.
    Returns a compact JSON bundle with asset metadata, fields, relationships, and profiles.
    """
    asset = get_asset_by_table(session, connection_id, schema_name, table_name)
    if not asset:
        return {"error": "Asset not found"}
    
    fields = get_fields_for_asset(session, asset.id)
    relationships = get_relationships_for_table(session, connection_id, schema_name, table_name)
    profiles = get_profiles_for_table(session, connection_id, schema_name, table_name, latest_only=True)
    
    # Build context
    context = {
        "table": {
            "name": f"{schema_name}.{table_name}",
            "business_name": asset.business_name,
            "definition": asset.business_definition,
            "domain": asset.business_domain,
            "grain": asset.grain or asset.row_meaning,
            "trust_tier": asset.trust_tier,
            "trust_score": asset.trust_score,
            "row_count": asset.row_count_estimate
        },
        "columns": [],
        "relationships": [],
        "quality_summary": {}
    }
    
    # Add column info
    for field in fields:
        # Find profile for this field
        profile = next((p for p in profiles if p.column_name == field.column_name), None)
        
        col_info = {
            "name": field.column_name,
            "business_name": field.business_name,
            "definition": field.business_definition,
            "role": field.entity_role,
            "data_type": field.data_type,
            "nullable": field.is_nullable,
            "trust_tier": field.trust_tier
        }
        
        if profile:
            col_info["profile"] = {
                "null_fraction": profile.null_fraction,
                "distinct_count": profile.distinct_count or profile.distinct_count_estimate,
                "has_stats": True
            }
        
        context["columns"].append(col_info)
    
    # Add relationships
    for rel in relationships:
        is_source = rel.source_schema == schema_name and rel.source_table == table_name
        
        context["relationships"].append({
            "direction": "outgoing" if is_source else "incoming",
            "from": f"{rel.source_schema}.{rel.source_table}.{rel.source_column}",
            "to": f"{rel.target_schema}.{rel.target_table}.{rel.target_column}",
            "cardinality": rel.cardinality,
            "confidence": rel.confidence
        })
    
    return context


