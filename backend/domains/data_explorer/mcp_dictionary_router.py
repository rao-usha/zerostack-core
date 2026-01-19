"""
Backend API router for MCP Dictionary operations.

Provides additional endpoints optimized for MCP tool usage,
supplementing the existing data dictionary endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field
from sqlmodel import Session, select, func, or_, and_

from db_session import get_session
from .dictionary_enhanced_models import (
    DictionaryAsset,
    DictionaryField,
    DictionaryProfile,
)
from .dictionary_semantics_models import DictionaryRelationship
from . import dictionary_enhanced_service as service

router = APIRouter(prefix="/mcp/dictionary", tags=["MCP Dictionary"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SearchResult(BaseModel):
    """A single search result."""
    match_type: str  # table, column, definition
    schema_name: str
    table_name: str
    column_name: Optional[str] = None
    business_name: Optional[str] = None
    description: Optional[str] = None
    relevance: str  # high, medium, low
    

class SearchResponse(BaseModel):
    """Search results response."""
    query: str
    results: List[SearchResult]
    total: int


class JoinAnalysis(BaseModel):
    """Join analysis result."""
    can_join: bool
    join_type: Optional[str] = None  # direct, indirect, none
    left_table: str
    right_table: str
    join_columns: Optional[Dict[str, str]] = None
    cardinality: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    example_sql: Optional[str] = None
    path: Optional[List[str]] = None  # For indirect joins


class CurationStats(BaseModel):
    """Curation statistics."""
    total_assets: int
    documented_assets: int
    documentation_coverage: float
    total_relationships: int
    approved_relationships: int
    pending_relationships: int
    total_fields: int
    documented_fields: int


class TrustSummary(BaseModel):
    """Trust tier summary."""
    tier: str
    count: int
    percentage: float


class QualityOverview(BaseModel):
    """Quality overview for the dictionary."""
    trust_distribution: List[TrustSummary]
    approved_for_reporting: int
    approved_for_ml: int
    assets_with_issues: int


# =============================================================================
# SEARCH ENDPOINT
# =============================================================================

@router.get("/search", response_model=SearchResponse)
def search_dictionary(
    query: str = QueryParam(..., min_length=1),
    connection_id: str = QueryParam("default"),
    scope: str = QueryParam("all", description="Search scope: all, tables, columns, definitions"),
    schema: Optional[str] = QueryParam(None),
    limit: int = QueryParam(20, le=100),
    session: Session = Depends(get_session)
):
    """
    Search the data dictionary with natural language queries.
    
    Searches across table names, column names, business names, and definitions.
    Returns ranked results with match context.
    """
    results = []
    search_pattern = f"%{query}%"
    
    # Search tables/assets
    if scope in ("all", "tables", "definitions"):
        asset_query = select(DictionaryAsset).where(
            DictionaryAsset.connection_id == connection_id
        )
        
        if schema:
            asset_query = asset_query.where(DictionaryAsset.schema_name == schema)
        
        asset_query = asset_query.where(
            or_(
                DictionaryAsset.table_name.ilike(search_pattern),
                DictionaryAsset.business_name.ilike(search_pattern),
                DictionaryAsset.business_definition.ilike(search_pattern),
                DictionaryAsset.business_domain.ilike(search_pattern)
            )
        ).limit(limit)
        
        assets = session.exec(asset_query).all()
        
        for asset in assets:
            # Determine match type and relevance
            match_type = "table"
            relevance = "medium"
            
            if query.lower() in (asset.table_name or "").lower():
                relevance = "high"
            elif query.lower() in (asset.business_name or "").lower():
                relevance = "high"
            elif query.lower() in (asset.business_definition or "").lower():
                match_type = "definition"
            
            results.append(SearchResult(
                match_type=match_type,
                schema_name=asset.schema_name,
                table_name=asset.table_name,
                business_name=asset.business_name,
                description=asset.business_definition[:200] if asset.business_definition else None,
                relevance=relevance
            ))
    
    # Search columns/fields
    if scope in ("all", "columns"):
        # Join with assets to get schema/table info
        field_query = (
            select(DictionaryField, DictionaryAsset)
            .join(DictionaryAsset, DictionaryField.asset_id == DictionaryAsset.id)
            .where(DictionaryAsset.connection_id == connection_id)
        )
        
        if schema:
            field_query = field_query.where(DictionaryAsset.schema_name == schema)
        
        field_query = field_query.where(
            or_(
                DictionaryField.column_name.ilike(search_pattern),
                DictionaryField.business_name.ilike(search_pattern),
                DictionaryField.business_definition.ilike(search_pattern)
            )
        ).limit(limit)
        
        field_results = session.exec(field_query).all()
        
        for field, asset in field_results:
            relevance = "high" if query.lower() in (field.column_name or "").lower() else "medium"
            
            results.append(SearchResult(
                match_type="column",
                schema_name=asset.schema_name,
                table_name=asset.table_name,
                column_name=field.column_name,
                business_name=field.business_name,
                description=field.business_definition[:200] if field.business_definition else None,
                relevance=relevance
            ))
    
    # Sort by relevance
    relevance_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda x: relevance_order.get(x.relevance, 2))
    
    return SearchResponse(
        query=query,
        results=results[:limit],
        total=len(results)
    )


# =============================================================================
# JOIN ANALYSIS ENDPOINT
# =============================================================================

@router.get("/analyze-join", response_model=JoinAnalysis)
def analyze_join(
    left_schema: str = QueryParam(...),
    left_table: str = QueryParam(...),
    right_schema: str = QueryParam(...),
    right_table: str = QueryParam(...),
    connection_id: str = QueryParam("default"),
    session: Session = Depends(get_session)
):
    """
    Analyze if and how two tables can be joined.
    
    Checks for direct relationships, suggests join columns,
    and warns about potential issues like fanout.
    """
    # Get relationships for left table using enhanced service
    try:
        left_rels = service.get_relationships_for_table(
            session, connection_id, left_schema, left_table
        )
    except Exception:
        left_rels = []
    
    # Find direct relationship
    direct_rel = None
    for rel in left_rels:
        if (rel.target_schema == right_schema and rel.target_table == right_table):
            direct_rel = rel
            break
        if (rel.source_schema == right_schema and rel.source_table == right_table):
            direct_rel = rel
            break
    
    if direct_rel:
        # Direct join found
        warnings = []
        
        # Determine cardinality warnings
        cardinality = direct_rel.cardinality
        if cardinality == "one_to_many":
            warnings.append(
                "1:N relationship - aggregations on the 'one' side may be affected by fanout"
            )
        elif cardinality == "many_to_many":
            warnings.append(
                "N:M relationship - use with caution, consider aggregating first"
            )
        
        # Build example SQL
        if direct_rel.source_schema == left_schema and direct_rel.source_table == left_table:
            left_col = direct_rel.source_column
            right_col = direct_rel.target_column
        else:
            left_col = direct_rel.target_column
            right_col = direct_rel.source_column
        
        example_sql = f"""SELECT *
FROM {left_schema}.{left_table} l
LEFT JOIN {right_schema}.{right_table} r
  ON l.{left_col} = r.{right_col}"""
        
        return JoinAnalysis(
            can_join=True,
            join_type="direct",
            left_table=f"{left_schema}.{left_table}",
            right_table=f"{right_schema}.{right_table}",
            join_columns={"left": left_col, "right": right_col},
            cardinality=cardinality,
            warnings=warnings,
            example_sql=example_sql
        )
    
    # No direct relationship - check for indirect paths
    # Simple BFS to find path (max 2 hops)
    visited = {f"{left_schema}.{left_table}"}
    queue = [(left_schema, left_table, [])]
    
    while queue:
        current_schema, current_table, path = queue.pop(0)
        
        if len(path) >= 2:
            continue
        
        try:
            rels = service.get_relationships_for_table(
                session, connection_id, current_schema, current_table
            )
        except Exception:
            rels = []
        
        for rel in rels:
            # Get the "other" table
            if rel.source_schema == current_schema and rel.source_table == current_table:
                next_schema, next_table = rel.target_schema, rel.target_table
            else:
                next_schema, next_table = rel.source_schema, rel.source_table
            
            next_key = f"{next_schema}.{next_table}"
            
            if next_key in visited:
                continue
            
            new_path = path + [f"{current_schema}.{current_table}"]
            
            if next_schema == right_schema and next_table == right_table:
                # Found path!
                full_path = new_path + [next_key]
                return JoinAnalysis(
                    can_join=True,
                    join_type="indirect",
                    left_table=f"{left_schema}.{left_table}",
                    right_table=f"{right_schema}.{right_table}",
                    path=full_path,
                    warnings=[
                        f"Indirect join through {len(full_path) - 1} intermediate table(s)",
                        "Verify grain compatibility before aggregating"
                    ]
                )
            
            visited.add(next_key)
            queue.append((next_schema, next_table, new_path))
    
    # No path found
    return JoinAnalysis(
        can_join=False,
        join_type="none",
        left_table=f"{left_schema}.{left_table}",
        right_table=f"{right_schema}.{right_table}",
        warnings=["No relationship path found between these tables"]
    )


# =============================================================================
# CURATION STATISTICS ENDPOINT
# =============================================================================

@router.get("/curation-stats", response_model=CurationStats)
def get_curation_stats(
    connection_id: str = QueryParam("default"),
    schema: Optional[str] = QueryParam(None),
    session: Session = Depends(get_session)
):
    """
    Get curation statistics for the data dictionary.
    
    Returns counts and percentages for documentation coverage,
    relationship approval status, and field coverage.
    """
    # Count assets
    asset_query = select(DictionaryAsset).where(
        DictionaryAsset.connection_id == connection_id
    )
    if schema:
        asset_query = asset_query.where(DictionaryAsset.schema_name == schema)
    
    assets = list(session.exec(asset_query).all())
    total_assets = len(assets)
    documented_assets = sum(1 for a in assets if a.business_definition)
    
    # Count fields
    if assets:
        asset_ids = [a.id for a in assets]
        field_query = select(DictionaryField).where(
            DictionaryField.asset_id.in_(asset_ids)
        )
        fields = list(session.exec(field_query).all())
        total_fields = len(fields)
        documented_fields = sum(1 for f in fields if f.business_definition)
    else:
        total_fields = 0
        documented_fields = 0
    
    # Count relationships (DictionaryRelationship uses status field)
    rel_query = select(DictionaryRelationship)
    relationships = list(session.exec(rel_query).all())
    total_rels = len(relationships)
    
    # Count by status
    approved_rels = sum(1 for r in relationships if r.status == "approved")
    pending_rels = sum(1 for r in relationships if r.status == "suggested")
    
    return CurationStats(
        total_assets=total_assets,
        documented_assets=documented_assets,
        documentation_coverage=round(documented_assets / total_assets * 100, 1) if total_assets > 0 else 0,
        total_relationships=total_rels,
        approved_relationships=approved_rels,
        pending_relationships=pending_rels,
        total_fields=total_fields,
        documented_fields=documented_fields
    )


# =============================================================================
# QUALITY OVERVIEW ENDPOINT
# =============================================================================

@router.get("/quality-overview", response_model=QualityOverview)
def get_quality_overview(
    connection_id: str = QueryParam("default"),
    schema: Optional[str] = QueryParam(None),
    session: Session = Depends(get_session)
):
    """
    Get quality overview for the data dictionary.
    
    Returns trust tier distribution, approval counts, and issue summary.
    """
    # Get assets
    asset_query = select(DictionaryAsset).where(
        DictionaryAsset.connection_id == connection_id
    )
    if schema:
        asset_query = asset_query.where(DictionaryAsset.schema_name == schema)
    
    assets = list(session.exec(asset_query).all())
    total = len(assets)
    
    if total == 0:
        return QualityOverview(
            trust_distribution=[],
            approved_for_reporting=0,
            approved_for_ml=0,
            assets_with_issues=0
        )
    
    # Count by trust tier
    tier_counts = {}
    for asset in assets:
        tier = asset.trust_tier or "experimental"
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    trust_distribution = [
        TrustSummary(
            tier=tier,
            count=count,
            percentage=round(count / total * 100, 1)
        )
        for tier, count in sorted(tier_counts.items())
    ]
    
    # Count approvals
    approved_reporting = sum(1 for a in assets if a.approved_for_reporting)
    approved_ml = sum(1 for a in assets if a.approved_for_ml)
    
    # Count issues
    with_issues = sum(1 for a in assets if a.known_issues)
    
    return QualityOverview(
        trust_distribution=trust_distribution,
        approved_for_reporting=approved_reporting,
        approved_for_ml=approved_ml,
        assets_with_issues=with_issues
    )


# =============================================================================
# CONTEXT BLOB FOR LLM (Enhanced)
# =============================================================================

@router.get("/context/{schema}/{table}")
def get_llm_context(
    schema: str,
    table: str,
    connection_id: str = QueryParam("default"),
    depth: str = QueryParam("standard", description="Context depth: minimal, standard, comprehensive"),
    session: Session = Depends(get_session)
):
    """
    Get comprehensive context for LLM grounding.
    
    Returns a structured context blob optimized for LLM consumption,
    with configurable depth.
    """
    # Get base context from existing service
    context = service.get_dictionary_context(
        session=session,
        connection_id=connection_id,
        schema_name=schema,
        table_name=table
    )
    
    if "error" in context:
        raise HTTPException(status_code=404, detail=context["error"])
    
    # Get full asset for additional fields
    asset = service.get_asset_by_table(session, connection_id, schema, table)
    
    if depth == "minimal":
        # Strip down to essentials
        return {
            "table": context["table"]["name"],
            "business_name": context["table"].get("business_name"),
            "grain": context["table"].get("grain"),
            "trust_tier": context["table"].get("trust_tier"),
            "column_count": len(context.get("columns", [])),
            "relationship_count": len(context.get("relationships", []))
        }
    
    elif depth == "comprehensive":
        # Add everything we have
        context["ownership"] = {
            "owner": asset.owner if asset else None,
            "steward": asset.steward if asset else None,
            "domain": asset.business_domain if asset else None
        }
        context["quality"] = {
            "trust_tier": asset.trust_tier if asset else None,
            "trust_score": asset.trust_score if asset else None,
            "approved_for_reporting": asset.approved_for_reporting if asset else False,
            "approved_for_ml": asset.approved_for_ml if asset else False,
            "known_issues": asset.known_issues if asset else None,
            "issue_tags": asset.issue_tags if asset else []
        }
        context["usage"] = {
            "query_count_30d": asset.query_count_30d if asset else 0,
            "last_queried_at": str(asset.last_queried_at) if asset and asset.last_queried_at else None
        }
    
    return context
