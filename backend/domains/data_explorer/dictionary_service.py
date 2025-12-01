"""Service layer for Data Dictionary management."""
from datetime import datetime
from typing import List, Dict, Any
from sqlmodel import Session, select
from .db_models import DataDictionaryEntry


def upsert_dictionary_entries(session: Session, entries: List[Dict[str, Any]], database_name: str = "default") -> int:
    """
    Upsert dictionary entries from LLM analysis.
    
    Args:
        session: Database session
        entries: List of dictionary entry dictionaries
        database_name: Override database_name if not in entries
    
    Returns:
        Number of entries processed
    """
    count = 0
    
    for entry_data in entries:
        # Ensure database_name is set
        if "database_name" not in entry_data:
            entry_data["database_name"] = database_name
        
        # Find existing entry
        existing = session.exec(
            select(DataDictionaryEntry).where(
                DataDictionaryEntry.database_name == entry_data.get("database_name"),
                DataDictionaryEntry.schema_name == entry_data.get("schema_name"),
                DataDictionaryEntry.table_name == entry_data.get("table_name"),
                DataDictionaryEntry.column_name == entry_data.get("column_name"),
            )
        ).first()
        
        if existing:
            # Update existing entry (only if source is still llm_initial or we're overwriting)
            if existing.source == "llm_initial" or existing.source.startswith("llm"):
                existing.business_name = entry_data.get("business_name")
                existing.business_description = entry_data.get("business_description")
                existing.technical_description = entry_data.get("technical_description")
                existing.data_type = entry_data.get("data_type")
                existing.examples = entry_data.get("examples", [])
                existing.tags = entry_data.get("tags", [])
                existing.source = entry_data.get("source", "llm_initial")
                existing.updated_at = datetime.utcnow()
                session.add(existing)
                count += 1
        else:
            # Create new entry
            new_entry = DataDictionaryEntry(
                database_name=entry_data.get("database_name"),
                schema_name=entry_data.get("schema_name"),
                table_name=entry_data.get("table_name"),
                column_name=entry_data.get("column_name"),
                business_name=entry_data.get("business_name"),
                business_description=entry_data.get("business_description"),
                technical_description=entry_data.get("technical_description"),
                data_type=entry_data.get("data_type"),
                examples=entry_data.get("examples", []),
                tags=entry_data.get("tags", []),
                source=entry_data.get("source", "llm_initial"),
            )
            session.add(new_entry)
            count += 1
    
    session.commit()
    return count


def get_dictionary_for_tables(session: Session, database_name: str, schema_name: str, table_names: List[str]) -> List[DataDictionaryEntry]:
    """
    Retrieve dictionary entries for specific tables.
    
    Args:
        session: Database session
        database_name: Database name
        schema_name: Schema name
        table_names: List of table names
    
    Returns:
        List of dictionary entries
    """
    statement = select(DataDictionaryEntry).where(
        DataDictionaryEntry.database_name == database_name,
        DataDictionaryEntry.schema_name == schema_name,
        DataDictionaryEntry.table_name.in_(table_names)
    )
    return list(session.exec(statement).all())


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

