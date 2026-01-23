"""
Data Lineage API Router

Endpoints for querying and managing data lineage.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session
from pydantic import BaseModel

from db_session import get_session
from .service import LineageService
from .auto_tracker import AutoLineageTracker
from .models import (
    EntityType,
    EdgeType,
    LineageGraphResponse,
    LineageSummary,
    CreateLineageRequest,
    LineageImpactAnalysis,
    LineageQueryRequest,
)


router = APIRouter(prefix="/api/v1/lineage", tags=["lineage"])


class ParseSQLRequest(BaseModel):
    """Request to parse SQL query"""
    sql: str


class TrackQueryRequest(BaseModel):
    """Request to track query execution"""
    sql: str
    result_dataset_id: Optional[UUID] = None
    result_dataset_name: Optional[str] = None
    result_row_count: Optional[int] = None
    execution_time_ms: Optional[float] = None


def get_lineage_service(session: Session = Depends(get_session)) -> LineageService:
    """Dependency injection for LineageService"""
    return LineageService(db=session)


def get_auto_tracker(service: LineageService = Depends(get_lineage_service)) -> AutoLineageTracker:
    """Dependency injection for AutoLineageTracker"""
    return AutoLineageTracker(lineage_service=service)


# ========================================
# Lineage Query Endpoints
# ========================================

@router.get("/{entity_type}/{entity_id}", response_model=LineageGraphResponse)
async def get_lineage(
    entity_type: EntityType,
    entity_id: UUID,
    direction: str = Query(default="both", regex="^(upstream|downstream|both)$"),
    max_depth: int = Query(default=3, ge=1, le=10),
    include_columns: bool = Query(default=False),
    service: LineageService = Depends(get_lineage_service),
):
    """
    Get complete lineage graph for an entity.
    
    - **entity_type**: Type of entity (file, file_table, dataset, etc.)
    - **entity_id**: UUID of the entity
    - **direction**: upstream, downstream, or both
    - **max_depth**: Maximum depth to traverse (1-10)
    - **include_columns**: Whether to include column-level lineage
    """
    try:
        lineage = service.get_lineage_graph(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth,
            direction=direction,
            include_columns=include_columns,
        )
        return lineage
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


@router.get("/{entity_type}/{entity_id}/summary", response_model=LineageSummary)
async def get_lineage_summary(
    entity_type: EntityType,
    entity_id: UUID,
    service: LineageService = Depends(get_lineage_service),
):
    """
    Get quick summary of lineage for an entity.
    
    Returns counts and names of immediate upstream/downstream entities.
    """
    try:
        summary = service.get_lineage_summary(
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/{entity_type}/{entity_id}/upstream", response_model=LineageGraphResponse)
async def get_upstream_lineage(
    entity_type: EntityType,
    entity_id: UUID,
    max_depth: int = Query(default=3, ge=1, le=10),
    service: LineageService = Depends(get_lineage_service),
):
    """Get only upstream (source) lineage."""
    try:
        lineage = service.get_lineage_graph(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth,
            direction="upstream",
        )
        return lineage
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get upstream lineage: {str(e)}")


@router.get("/{entity_type}/{entity_id}/downstream", response_model=LineageGraphResponse)
async def get_downstream_lineage(
    entity_type: EntityType,
    entity_id: UUID,
    max_depth: int = Query(default=3, ge=1, le=10),
    service: LineageService = Depends(get_lineage_service),
):
    """Get only downstream (derived) lineage."""
    try:
        lineage = service.get_lineage_graph(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth,
            direction="downstream",
        )
        return lineage
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get downstream lineage: {str(e)}")


@router.get("/{entity_type}/{entity_id}/impact", response_model=LineageImpactAnalysis)
async def analyze_impact(
    entity_type: EntityType,
    entity_id: UUID,
    service: LineageService = Depends(get_lineage_service),
):
    """
    Analyze the impact of changes to this entity.
    
    Returns all downstream entities that would be affected.
    """
    try:
        impact = service.analyze_impact(
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return impact
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze impact: {str(e)}")


# ========================================
# Lineage Creation Endpoints
# ========================================

@router.post("/track", response_model=dict)
async def track_lineage(
    request: CreateLineageRequest,
    service: LineageService = Depends(get_lineage_service),
):
    """
    Track a new lineage relationship between two entities.
    
    Use this endpoint when creating derived datasets, publishing files, etc.
    """
    try:
        edge = service.track_lineage(
            source_type=request.source_type,
            source_id=request.source_id,
            source_name=request.source_name,
            target_type=request.target_type,
            target_id=request.target_id,
            target_name=request.target_name,
            edge_type=request.edge_type,
            transform_sql=request.transform_sql,
            transform_config=request.transform_config,
            source_row_count=request.source_row_count,
            target_row_count=request.target_row_count,
            source_column_count=request.source_column_count,
            target_column_count=request.target_column_count,
            column_mappings=request.column_mappings,
        )
        return {
            "success": True,
            "edge_id": str(edge.id),
            "message": "Lineage tracked successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track lineage: {str(e)}")


@router.delete("/{entity_type}/{entity_id}")
async def delete_lineage(
    entity_type: EntityType,
    entity_id: UUID,
    service: LineageService = Depends(get_lineage_service),
):
    """
    Delete all lineage for an entity.
    
    Use with caution - this removes all upstream and downstream relationships.
    """
    try:
        service.delete_lineage(entity_type=entity_type, entity_id=entity_id)
        return {
            "success": True,
            "message": f"Lineage deleted for {entity_type}:{entity_id}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete lineage: {str(e)}")


# ========================================
# SQL Query Lineage Endpoints
# ========================================

@router.post("/parse-sql")
async def parse_sql_query(
    request: ParseSQLRequest,
    tracker: AutoLineageTracker = Depends(get_auto_tracker),
):
    """
    Parse SQL query and preview lineage without tracking.
    
    Returns information about:
    - Source tables that will be read
    - Target table (if INSERT/CREATE)
    - Columns used
    - Transformations applied (JOIN, aggregation, filter)
    
    Use this before executing a query to understand its lineage impact.
    """
    try:
        lineage_info = tracker.parse_query_preview(request.sql)
        return {
            "success": True,
            "lineage": lineage_info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse SQL: {str(e)}")


@router.post("/track-query")
async def track_query_execution(
    request: TrackQueryRequest,
    tracker: AutoLineageTracker = Depends(get_auto_tracker),
):
    """
    Track lineage from a SQL query execution.
    
    Call this after executing a query to automatically create lineage relationships.
    
    The tracker will:
    - Parse the SQL to find source tables
    - Create lineage edges from each source to the result
    - Detect transformation types (JOIN, aggregation, filter)
    - Store the SQL and metadata
    """
    try:
        result = tracker.track_query_execution(
            sql=request.sql,
            result_dataset_id=request.result_dataset_id,
            result_dataset_name=request.result_dataset_name,
            result_row_count=request.result_row_count,
            execution_time_ms=request.execution_time_ms,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track query: {str(e)}")


# ========================================
# Advanced Lineage Features
# ========================================

@router.post("/parse-sql/column-level")
async def parse_column_lineage(request: ParseSQLRequest):
    """
    Extract column-level lineage from SQL query.
    
    Shows how individual columns transform through the query:
    - Direct mappings (sales.amount -> result.amount)
    - Aggregations (SUM(amount) -> total_sales)
    - Functions (UPPER(name) -> name_upper)
    - Calculated fields (price * quantity -> total)
    
    Returns detailed transformation information for each column.
    """
    try:
        from .column_lineage import extract_column_lineage
        
        lineage = extract_column_lineage(request.sql)
        
        return {
            'success': True,
            'transformations': [
                {
                    'source': t.source_full_name,
                    'target': t.target_column,
                    'type': t.transformation_type,
                    'function': t.function_used,
                    'sql': t.transformation_sql,
                    'label': t.lineage_edge_label
                }
                for t in lineage.transformations
            ],
            'unmapped_columns': lineage.unmapped_columns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse column lineage: {str(e)}")


@router.post("/analyze-ml-query")
async def analyze_ml_query(request: ParseSQLRequest):
    """
    Analyze if a query is ML-related and extract ML metadata.
    
    Automatically detects:
    - Feature extraction queries
    - Training data preparation
    - Model inference data sources
    - Statistical transformations
    - Train/test split patterns
    
    Returns ML features, confidence score, and detected patterns.
    """
    try:
        from .ml_tracker import analyze_ml_query
        
        result = analyze_ml_query(request.sql)
        
        if not result:
            return {
                'is_ml_related': False,
                'confidence': 0.0,
                'message': 'Query does not appear to be ML-related'
            }
        
        return {
            'is_ml_related': True,
            'confidence': result.confidence_score,
            'query_type': result.query_type,
            'features': [
                {
                    'name': f.feature_name,
                    'type': f.feature_type,
                    'source_table': f.source_table,
                    'source_column': f.source_column,
                    'transformation': f.transformation
                }
                for f in result.features_extracted
            ],
            'source_tables': result.source_tables,
            'target_dataset': result.target_dataset,
            'detected_patterns': result.detected_patterns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze ML query: {str(e)}")


@router.get("/pipelines")
async def discover_pipelines(
    min_stages: int = Query(default=3, ge=2, description="Minimum pipeline stages"),
    time_window_hours: Optional[int] = Query(default=24, description="Time window in hours"),
    service: LineageService = Depends(get_lineage_service),
):
    """
    Discover data pipelines (chains of connected queries).
    
    Finds sequences like:
    - raw_data -> cleaned_data -> aggregated_data -> report
    
    Useful for understanding data flows and dependencies.
    """
    try:
        from .cross_query_tracker import CrossQueryTracker
        from db_session import get_session
        
        session = next(get_session())
        try:
            tracker = CrossQueryTracker(db=session)
            pipelines = tracker.discover_pipelines(
                min_stages=min_stages,
                time_window_hours=time_window_hours
            )
            
            return {
                'success': True,
                'pipelines_found': len(pipelines),
                'pipelines': [
                    {
                        'pipeline_id': p.pipeline_id,
                        'name': p.name,
                        'stages': p.stages,
                        'source_tables': p.source_tables,
                        'target_tables': p.target_tables,
                        'last_run': p.last_run.isoformat() if p.last_run else None
                    }
                    for p in pipelines
                ]
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover pipelines: {str(e)}")


@router.get("/query-chains/{table_name}")
async def find_query_chains(
    table_name: str,
    max_depth: int = Query(default=10, ge=1, le=20, description="Maximum chain depth"),
    time_window_hours: Optional[int] = Query(default=None, description="Time window in hours"),
    service: LineageService = Depends(get_lineage_service),
):
    """
    Find chains of queries starting from a table.
    
    Shows how data flows through multiple transformations:
    - table_a -> table_b -> table_c -> final_table
    
    Useful for impact analysis and debugging data issues.
    """
    try:
        from .cross_query_tracker import CrossQueryTracker
        from db_session import get_session
        
        session = next(get_session())
        try:
            tracker = CrossQueryTracker(db=session)
            chains = tracker.find_query_chains(
                starting_table=table_name,
                max_depth=max_depth,
                time_window_hours=time_window_hours
            )
            
            return {
                'success': True,
                'starting_table': table_name,
                'chains_found': len(chains),
                'chains': [
                    {
                        'chain_id': chain.chain_id,
                        'tables': chain.tables_involved,
                        'start_table': chain.start_table,
                        'end_table': chain.end_table,
                        'transformations': chain.total_transformations,
                        'created_at': chain.created_at.isoformat()
                    }
                    for chain in chains
                ]
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find query chains: {str(e)}")


# ========================================
# SQL Parser Endpoints
# ========================================

@router.post("/parse-sql")
async def parse_sql_query(
    sql: str = Query(..., description="SQL query to parse"),
):
    """
    Parse SQL query and extract lineage information.
    
    Returns:
    - source_tables: List of tables referenced in query
    - target_columns: List of output columns
    - transformations: Types of transformations (JOIN, WHERE, etc.)
    - column_mappings: Column-level dependencies
    - joins: JOIN clauses details
    """
    from .sql_parser import parse_sql_for_lineage
    
    try:
        lineage = parse_sql_for_lineage(sql)
        return {
            "success": True,
            "lineage": lineage,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse SQL: {str(e)}"
        )


@router.post("/track-from-sql")
async def track_lineage_from_sql(
    sql: str,
    target_table: str,
    target_schema: Optional[str] = None,
    target_id: Optional[UUID] = None,
    service: LineageService = Depends(get_lineage_service),
):
    """
    Parse SQL query and automatically create lineage relationships.
    
    This endpoint:
    1. Parses the SQL query
    2. Extracts source tables
    3. Creates lineage edges from sources → target
    4. Tracks column-level mappings
    
    Perfect for automatic lineage tracking when queries are executed.
    """
    from .sql_parser import create_lineage_from_query
    
    try:
        # Parse SQL and get lineage edges
        lineage_data = create_lineage_from_query(sql, target_table, target_schema)
        
        created_edges = []
        for edge_data in lineage_data['edges']:
            # Create lineage edge
            edge = service.track_lineage(
                source_type=EntityType.DATABASE_TABLE,
                source_id=target_id or UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                source_name=f"{edge_data['source_schema']}.{edge_data['source_table']}" if edge_data['source_schema'] else edge_data['source_table'],
                target_type=EntityType.DATABASE_TABLE,
                target_id=target_id or UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                target_name=f"{target_schema}.{target_table}" if target_schema else target_table,
                edge_type=EdgeType(edge_data['edge_type']),
                transform_sql=sql,
                column_mappings=edge_data.get('column_mappings'),
            )
            created_edges.append(str(edge.id))
        
        return {
            "success": True,
            "message": f"Created {len(created_edges)} lineage edges",
            "edge_ids": created_edges,
            "source_tables": lineage_data.get('source_count', 0),
            "transformations": lineage_data.get('transformations', []),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track lineage from SQL: {str(e)}"
        )
