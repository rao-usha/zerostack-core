"""
Cross-Query Lineage Tracking

Connects queries that share intermediate tables to build a complete
data pipeline view.

Example:
    Query 1: sales_raw -> sales_clean
    Query 2: sales_clean -> daily_summary
    Result: sales_raw -> sales_clean -> daily_summary (full pipeline)
"""
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID
from collections import defaultdict

from sqlmodel import Session, select
from .models import LineageNode, LineageEdge, EntityType


@dataclass
class QueryChain:
    """Represents a chain of connected queries"""
    chain_id: str
    queries: List[Dict]
    tables_involved: List[str]
    start_table: str
    end_table: str
    total_transformations: int
    created_at: datetime


@dataclass
class DataPipeline:
    """Represents a complete data pipeline"""
    pipeline_id: str
    name: str
    stages: List[Dict]  # Each stage: {table, query, transformation}
    source_tables: List[str]
    target_tables: List[str]
    total_rows_processed: Optional[int]
    last_run: Optional[datetime]


class CrossQueryTracker:
    """
    Tracks relationships between queries that share tables.
    
    Detects:
    - Sequential queries (output of one is input to another)
    - Parallel queries (multiple queries reading same source)
    - Pipelines (chains of transformations)
    - Circular dependencies (should warn!)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_query_chains(
        self,
        starting_table: str,
        max_depth: int = 10,
        time_window_hours: Optional[int] = None
    ) -> List[QueryChain]:
        """
        Find chains of queries starting from a table.
        
        Args:
            starting_table: Table to start from
            max_depth: Maximum chain depth
            time_window_hours: Only consider queries within this time window
            
        Returns:
            List of query chains
        """
        chains = []
        
        # Find node for starting table
        start_node = self._find_node_by_name(starting_table, EntityType.DATABASE_TABLE)
        if not start_node:
            return []
        
        # Build chains via recursive traversal
        visited = set()
        current_chain = []
        
        self._traverse_downstream(
            node_id=start_node.id,
            current_chain=current_chain,
            visited=visited,
            chains=chains,
            depth=0,
            max_depth=max_depth,
            time_window_hours=time_window_hours
        )
        
        return chains
    
    def _traverse_downstream(
        self,
        node_id: UUID,
        current_chain: List[Dict],
        visited: Set[UUID],
        chains: List[QueryChain],
        depth: int,
        max_depth: int,
        time_window_hours: Optional[int]
    ):
        """Recursively traverse downstream to build query chains"""
        if depth >= max_depth or node_id in visited:
            return
        
        visited.add(node_id)
        
        # Get current node
        node = self.db.get(LineageNode, node_id)
        if not node:
            return
        
        # Add to current chain
        current_chain.append({
            'node_id': str(node.id),
            'entity_type': node.entity_type,
            'name': node.name,
            'created_at': node.created_at
        })
        
        # Get downstream edges
        edges_query = select(LineageEdge).where(LineageEdge.source_node_id == node_id)
        if time_window_hours:
            cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
            edges_query = edges_query.where(LineageEdge.created_at >= cutoff)
        
        edges = self.db.exec(edges_query).all()
        
        if not edges:
            # End of chain - save it if it's longer than 1
            if len(current_chain) > 1:
                chains.append(self._create_query_chain(current_chain))
        else:
            # Continue traversal
            for edge in edges:
                self._traverse_downstream(
                    node_id=edge.target_node_id,
                    current_chain=current_chain.copy(),
                    visited=visited.copy(),
                    chains=chains,
                    depth=depth + 1,
                    max_depth=max_depth,
                    time_window_hours=time_window_hours
                )
    
    def _create_query_chain(self, chain: List[Dict]) -> QueryChain:
        """Create QueryChain from list of nodes"""
        return QueryChain(
            chain_id=f"chain_{chain[0]['node_id']}_{chain[-1]['node_id']}",
            queries=chain,
            tables_involved=[node['name'] for node in chain],
            start_table=chain[0]['name'],
            end_table=chain[-1]['name'],
            total_transformations=len(chain) - 1,
            created_at=chain[0]['created_at']
        )
    
    def discover_pipelines(
        self,
        min_stages: int = 3,
        time_window_hours: Optional[int] = 24
    ) -> List[DataPipeline]:
        """
        Discover data pipelines (query chains with multiple stages).
        
        Args:
            min_stages: Minimum number of stages to qualify as pipeline
            time_window_hours: Time window to search
            
        Returns:
            List of discovered pipelines
        """
        pipelines = []
        
        # Get all nodes that have both upstream and downstream connections
        # (intermediate tables in pipelines)
        query = """
        SELECT DISTINCT n.id, n.name, n.entity_type
        FROM data_lineage_nodes n
        WHERE EXISTS (SELECT 1 FROM data_lineage_edges e WHERE e.target_node_id = n.id)
          AND EXISTS (SELECT 1 FROM data_lineage_edges e WHERE e.source_node_id = n.id)
        """
        
        results = self.db.exec(query).all()
        
        for row in results:
            # Find chains starting from upstream sources
            chains = self.find_query_chains(
                starting_table=row.name,
                max_depth=15,
                time_window_hours=time_window_hours
            )
            
            for chain in chains:
                if chain.total_transformations >= min_stages - 1:
                    pipeline = self._chain_to_pipeline(chain)
                    pipelines.append(pipeline)
        
        return pipelines
    
    def _chain_to_pipeline(self, chain: QueryChain) -> DataPipeline:
        """Convert QueryChain to DataPipeline"""
        stages = []
        
        for i, node_info in enumerate(chain.queries):
            stage = {
                'stage_number': i + 1,
                'table': node_info['name'],
                'entity_type': node_info['entity_type'],
                'created_at': node_info['created_at']
            }
            
            # Get transformation SQL if available
            if i > 0:
                prev_node_id = UUID(chain.queries[i-1]['node_id'])
                curr_node_id = UUID(node_info['node_id'])
                
                edge = self.db.exec(
                    select(LineageEdge).where(
                        LineageEdge.source_node_id == prev_node_id,
                        LineageEdge.target_node_id == curr_node_id
                    )
                ).first()
                
                if edge:
                    stage['transformation'] = edge.relationship_type
                    stage['transform_sql'] = edge.metadata.get('transform_sql')
            
            stages.append(stage)
        
        return DataPipeline(
            pipeline_id=chain.chain_id,
            name=f"Pipeline: {chain.start_table} → {chain.end_table}",
            stages=stages,
            source_tables=[chain.start_table],
            target_tables=[chain.end_table],
            total_rows_processed=None,  # Could be calculated
            last_run=chain.created_at
        )
    
    def find_shared_sources(self, target_table: str) -> Dict[str, List[str]]:
        """
        Find queries that share the same source tables.
        
        Useful for detecting parallel processing or duplicate logic.
        
        Args:
            target_table: Table to analyze
            
        Returns:
            Dict mapping source tables to list of queries using them
        """
        target_node = self._find_node_by_name(target_table, EntityType.DATABASE_TABLE)
        if not target_node:
            return {}
        
        # Get all upstream sources
        upstream_query = select(LineageEdge).where(
            LineageEdge.target_node_id == target_node.id
        )
        upstream_edges = self.db.exec(upstream_query).all()
        
        # Group by source
        sources: Dict[str, List[str]] = defaultdict(list)
        
        for edge in upstream_edges:
            source_node = self.db.get(LineageNode, edge.source_node_id)
            if source_node:
                # Get transform SQL if available
                transform_info = edge.metadata.get('transform_sql', 'Unknown transformation')
                sources[source_node.name].append(transform_info)
        
        return dict(sources)
    
    def detect_circular_dependencies(self) -> List[Dict]:
        """
        Detect circular dependencies in lineage graph.
        
        These usually indicate issues (e.g., table A depends on B, B depends on A)
        
        Returns:
            List of circular dependency chains
        """
        circular_deps = []
        
        # Get all nodes
        nodes = self.db.exec(select(LineageNode)).all()
        
        for node in nodes:
            # Try to find a path back to this node
            visited = set()
            path = []
            
            if self._has_cycle(node.id, node.id, visited, path, is_start=True):
                circular_deps.append({
                    'cycle': path,
                    'tables': [self.db.get(LineageNode, node_id).name for node_id in path]
                })
        
        return circular_deps
    
    def _has_cycle(
        self,
        start_id: UUID,
        current_id: UUID,
        visited: Set[UUID],
        path: List[UUID],
        is_start: bool = False
    ) -> bool:
        """Check if there's a cycle from start_id to current_id"""
        if not is_start and current_id == start_id:
            return True
        
        if current_id in visited:
            return False
        
        visited.add(current_id)
        path.append(current_id)
        
        # Get downstream nodes
        edges = self.db.exec(
            select(LineageEdge).where(LineageEdge.source_node_id == current_id)
        ).all()
        
        for edge in edges:
            if self._has_cycle(start_id, edge.target_node_id, visited.copy(), path.copy(), False):
                return True
        
        return False
    
    def _find_node_by_name(self, name: str, entity_type: EntityType) -> Optional[LineageNode]:
        """Find a node by name and type"""
        return self.db.exec(
            select(LineageNode).where(
                LineageNode.name == name,
                LineageNode.entity_type == entity_type
            )
        ).first()


def get_cross_query_tracker(db: Session) -> CrossQueryTracker:
    """Dependency injection helper"""
    return CrossQueryTracker(db)
