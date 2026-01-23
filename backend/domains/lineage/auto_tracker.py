"""
Automatic Lineage Tracking from SQL Queries

Integrates SQL parser with lineage tracking service to automatically
create lineage relationships when queries are executed.
"""
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from .sql_parser import SQLLineageParser, QueryLineage, TableReference
from .service import LineageService
from .models import EntityType, EdgeType


class AutoLineageTracker:
    """
    Automatically tracks lineage from SQL query execution.
    
    Usage:
        tracker = AutoLineageTracker(lineage_service)
        tracker.track_query_execution(
            sql="SELECT * FROM sales JOIN customers ...",
            result_dataset_id=dataset_id,
            result_dataset_name="sales_analysis",
            result_row_count=1000
        )
    """
    
    def __init__(self, lineage_service: LineageService):
        self.lineage_service = lineage_service
        self.parser = SQLLineageParser()
    
    def track_query_execution(
        self,
        sql: str,
        result_dataset_id: Optional[UUID] = None,
        result_dataset_name: Optional[str] = None,
        result_row_count: Optional[int] = None,
        executed_by: Optional[UUID] = None,
        execution_time_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Track lineage from a SQL query execution.
        
        Args:
            sql: The SQL query that was executed
            result_dataset_id: UUID of the result dataset (if saved)
            result_dataset_name: Name of the result dataset
            result_row_count: Number of rows in result
            executed_by: User who executed the query
            execution_time_ms: Query execution time
            
        Returns:
            Dictionary with tracking results
        """
        # Parse SQL to extract lineage
        lineage = self.parser.parse(sql)
        
        # If no result dataset ID, generate one for tracking
        if not result_dataset_id:
            result_dataset_id = uuid4()
        
        if not result_dataset_name:
            result_dataset_name = f"query_result_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Track each source table -> result
        edges_created = []
        for source_table in lineage.source_tables:
            try:
                # Determine edge type based on query transformations
                edge_type = self._determine_edge_type(lineage)
                
                # Create lineage relationship
                edge = self.lineage_service.track_lineage(
                    source_type=EntityType.DATABASE_TABLE,
                    source_id=uuid4(),  # TODO: Look up actual table ID from DB
                    source_name=source_table.full_name,
                    target_type=EntityType.DATASET if not lineage.target_table else EntityType.DATABASE_TABLE,
                    target_id=result_dataset_id,
                    target_name=result_dataset_name,
                    edge_type=edge_type,
                    transform_sql=sql[:5000],  # Limit SQL length
                    transform_config={
                        'query_type': lineage.query_type,
                        'join_type': lineage.join_type,
                        'has_aggregation': lineage.has_aggregation,
                        'has_filter': lineage.has_filter,
                        'execution_time_ms': execution_time_ms,
                    },
                    target_row_count=result_row_count,
                    created_by=executed_by,
                )
                edges_created.append({
                    'edge_id': str(edge.id),
                    'source': source_table.full_name,
                    'target': result_dataset_name,
                    'edge_type': edge_type,
                })
            except Exception as e:
                print(f"Warning: Failed to track lineage for {source_table.full_name}: {e}")
                continue
        
        return {
            'success': True,
            'query_type': lineage.query_type,
            'source_tables': [t.full_name for t in lineage.source_tables],
            'target_table': lineage.target_table.full_name if lineage.target_table else None,
            'edges_created': edges_created,
            'has_aggregation': lineage.has_aggregation,
            'has_filter': lineage.has_filter,
            'join_type': lineage.join_type,
        }
    
    def _determine_edge_type(self, lineage: QueryLineage) -> EdgeType:
        """Determine the appropriate edge type based on query characteristics"""
        if lineage.query_type == 'INSERT' or lineage.query_type == 'CREATE':
            return EdgeType.DERIVED_FROM
        
        if lineage.join_type:
            return EdgeType.JOINED
        
        if lineage.has_aggregation:
            return EdgeType.AGGREGATED
        
        if lineage.has_filter:
            return EdgeType.FILTERED
        
        # Default
        return EdgeType.QUERIED_FROM
    
    def parse_query_preview(self, sql: str) -> Dict[str, Any]:
        """
        Parse SQL and return lineage info without tracking.
        
        Useful for previewing lineage before executing a query.
        
        Args:
            sql: SQL query to parse
            
        Returns:
            Dictionary with parsed lineage information
        """
        lineage = self.parser.parse(sql)
        
        return {
            'query_type': lineage.query_type,
            'source_tables': [
                {
                    'schema': t.schema,
                    'table': t.table,
                    'alias': t.alias,
                    'full_name': t.full_name,
                }
                for t in lineage.source_tables
            ],
            'target_table': {
                'schema': lineage.target_table.schema,
                'table': lineage.target_table.table,
                'full_name': lineage.target_table.full_name,
            } if lineage.target_table else None,
            'columns_used': [
                {
                    'table': c.table,
                    'column': c.column,
                }
                for c in lineage.columns_used
            ],
            'transformations': {
                'join_type': lineage.join_type,
                'has_aggregation': lineage.has_aggregation,
                'has_filter': lineage.has_filter,
            },
            'ctes': {
                name: [t.full_name for t in tables]
                for name, tables in lineage.ctes.items()
            },
        }
