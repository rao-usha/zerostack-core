"""
Service for discovering and managing data dictionary relationships.

This service implements relationship inference algorithms that analyze database
structure and sample data to discover potential relationships between assets.
"""
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text, select, insert, update, delete as sql_delete, and_, or_
from sqlalchemy.engine import Connection
from difflib import SequenceMatcher

from .relationship_intelligence_models import (
    DictionaryRelationship,
    DictionaryRelationshipCreate,
    DictionaryRelationshipUpdate,
    RelationshipType,
    RelationshipStatus,
    AssetType,
    DiscoveryJob,
    DiscoveryJobCreate,
    DiscoveryJobStatus,
    DiscoveryConfig,
    RelationshipEvidence,
    NameSimilarityEvidence,
    TypeCompatibilityEvidence,
    CardinalityEvidence,
    ValueOverlapEvidence,
)
from db.models import dictionary_relationships, dictionary_relationship_discovery_jobs


# ============================================================================
# Relationship Discovery Service
# ============================================================================

class RelationshipDiscoveryService:
    """Service for discovering relationships between data assets."""
    
    @staticmethod
    def _normalize_column_name(name: str) -> str:
        """
        Normalize column name for comparison.
        
        - Convert to lowercase
        - Remove underscores/hyphens
        - Handle common suffixes (_id, Id, ID)
        """
        name = name.lower()
        
        # Strip common ID suffixes for comparison
        for suffix in ['_id', '_key', '_code', '_num', '_number']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        # Remove separators
        name = re.sub(r'[_\-\s]+', '', name)
        
        return name
    
    @staticmethod
    def _calculate_name_similarity(name1: str, name2: str) -> Tuple[float, str]:
        """
        Calculate similarity between two column names.
        
        Returns:
            (similarity_score, match_type)
        """
        norm1 = RelationshipDiscoveryService._normalize_column_name(name1)
        norm2 = RelationshipDiscoveryService._normalize_column_name(name2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return 1.0, "exact"
        
        # Sequence similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Check for prefix/suffix patterns
        if norm1.startswith(norm2) or norm2.startswith(norm1):
            return max(similarity, 0.85), "prefix"
        
        if norm1.endswith(norm2) or norm2.endswith(norm1):
            return max(similarity, 0.85), "suffix"
        
        # Fuzzy match
        if similarity >= 0.7:
            return similarity, "fuzzy"
        
        return similarity, "none"
    
    @staticmethod
    def _are_types_compatible(type1: str, type2: str) -> Tuple[bool, str]:
        """
        Check if two SQL data types are compatible for joining.
        
        Returns:
            (compatible, reason)
        """
        type1 = type1.lower()
        type2 = type2.lower()
        
        # Exact match
        if type1 == type2:
            return True, "exact_match"
        
        # Numeric types
        numeric_types = {'integer', 'bigint', 'smallint', 'int', 'int4', 'int8', 'int2', 
                        'numeric', 'decimal', 'real', 'double precision', 'float', 'float4', 'float8'}
        if any(t in type1 for t in numeric_types) and any(t in type2 for t in numeric_types):
            return True, "both_numeric"
        
        # String types
        string_types = {'character varying', 'varchar', 'char', 'text', 'string'}
        if any(t in type1 for t in string_types) and any(t in type2 for t in string_types):
            return True, "both_string"
        
        # UUID types
        if 'uuid' in type1 and 'uuid' in type2:
            return True, "both_uuid"
        
        # Date/time types
        datetime_types = {'timestamp', 'date', 'time', 'datetime'}
        if any(t in type1 for t in datetime_types) and any(t in type2 for t in datetime_types):
            return True, "both_datetime"
        
        # Boolean types
        if ('bool' in type1 or 'bit' in type1) and ('bool' in type2 or 'bit' in type2):
            return True, "both_boolean"
        
        return False, "incompatible"
    
    @staticmethod
    def _analyze_cardinality(
        conn: Connection,
        schema1: str,
        table1: str,
        column1: str,
        schema2: str,
        table2: str,
        column2: str,
        sample_size: int = 10000
    ) -> Optional[CardinalityEvidence]:
        """
        Analyze cardinality relationship between two columns using sampling.
        
        Uses safe SQL with row limits to avoid full table scans.
        """
        try:
            # Sample from first column
            query1 = text(f"""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT "{column1}") as distinct_count,
                    COUNT(*) FILTER (WHERE "{column1}" IS NULL) as null_count
                FROM "{schema1}"."{table1}"
                LIMIT :limit
            """)
            result1 = conn.execute(query1, {"limit": sample_size}).fetchone()
            
            # Sample from second column
            query2 = text(f"""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT "{column2}") as distinct_count,
                    COUNT(*) FILTER (WHERE "{column2}" IS NULL) as null_count
                FROM "{schema2}"."{table2}"
                LIMIT :limit
            """)
            result2 = conn.execute(query2, {"limit": sample_size}).fetchone()
            
            from_total = result1[0]
            from_distinct = result1[1]
            from_null = result1[2]
            from_uniqueness = from_distinct / from_total if from_total > 0 else 0.0
            
            to_total = result2[0]
            to_distinct = result2[1]
            to_null = result2[2]
            to_uniqueness = to_distinct / to_total if to_total > 0 else 0.0
            
            # Infer cardinality
            if from_uniqueness > 0.95 and to_uniqueness > 0.95:
                cardinality = "one_to_one"
            elif from_uniqueness > 0.95 and to_uniqueness < 0.95:
                cardinality = "one_to_many"
            elif from_uniqueness < 0.95 and to_uniqueness > 0.95:
                cardinality = "many_to_one"
            else:
                cardinality = "many_to_many"
            
            return CardinalityEvidence(
                from_total_rows=from_total,
                from_distinct_count=from_distinct,
                from_null_count=from_null,
                from_uniqueness=from_uniqueness,
                to_total_rows=to_total,
                to_distinct_count=to_distinct,
                to_null_count=to_null,
                to_uniqueness=to_uniqueness,
                inferred_cardinality=cardinality,
                sample_size=sample_size
            )
            
        except Exception as e:
            print(f"Error analyzing cardinality: {e}")
            return None
    
    @staticmethod
    def _analyze_value_overlap(
        conn: Connection,
        schema1: str,
        table1: str,
        column1: str,
        schema2: str,
        table2: str,
        column2: str,
        sample_size: int = 10000
    ) -> Optional[ValueOverlapEvidence]:
        """
        Analyze value overlap between two columns using sampling.
        
        Measures what percentage of values in column1 exist in column2.
        """
        try:
            # Get sample from first column (non-null values)
            query1 = text(f"""
                SELECT DISTINCT "{column1}" as value
                FROM "{schema1}"."{table1}"
                WHERE "{column1}" IS NOT NULL
                LIMIT :limit
            """)
            result1 = conn.execute(query1, {"limit": sample_size}).fetchall()
            sample1 = [str(row[0]) for row in result1]
            
            if not sample1:
                return None
            
            # Get sample from second column (non-null values)
            query2 = text(f"""
                SELECT DISTINCT "{column2}" as value
                FROM "{schema2}"."{table2}"
                WHERE "{column2}" IS NOT NULL
                LIMIT :limit
            """)
            result2 = conn.execute(query2, {"limit": sample_size}).fetchall()
            sample2 = set(str(row[0]) for row in result2)
            
            if not sample2:
                return None
            
            # Calculate overlap
            overlap = sum(1 for val in sample1 if val in sample2)
            overlap_pct = (overlap / len(sample1)) * 100.0 if sample1 else 0.0
            
            # Get null counts
            null_query1 = text(f"""
                SELECT COUNT(*) FILTER (WHERE "{column1}" IS NULL) as null_count
                FROM "{schema1}"."{table1}"
                LIMIT :limit
            """)
            null1 = conn.execute(null_query1, {"limit": sample_size}).scalar()
            
            null_query2 = text(f"""
                SELECT COUNT(*) FILTER (WHERE "{column2}" IS NULL) as null_count
                FROM "{schema2}"."{table2}"
                LIMIT :limit
            """)
            null2 = conn.execute(null_query2, {"limit": sample_size}).scalar()
            
            # Get example values
            examples = sample1[:5]
            
            return ValueOverlapEvidence(
                sample_size=min(sample_size, len(sample1) + len(sample2)),
                from_sample_size=len(sample1),
                to_sample_size=len(sample2),
                overlap_count=overlap,
                overlap_percentage=overlap_pct,
                from_null_count=null1 or 0,
                to_null_count=null2 or 0,
                examples=examples
            )
            
        except Exception as e:
            print(f"Error analyzing value overlap: {e}")
            return None
    
    @staticmethod
    def _generate_explanation(
        rel_type: RelationshipType,
        from_asset: str,
        to_asset: str,
        evidence: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable explanation from evidence.
        
        Example: "orders.customer_id likely references customers.id based on 
        name similarity, compatible types, and 94% value overlap on a 10k row sample."
        """
        parts = [f"{from_asset} {rel_type.value} {to_asset} based on"]
        
        reasons = []
        
        # Name similarity
        if 'name_similarity' in evidence and evidence['name_similarity']:
            sim = evidence['name_similarity']
            score = sim.get('similarity_score', 0)
            if score > 0.7:
                match_type = sim.get('match_type', 'similar')
                reasons.append(f"{match_type} name match ({score:.0%})")
        
        # Type compatibility
        if 'type_compatibility' in evidence and evidence['type_compatibility']:
            compat = evidence['type_compatibility']
            if compat.get('compatible'):
                reason = compat.get('compatibility_reason', 'compatible')
                reasons.append(f"{reason} types")
        
        # Value overlap
        if 'value_overlap' in evidence and evidence['value_overlap']:
            overlap = evidence['value_overlap']
            pct = overlap.get('overlap_percentage', 0)
            sample = overlap.get('sample_size', 0)
            if pct > 0:
                reasons.append(f"{pct:.0f}% value overlap on {sample:,} row sample")
        
        # Cardinality
        if 'cardinality' in evidence and evidence['cardinality']:
            card = evidence['cardinality']
            cardinality = card.get('inferred_cardinality', '')
            if cardinality:
                reasons.append(f"{cardinality.replace('_', '-')} cardinality")
        
        if reasons:
            return parts[0] + " " + ", ".join(reasons) + "."
        else:
            return f"{from_asset} {rel_type.value} {to_asset}."
    
    @staticmethod
    def discover_foreign_key_relationships(
        conn: Connection,
        database: str,
        schema: str,
        config: DiscoveryConfig
    ) -> List[DictionaryRelationshipCreate]:
        """
        Discover foreign-key-like relationships within a schema.
        
        Looks for:
        - Name patterns (table_id, tableId, etc.)
        - Type compatibility
        - Cardinality (many-to-one)
        - Value overlap
        """
        relationships = []
        
        # Get all tables and columns in schema
        query = text("""
            SELECT 
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = :schema
            ORDER BY table_name, ordinal_position
        """)
        
        result = conn.execute(query, {"schema": schema}).fetchall()
        
        # Build column index
        columns_by_table = {}
        all_columns = []
        
        for row in result:
            table_name, column_name, data_type = row
            if table_name not in columns_by_table:
                columns_by_table[table_name] = []
            
            col_info = {
                "table": table_name,
                "column": column_name,
                "type": data_type
            }
            columns_by_table[table_name].append(col_info)
            all_columns.append(col_info)
        
        # Look for FK-like relationships
        for from_col in all_columns:
            from_table = from_col["table"]
            from_column = from_col["column"]
            from_type = from_col["type"]
            
            # Skip if not an ID-like column
            if not any(pattern in from_column.lower() for pattern in ['_id', 'id', '_key', '_code']):
                continue
            
            # Look for matching PK candidates in other tables
            for to_table, to_cols in columns_by_table.items():
                if to_table == from_table:
                    continue  # Skip self-references for now
                
                for to_col in to_cols:
                    to_column = to_col["column"]
                    to_type = to_col["type"]
                    
                    # Check name similarity
                    sim_score, match_type = RelationshipDiscoveryService._calculate_name_similarity(
                        from_column, to_column
                    )
                    
                    if sim_score < config.name_similarity_threshold:
                        continue
                    
                    # Check type compatibility
                    compatible, compat_reason = RelationshipDiscoveryService._are_types_compatible(
                        from_type, to_type
                    )
                    
                    if not compatible:
                        continue
                    
                    # Analyze cardinality
                    cardinality_evidence = RelationshipDiscoveryService._analyze_cardinality(
                        conn, schema, from_table, from_column,
                        schema, to_table, to_column,
                        config.sample_size
                    )
                    
                    # Analyze value overlap
                    overlap_evidence = RelationshipDiscoveryService._analyze_value_overlap(
                        conn, schema, from_table, from_column,
                        schema, to_table, to_column,
                        config.sample_size
                    )
                    
                    # Calculate confidence
                    confidence = 0.0
                    signals = []
                    
                    # Name similarity weight: 30%
                    confidence += sim_score * 0.3
                    signals.append("name_similarity")
                    
                    # Type compatibility weight: 20%
                    confidence += 0.2
                    signals.append("type_compatibility")
                    
                    # Value overlap weight: 40%
                    if overlap_evidence and overlap_evidence.overlap_percentage >= config.min_overlap_percentage:
                        overlap_score = overlap_evidence.overlap_percentage / 100.0
                        confidence += overlap_score * 0.4
                        signals.append("value_overlap")
                    
                    # Cardinality weight: 10%
                    if cardinality_evidence:
                        if cardinality_evidence.inferred_cardinality == "many_to_one":
                            confidence += 0.1
                            signals.append("cardinality")
                    
                    # Only create relationship if meets minimum confidence
                    if confidence < config.min_confidence:
                        continue
                    
                    # Build evidence
                    evidence = RelationshipEvidence(
                        signals_fired=signals,
                        name_similarity=NameSimilarityEvidence(
                            normalized_from=RelationshipDiscoveryService._normalize_column_name(from_column),
                            normalized_to=RelationshipDiscoveryService._normalize_column_name(to_column),
                            similarity_score=sim_score,
                            match_type=match_type
                        ),
                        type_compatibility=TypeCompatibilityEvidence(
                            from_type=from_type,
                            to_type=to_type,
                            compatible=compatible,
                            compatibility_reason=compat_reason
                        ),
                        cardinality=cardinality_evidence,
                        value_overlap=overlap_evidence
                    )
                    
                    # Generate explanation
                    from_asset = f"{from_table}.{from_column}"
                    to_asset = f"{to_table}.{to_column}"
                    explanation = RelationshipDiscoveryService._generate_explanation(
                        RelationshipType.foreign_key_like,
                        from_asset,
                        to_asset,
                        evidence.model_dump()
                    )
                    
                    # Create relationship
                    rel = DictionaryRelationshipCreate(
                        from_asset_type=AssetType.column,
                        from_database=database,
                        from_schema=schema,
                        from_table=from_table,
                        from_column=from_column,
                        to_asset_type=AssetType.column,
                        to_database=database,
                        to_schema=schema,
                        to_table=to_table,
                        to_column=to_column,
                        relationship_type=RelationshipType.foreign_key_like,
                        confidence=confidence,
                        evidence=evidence.model_dump(),
                        explanation=explanation,
                        generated_by="system",
                        status=RelationshipStatus.suggested
                    )
                    
                    relationships.append(rel)
        
        return relationships


# ============================================================================
# Relationship CRUD Service
# ============================================================================

class RelationshipCRUDService:
    """Service for CRUD operations on relationships."""
    
    @staticmethod
    def create_relationship(conn: Connection, rel: DictionaryRelationshipCreate) -> DictionaryRelationship:
        """Create a new relationship."""
        rel_id = rel.id or f"rel_{uuid.uuid4().hex[:12]}"
        
        # Convert float confidence (0.0-1.0) to integer (0-10000) for storage
        confidence_int = int(rel.confidence * 10000)
        
        stmt = insert(dictionary_relationships).values(
            id=rel_id,
            from_asset_type=rel.from_asset_type.value,
            from_database=rel.from_database,
            from_schema=rel.from_schema,
            from_table=rel.from_table,
            from_column=rel.from_column,
            to_asset_type=rel.to_asset_type.value,
            to_database=rel.to_database,
            to_schema=rel.to_schema,
            to_table=rel.to_table,
            to_column=rel.to_column,
            relationship_type=rel.relationship_type.value,
            confidence=confidence_int,
            evidence=rel.evidence,
            explanation=rel.explanation,
            generated_by=rel.generated_by,
            status=rel.status.value
        )
        
        conn.execute(stmt)
        conn.commit()
        
        return RelationshipCRUDService.get_relationship(conn, rel_id)
    
    @staticmethod
    def get_relationship(conn: Connection, rel_id: str) -> Optional[DictionaryRelationship]:
        """Get a relationship by ID."""
        stmt = select(dictionary_relationships).where(dictionary_relationships.c.id == rel_id)
        result = conn.execute(stmt).first()
        
        if not result:
            return None
        
        # Convert integer confidence (0-10000) back to float (0.0-1.0)
        data = dict(result._mapping)
        data['confidence'] = data['confidence'] / 10000.0
        
        return DictionaryRelationship(**data)
    
    @staticmethod
    def list_relationships(
        conn: Connection,
        status: Optional[RelationshipStatus] = None,
        relationship_type: Optional[RelationshipType] = None,
        min_confidence: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DictionaryRelationship], int]:
        """List relationships with filters."""
        stmt = select(dictionary_relationships)
        count_stmt = select(dictionary_relationships)
        
        filters = []
        if status:
            filters.append(dictionary_relationships.c.status == status.value)
        if relationship_type:
            filters.append(dictionary_relationships.c.relationship_type == relationship_type.value)
        if min_confidence is not None:
            # Convert float to integer for DB comparison
            min_confidence_int = int(min_confidence * 10000)
            filters.append(dictionary_relationships.c.confidence >= min_confidence_int)
        
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        
        # Get total count
        from sqlalchemy import func
        total = conn.execute(select(func.count()).select_from(count_stmt.subquery())).scalar()
        
        # Get page
        stmt = stmt.offset(skip).limit(limit).order_by(dictionary_relationships.c.confidence.desc())
        results = conn.execute(stmt).fetchall()
        
        # Convert integer confidence back to float for each result
        relationships = []
        for row in results:
            data = dict(row._mapping)
            data['confidence'] = data['confidence'] / 10000.0
            relationships.append(DictionaryRelationship(**data))
        
        return relationships, total or 0
    
    @staticmethod
    def get_asset_relationships(
        conn: Connection,
        database: str,
        schema: str,
        table: str,
        column: Optional[str] = None
    ) -> Tuple[List[DictionaryRelationship], List[DictionaryRelationship]]:
        """Get incoming and outgoing relationships for an asset."""
        # Outgoing relationships (from this asset)
        outgoing_filters = [
            dictionary_relationships.c.from_database == database,
            dictionary_relationships.c.from_schema == schema,
            dictionary_relationships.c.from_table == table
        ]
        if column:
            outgoing_filters.append(dictionary_relationships.c.from_column == column)
        
        outgoing_stmt = select(dictionary_relationships).where(and_(*outgoing_filters))
        outgoing_results = conn.execute(outgoing_stmt).fetchall()
        outgoing = []
        for row in outgoing_results:
            data = dict(row._mapping)
            data['confidence'] = data['confidence'] / 10000.0
            outgoing.append(DictionaryRelationship(**data))
        
        # Incoming relationships (to this asset)
        incoming_filters = [
            dictionary_relationships.c.to_database == database,
            dictionary_relationships.c.to_schema == schema,
            dictionary_relationships.c.to_table == table
        ]
        if column:
            incoming_filters.append(dictionary_relationships.c.to_column == column)
        
        incoming_stmt = select(dictionary_relationships).where(and_(*incoming_filters))
        incoming_results = conn.execute(incoming_stmt).fetchall()
        incoming = []
        for row in incoming_results:
            data = dict(row._mapping)
            data['confidence'] = data['confidence'] / 10000.0
            incoming.append(DictionaryRelationship(**data))
        
        return incoming, outgoing
    
    @staticmethod
    def accept_relationship(
        conn: Connection,
        rel_id: str,
        reviewed_by: Optional[str] = None
    ) -> Optional[DictionaryRelationship]:
        """Accept a relationship."""
        stmt = update(dictionary_relationships).where(
            dictionary_relationships.c.id == rel_id
        ).values(
            status=RelationshipStatus.accepted.value,
            reviewed_by=reviewed_by,
            reviewed_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        conn.execute(stmt)
        conn.commit()
        
        return RelationshipCRUDService.get_relationship(conn, rel_id)
    
    @staticmethod
    def reject_relationship(
        conn: Connection,
        rel_id: str,
        reviewed_by: Optional[str] = None
    ) -> Optional[DictionaryRelationship]:
        """Reject a relationship."""
        stmt = update(dictionary_relationships).where(
            dictionary_relationships.c.id == rel_id
        ).values(
            status=RelationshipStatus.rejected.value,
            reviewed_by=reviewed_by,
            reviewed_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        conn.execute(stmt)
        conn.commit()
        
        return RelationshipCRUDService.get_relationship(conn, rel_id)
    
    @staticmethod
    def delete_relationship(conn: Connection, rel_id: str) -> bool:
        """Delete a relationship."""
        stmt = sql_delete(dictionary_relationships).where(dictionary_relationships.c.id == rel_id)
        result = conn.execute(stmt)
        conn.commit()
        
        return result.rowcount > 0

