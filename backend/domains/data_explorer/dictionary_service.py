"""Service layer for Data Dictionary management."""
from datetime import datetime
from typing import List, Dict, Any
from sqlmodel import Session, select
from .db_models import DataDictionaryEntry


def upsert_dictionary_entries(session: Session, entries: List[Dict[str, Any]], database_name: str = "default", create_new_version: bool = False) -> int:
    """
    Upsert dictionary entries from LLM analysis with versioning support.
    
    Args:
        session: Database session
        entries: List of dictionary entry dictionaries
        database_name: Override database_name if not in entries
        create_new_version: If True, creates new version instead of updating active one
    
    Returns:
        Number of entries processed
    """
    count = 0
    
    for entry_data in entries:
        # Ensure database_name is set
        if "database_name" not in entry_data:
            entry_data["database_name"] = database_name
        
        # Find active entry for this column
        active_entry = session.exec(
            select(DataDictionaryEntry).where(
                DataDictionaryEntry.database_name == entry_data.get("database_name"),
                DataDictionaryEntry.schema_name == entry_data.get("schema_name"),
                DataDictionaryEntry.table_name == entry_data.get("table_name"),
                DataDictionaryEntry.column_name == entry_data.get("column_name"),
                DataDictionaryEntry.is_active == True
            )
        ).first()
        
        if active_entry:
            # Decide whether to update or create new version
            if create_new_version or active_entry.source == "human_edited":
                # Create new version, deactivate old one
                active_entry.is_active = False
                session.add(active_entry)
                
                new_entry = DataDictionaryEntry(
                    database_name=entry_data.get("database_name"),
                    schema_name=entry_data.get("schema_name"),
                    table_name=entry_data.get("table_name"),
                    column_name=entry_data.get("column_name"),
                    version_number=active_entry.version_number + 1,
                    is_active=True,
                    business_name=entry_data.get("business_name"),
                    business_description=entry_data.get("business_description"),
                    technical_description=entry_data.get("technical_description"),
                    data_type=entry_data.get("data_type"),
                    examples=entry_data.get("examples", []),
                    tags=entry_data.get("tags", []),
                    source=entry_data.get("source", "llm_initial"),
                    version_notes=entry_data.get("version_notes", "Updated by AI analysis")
                )
                session.add(new_entry)
                count += 1
            else:
                # Update existing entry in place (only if llm_initial)
                active_entry.business_name = entry_data.get("business_name")
                active_entry.business_description = entry_data.get("business_description")
                active_entry.technical_description = entry_data.get("technical_description")
                active_entry.data_type = entry_data.get("data_type")
                active_entry.examples = entry_data.get("examples", [])
                active_entry.tags = entry_data.get("tags", [])
                active_entry.source = entry_data.get("source", "llm_initial")
                active_entry.updated_at = datetime.utcnow()
                session.add(active_entry)
                count += 1
        else:
            # Create new entry (version 1)
            new_entry = DataDictionaryEntry(
                database_name=entry_data.get("database_name"),
                schema_name=entry_data.get("schema_name"),
                table_name=entry_data.get("table_name"),
                column_name=entry_data.get("column_name"),
                version_number=1,
                is_active=True,
                business_name=entry_data.get("business_name"),
                business_description=entry_data.get("business_description"),
                technical_description=entry_data.get("technical_description"),
                data_type=entry_data.get("data_type"),
                examples=entry_data.get("examples", []),
                tags=entry_data.get("tags", []),
                source=entry_data.get("source", "llm_initial"),
                version_notes="Initial documentation"
            )
            session.add(new_entry)
            count += 1
    
    session.commit()
    return count


def get_dictionary_for_tables(session: Session, database_name: str, schema_name: str, table_names: List[str], active_only: bool = True) -> List[DataDictionaryEntry]:
    """
    Retrieve dictionary entries for specific tables.
    
    Args:
        session: Database session
        database_name: Database name
        schema_name: Schema name
        table_names: List of table names
        active_only: If True, only return active versions
    
    Returns:
        List of dictionary entries
    """
    statement = select(DataDictionaryEntry).where(
        DataDictionaryEntry.database_name == database_name,
        DataDictionaryEntry.schema_name == schema_name,
        DataDictionaryEntry.table_name.in_(table_names)
    )
    
    if active_only:
        statement = statement.where(DataDictionaryEntry.is_active == True)
    
    return list(session.exec(statement).all())


def get_column_versions(session: Session, database_name: str, schema_name: str, table_name: str, column_name: str) -> List[DataDictionaryEntry]:
    """
    Get all versions of a specific column's documentation.
    
    Returns entries ordered by version_number descending (newest first).
    """
    statement = select(DataDictionaryEntry).where(
        DataDictionaryEntry.database_name == database_name,
        DataDictionaryEntry.schema_name == schema_name,
        DataDictionaryEntry.table_name == table_name,
        DataDictionaryEntry.column_name == column_name
    ).order_by(DataDictionaryEntry.version_number.desc())
    
    return list(session.exec(statement).all())


def activate_version(session: Session, entry_id: int) -> DataDictionaryEntry:
    """
    Activate a specific version of a dictionary entry.
    Deactivates all other versions of the same column.
    
    Args:
        session: Database session
        entry_id: ID of the entry to activate
    
    Returns:
        The activated entry
    """
    entry = session.get(DataDictionaryEntry, entry_id)
    if not entry:
        raise ValueError(f"Entry {entry_id} not found")
    
    # Deactivate all versions of this column
    all_versions = session.exec(
        select(DataDictionaryEntry).where(
            DataDictionaryEntry.database_name == entry.database_name,
            DataDictionaryEntry.schema_name == entry.schema_name,
            DataDictionaryEntry.table_name == entry.table_name,
            DataDictionaryEntry.column_name == entry.column_name
        )
    ).all()
    
    for version in all_versions:
        version.is_active = False
        session.add(version)
    
    # Activate the selected version
    entry.is_active = True
    entry.updated_at = datetime.utcnow()
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    return entry


def format_dictionary_as_context(entries: List[DataDictionaryEntry]) -> str:
    """
    Format dictionary entries as natural language context for LLM prompts.
    
    Args:
        entries: List of dictionary entries
    
    Returns:
        Formatted string suitable for inclusion in prompts
    """
    if not entries:
        return "No data dictionary entries available for these tables."
    
    lines = ["# Data Dictionary Context\n"]
    
    # Group by table
    by_table: Dict[str, List[DataDictionaryEntry]] = {}
    for entry in entries:
        key = f"{entry.schema_name}.{entry.table_name}"
        if key not in by_table:
            by_table[key] = []
        by_table[key].append(entry)
    
    for table_key, table_entries in by_table.items():
        lines.append(f"\n## {table_key}\n")
        for entry in table_entries:
            lines.append(f"**{entry.column_name}** ({entry.data_type or 'unknown'})")
            if entry.business_description:
                lines.append(f"  - {entry.business_description}")
            if entry.tags:
                lines.append(f"  - Tags: {', '.join(entry.tags)}")
            lines.append("")
    
    return "\n".join(lines)

