"""Relationship inference job for discovering candidate relationships."""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID
from sqlmodel import Session, select, text
from sqlalchemy import create_engine
import logging

from .dictionary_semantics_models import (
    DictionaryEntry,
    DictionaryRelationship,
    DictionaryInferenceJob,
    EntryType,
    RelationshipKind,
    CandidateRelationshipType,
)
from .dictionary_semantics_service import get_or_create_entry, create_relationship
from .connection import get_db_connection

logger = logging.getLogger(__name__)


# ==================== Column Pattern Matching ====================

def extract_column_patterns(column_name: str) -> Set[str]:
    """Extract patterns from column name for matching."""
    patterns = set()
    
    # Normalize
    normalized = column_name.lower().strip()
    patterns.add(normalized)
    
    # Common suffixes
    for suffix in ['_id', '_key', '_code', '_num', '_number']:
        if normalized.endswith(suffix):
            base = normalized[:-len(suffix)]
            patterns.add(base)
            patterns.add(f"{base}{suffix}")
    
    # If it's just 'id', add it
    if normalized == 'id':
        patterns.add('id')
    
    # Remove underscores
    patterns.add(normalized.replace('_', ''))
    
    return patterns


def columns_match(left_col: str, right_col: str) -> Tuple[bool, float]:
    """Check if columns match and return similarity score."""
    left_patterns = extract_column_patterns(left_col)
    right_patterns = extract_column_patterns(right_col)
    
    # Exact match
    if left_col.lower() == right_col.lower():
        return True, 1.0
    
    # Pattern overlap
    overlap = left_patterns & right_patterns
    if overlap:
        # Calculate Jaccard similarity
        union = left_patterns | right_patterns
        similarity = len(overlap) / len(union)
        return similarity > 0.3, similarity
    
    return False, 0.0


def types_compatible(left_type: str, right_type: str) -> Tuple[bool, float]:
    """Check if data types are compatible."""
    # Normalize types
    left_norm = left_type.lower().strip()
    right_norm = right_type.lower().strip()
    
    # Exact match
    if left_norm == right_norm:
        return True, 1.0
    
    # Integer types
    int_types = {'integer', 'int', 'bigint', 'smallint', 'int2', 'int4', 'int8'}
    if left_norm in int_types and right_norm in int_types:
        return True, 0.9
    
    # String types
    str_types = {'varchar', 'text', 'character varying', 'char', 'character'}
    if any(t in left_norm for t in str_types) and any(t in right_norm for t in str_types):
        return True, 0.8
    
    # Numeric types
    num_types = {'numeric', 'decimal', 'float', 'double', 'real'}
    if any(t in left_norm for t in num_types) and any(t in right_norm for t in num_types):
        return True, 0.9
    
    # UUID types
    if 'uuid' in left_norm and 'uuid' in right_norm:
        return True, 1.0
    
    return False, 0.0


# ==================== Sampling and Analysis ====================

def sample_column_values(
    db_connection: Any,
    schema: str,
    table: str,
    column: str,
    max_samples: int = 1000,
    timeout_seconds: int = 30
) -> Tuple[List[Any], int, float]:
    """
    Sample column values safely.
    Returns: (sample_values, distinct_count_estimate, null_rate)
    """
    try:
        # Set statement timeout
        db_connection.execute(text(f"SET statement_timeout = '{timeout_seconds}s'"))
        
        # Get row count estimate
        count_query = text(f"""
            SELECT reltuples::bigint AS estimate
            FROM pg_class
            WHERE oid = '{schema}.{table}'::regclass
        """)
        row_count_result = db_connection.execute(count_query).fetchone()
        row_count_estimate = row_count_result[0] if row_count_result else 0
        
        # Sample strategy
        if row_count_estimate > max_samples * 10:
            # Use TABLESAMPLE for large tables
            sample_query = text(f"""
                SELECT "{column}"
                FROM "{schema}"."{table}"
                TABLESAMPLE BERNOULLI (10)
                WHERE "{column}" IS NOT NULL
                LIMIT :limit
            """)
        else:
            # Direct sample for smaller tables
            sample_query = text(f"""
                SELECT "{column}"
                FROM "{schema}"."{table}"
                WHERE "{column}" IS NOT NULL
                LIMIT :limit
            """)
        
        result = db_connection.execute(sample_query, {"limit": max_samples})
        sample_values = [row[0] for row in result.fetchall()]
        
        # Get null rate
        null_query = text(f"""
            SELECT 
                COUNT(*) FILTER (WHERE "{column}" IS NULL)::float / NULLIF(COUNT(*), 0) as null_rate
            FROM "{schema}"."{table}"
            LIMIT 10000
        """)
        null_result = db_connection.execute(null_query).fetchone()
        null_rate = null_result[0] if null_result and null_result[0] else 0.0
        
        # Estimate distinct count
        distinct_query = text(f"""
            SELECT COUNT(DISTINCT "{column}") as distinct_count
            FROM (
                SELECT "{column}"
                FROM "{schema}"."{table}"
                LIMIT :limit
            ) sample
        """)
        distinct_result = db_connection.execute(distinct_query, {"limit": max_samples * 2})
        distinct_count = distinct_result.fetchone()[0] if distinct_result else 0
        
        return sample_values, distinct_count, null_rate
        
    except Exception as e:
        logger.warning(f"Failed to sample {schema}.{table}.{column}: {e}")
        return [], 0, 1.0
    finally:
        # Reset timeout
        try:
            db_connection.execute(text("RESET statement_timeout"))
        except:
            pass


def analyze_relationship(
    db_connection: Any,
    left_schema: str,
    left_table: str,
    left_column: str,
    right_schema: str,
    right_table: str,
    right_column: str,
    max_samples: int = 1000
) -> Optional[Dict[str, Any]]:
    """Analyze a potential relationship between two columns."""
    try:
        # Sample both columns
        left_values, left_distinct, left_null_rate = sample_column_values(
            db_connection, left_schema, left_table, left_column, max_samples
        )
        
        right_values, right_distinct, right_null_rate = sample_column_values(
            db_connection, right_schema, right_table, right_column, max_samples
        )
        
        if not left_values or not right_values:
            return None
        
        # Convert to sets for overlap analysis
        left_set = set(left_values)
        right_set = set(right_values)
        
        # Calculate overlap
        overlap = left_set & right_set
        overlap_ratio = len(overlap) / len(left_set) if left_set else 0.0
        
        # Check if right is unique (potential PK)
        right_unique = len(right_set) == len(right_values)
        
        # Infer cardinality
        if right_unique and overlap_ratio > 0.8:
            cardinality = "many_to_one"
        elif len(left_set) == len(left_values) and right_unique and overlap_ratio > 0.8:
            cardinality = "one_to_one"
        else:
            cardinality = "many_to_many"
        
        # Generate suggested join SQL
        suggested_join = f"""
SELECT *
FROM "{left_schema}"."{left_table}" l
JOIN "{right_schema}"."{right_table}" r
  ON l."{left_column}" = r."{right_column}"
        """.strip()
        
        return {
            "match_rate_sample": overlap_ratio,
            "left_null_rate": left_null_rate,
            "right_unique": right_unique,
            "cardinality": cardinality,
            "suggested_join_sql": suggested_join,
            "left_distinct": left_distinct,
            "right_distinct": right_distinct,
            "sample_size": min(len(left_values), len(right_values))
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze relationship: {e}")
        return None


# ==================== Inference Job ====================

def run_inference_job(
    session: Session,
    job_id: UUID,
    connection_id: str,
    schema_name: Optional[str] = None,
    include_tables: Optional[List[str]] = None,
    exclude_tables: Optional[List[str]] = None,
    max_samples: int = 1000
) -> Dict[str, Any]:
    """Run relationship inference job."""
    job = session.get(DictionaryInferenceJob, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    try:
        # Update job status
        job.status = "running"
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()
        
        # Get database connection
        db_conn = get_db_connection(connection_id)
        
        # Get tables to scan
        tables_query = text("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        
        if schema_name:
            tables_query = text(f"""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                AND table_schema = :schema
            """)
            tables_result = db_conn.execute(tables_query, {"schema": schema_name})
        else:
            tables_result = db_conn.execute(tables_query)
        
        tables = [(row[0], row[1]) for row in tables_result.fetchall()]
        
        # Filter tables
        if include_tables:
            tables = [(s, t) for s, t in tables if t in include_tables]
        if exclude_tables:
            tables = [(s, t) for s, t in tables if t not in exclude_tables]
        
        job.tables_scanned = len(tables)
        session.add(job)
        session.commit()
        
        # Get columns for each table
        table_columns: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        
        for schema, table in tables:
            job.current_stage = f"Scanning {schema}.{table}"
            session.add(job)
            session.commit()
            
            columns_query = text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = :table
                ORDER BY ordinal_position
            """)
            
            columns_result = db_conn.execute(
                columns_query,
                {"schema": schema, "table": table}
            )
            
            columns = [(row[0], row[1]) for row in columns_result.fetchall()]
            table_columns[(schema, table)] = columns
        
        # Find candidate relationships
        relationships_found = 0
        candidates = []
        
        for (left_schema, left_table), left_columns in table_columns.items():
            for left_col, left_type in left_columns:
                # Check if column looks like a key
                left_patterns = extract_column_patterns(left_col)
                
                # Look for matches in other tables
                for (right_schema, right_table), right_columns in table_columns.items():
                    # Skip same table
                    if left_schema == right_schema and left_table == right_table:
                        continue
                    
                    for right_col, right_type in right_columns:
                        # Check name match
                        name_match, name_similarity = columns_match(left_col, right_col)
                        if not name_match:
                            continue
                        
                        # Check type compatibility
                        type_match, type_similarity = types_compatible(left_type, right_type)
                        if not type_match:
                            continue
                        
                        # Analyze relationship
                        analysis = analyze_relationship(
                            db_conn,
                            left_schema, left_table, left_col,
                            right_schema, right_table, right_col,
                            max_samples
                        )
                        
                        if not analysis:
                            continue
                        
                        # Calculate confidence score
                        confidence = (
                            analysis["match_rate_sample"] * 0.5 +
                            name_similarity * 0.2 +
                            type_similarity * 0.2 +
                            (0.1 if analysis["right_unique"] else 0.0)
                        )
                        
                        # Only keep high-confidence candidates
                        if confidence < 0.5:
                            continue
                        
                        # Get or create entries
                        left_entry = get_or_create_entry(
                            session,
                            entry_type=EntryType.COLUMN.value,
                            title=f"{left_schema}.{left_table}.{left_col}",
                            database_name=connection_id,
                            schema_name=left_schema,
                            table_name=left_table,
                            column_name=left_col
                        )
                        
                        right_entry = get_or_create_entry(
                            session,
                            entry_type=EntryType.COLUMN.value,
                            title=f"{right_schema}.{right_table}.{right_col}",
                            database_name=connection_id,
                            schema_name=right_schema,
                            table_name=right_table,
                            column_name=right_col
                        )
                        
                        # Create relationship
                        rel = create_relationship(
                            session,
                            relationship_kind=RelationshipKind.CANDIDATE.value,
                            left_entry_id=left_entry.id,
                            right_entry_id=right_entry.id,
                            relationship_type=CandidateRelationshipType.FOREIGN_KEY_LIKE.value,
                            status="suggested",
                            cardinality=analysis["cardinality"],
                            left_ref={
                                "database": connection_id,
                                "schema": left_schema,
                                "table": left_table,
                                "column": left_col
                            },
                            right_ref={
                                "database": connection_id,
                                "schema": right_schema,
                                "table": right_table,
                                "column": right_col
                            },
                            match_rate_sample=analysis["match_rate_sample"],
                            left_null_rate=analysis["left_null_rate"],
                            right_unique=analysis["right_unique"],
                            suggested_join_sql=analysis["suggested_join_sql"],
                            confidence_score=confidence
                        )
                        
                        relationships_found += 1
                        candidates.append({
                            "id": str(rel.id),
                            "left": f"{left_schema}.{left_table}.{left_col}",
                            "right": f"{right_schema}.{right_table}.{right_col}",
                            "confidence": confidence,
                            "cardinality": analysis["cardinality"]
                        })
        
        # Update job completion
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.relationships_found = relationships_found
        job.result_summary = {
            "candidates": candidates[:100],  # Limit to first 100 for summary
            "total_relationships": relationships_found,
            "tables_scanned": len(tables)
        }
        session.add(job)
        session.commit()
        
        return {
            "status": "completed",
            "relationships_found": relationships_found,
            "tables_scanned": len(tables),
            "candidates": candidates
        }
        
    except Exception as e:
        logger.error(f"Inference job failed: {e}", exc_info=True)
        
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        session.add(job)
        session.commit()
        
        return {
            "status": "failed",
            "error": str(e)
        }

