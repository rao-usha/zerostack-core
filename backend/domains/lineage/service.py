"""
Data Lineage Service

Business logic for tracking and querying data lineage.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Set, Tuple
from uuid import UUID
from sqlmodel import Session, select, or_, and_, func
from collections import deque

from .models import (
    DataLineageEdge,
    DataLineageMetadata,
    DataLineageColumn,
    EntityType,
    EdgeType,
    LineageNode,
    LineageEdgeResponse,
    LineageGraphResponse,
    LineageSummary,
    CreateLineageRequest,
    LineageImpactAnalysis,
    ColumnLineage,
)


class LineageService:
    """Service for managing data lineage"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================
    # Create Lineage
    # ========================================
    
    def track_lineage(
        self,
        source_type: EntityType,
        source_id: UUID,
        source_name: str,
        target_type: EntityType,
        target_id: UUID,
        target_name: str,
        edge_type: EdgeType,
        transform_sql: Optional[str] = None,
        transform_config: Optional[Dict[str, Any]] = None,
        source_row_count: Optional[int] = None,
        target_row_count: Optional[int] = None,
        source_column_count: Optional[int] = None,
        target_column_count: Optional[int] = None,
        column_mappings: Optional[List[ColumnLineage]] = None,
        created_by: Optional[UUID] = None,
    ) -> DataLineageEdge:
        """
        Track a lineage relationship between two data entities.
        
        Args:
            source_type: Type of source entity
            source_id: ID of source entity
            source_name: Display name of source
            target_type: Type of target entity
            target_id: ID of target entity
            target_name: Display name of target
            edge_type: Type of relationship
            transform_sql: SQL query if applicable
            transform_config: JSON config for transformation
            source_row_count: Number of rows in source
            target_row_count: Number of rows in target
            source_column_count: Number of columns in source
            target_column_count: Number of columns in target
            column_mappings: Column-level lineage mappings
            created_by: User who created this relationship
            
        Returns:
            Created DataLineageEdge
        """
        # Check if edge already exists
        existing_edge = self.db.exec(
            select(DataLineageEdge).where(
                and_(
                    DataLineageEdge.source_type == source_type,
                    DataLineageEdge.source_id == source_id,
                    DataLineageEdge.target_type == target_type,
                    DataLineageEdge.target_id == target_id,
                    DataLineageEdge.edge_type == edge_type,
                )
            )
        ).first()
        
        if existing_edge:
            # Update existing edge
            existing_edge.transform_sql = transform_sql
            existing_edge.transform_config = transform_config
            existing_edge.source_row_count = source_row_count
            existing_edge.target_row_count = target_row_count
            existing_edge.source_column_count = source_column_count
            existing_edge.target_column_count = target_column_count
            self.db.add(existing_edge)
            edge = existing_edge
        else:
            # Create new edge
            edge = DataLineageEdge(
                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                edge_type=edge_type,
                transform_sql=transform_sql,
                transform_config=transform_config,
                source_row_count=source_row_count,
                target_row_count=target_row_count,
                source_column_count=source_column_count,
                target_column_count=target_column_count,
                created_by=created_by,
            )
            self.db.add(edge)
        
        self.db.commit()
        self.db.refresh(edge)
        
        # Add column-level lineage if provided
        if column_mappings:
            for col_map in column_mappings:
                col_lineage = DataLineageColumn(
                    edge_id=edge.id,
                    source_column=col_map.source_column,
                    source_data_type=col_map.source_data_type,
                    target_column=col_map.target_column,
                    target_data_type=col_map.target_data_type,
                    transformation=col_map.transformation,
                    transformation_expression=col_map.transformation_expression,
                )
                self.db.add(col_lineage)
            self.db.commit()
        
        # Update metadata for both entities
        self._update_metadata(source_type, source_id, source_name)
        self._update_metadata(target_type, target_id, target_name)
        
        return edge
    
    def _update_metadata(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        entity_name: str,
    ):
        """Update or create metadata for an entity"""
        metadata = self.db.exec(
            select(DataLineageMetadata).where(
                and_(
                    DataLineageMetadata.entity_type == entity_type,
                    DataLineageMetadata.entity_id == entity_id,
                )
            )
        ).first()
        
        if not metadata:
            metadata = DataLineageMetadata(
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
            )
            self.db.add(metadata)
        
        # Count direct upstream and downstream
        upstream_count = self.db.exec(
            select(func.count(DataLineageEdge.id)).where(
                and_(
                    DataLineageEdge.target_type == entity_type,
                    DataLineageEdge.target_id == entity_id,
                )
            )
        ).one()
        
        downstream_count = self.db.exec(
            select(func.count(DataLineageEdge.id)).where(
                and_(
                    DataLineageEdge.source_type == entity_type,
                    DataLineageEdge.source_id == entity_id,
                )
            )
        ).one()
        
        metadata.upstream_count = upstream_count
        metadata.downstream_count = downstream_count
        metadata.updated_at = datetime.utcnow()
        
        self.db.add(metadata)
        self.db.commit()
    
    # ========================================
    # Query Lineage
    # ========================================
    
    def get_lineage_graph(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        max_depth: int = 3,
        direction: str = "both",  # "upstream", "downstream", "both"
        include_columns: bool = False,
    ) -> LineageGraphResponse:
        """
        Get complete lineage graph for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            max_depth: Maximum depth to traverse
            direction: Which direction to traverse
            include_columns: Whether to include column-level lineage
            
        Returns:
            LineageGraphResponse with nodes and edges
        """
        # Get center node info
        center_node = self._get_node_info(entity_type, entity_id)
        
        # Get upstream lineage
        upstream_nodes = []
        upstream_edges = []
        if direction in ["upstream", "both"]:
            upstream_nodes, upstream_edges = self._traverse_lineage(
                entity_type, entity_id, max_depth, "upstream"
            )
        
        # Get downstream lineage
        downstream_nodes = []
        downstream_edges = []
        if direction in ["downstream", "both"]:
            downstream_nodes, downstream_edges = self._traverse_lineage(
                entity_type, entity_id, max_depth, "downstream"
            )
        
        # Get column mappings if requested
        column_mappings = []
        if include_columns:
            edge_ids = [e.id for e in upstream_edges + downstream_edges]
            if edge_ids:
                columns = self.db.exec(
                    select(DataLineageColumn).where(
                        DataLineageColumn.edge_id.in_(edge_ids)
                    )
                ).all()
                
                column_mappings = [
                    ColumnLineage(
                        source_column=col.source_column,
                        source_data_type=col.source_data_type,
                        target_column=col.target_column,
                        target_data_type=col.target_data_type,
                        transformation=col.transformation,
                        transformation_expression=col.transformation_expression,
                    )
                    for col in columns
                ]
        
        # Convert edges to response format
        edge_responses = [
            LineageEdgeResponse.model_validate(edge)
            for edge in upstream_edges + downstream_edges
        ]
        
        return LineageGraphResponse(
            center_node=center_node,
            upstream_nodes=upstream_nodes,
            downstream_nodes=downstream_nodes,
            edges=edge_responses,
            column_mappings=column_mappings,
            total_upstream_count=len(upstream_nodes),
            total_downstream_count=len(downstream_nodes),
            max_depth=max_depth,
        )
    
    def _traverse_lineage(
        self,
        start_type: EntityType,
        start_id: UUID,
        max_depth: int,
        direction: str,
    ) -> Tuple[List[LineageNode], List[DataLineageEdge]]:
        """
        Traverse lineage graph using BFS.
        
        Returns:
            Tuple of (nodes, edges)
        """
        visited_nodes: Set[Tuple[EntityType, UUID]] = set()
        all_nodes: List[LineageNode] = []
        all_edges: List[DataLineageEdge] = []
        
        # BFS queue: (entity_type, entity_id, depth)
        queue = deque([(start_type, start_id, 0)])
        visited_nodes.add((start_type, start_id))
        
        while queue:
            current_type, current_id, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Get edges
            if direction == "upstream":
                # Get edges where current entity is the target
                edges = self.db.exec(
                    select(DataLineageEdge).where(
                        and_(
                            DataLineageEdge.target_type == current_type,
                            DataLineageEdge.target_id == current_id,
                        )
                    )
                ).all()
                
                for edge in edges:
                    all_edges.append(edge)
                    next_node = (edge.source_type, edge.source_id)
                    if next_node not in visited_nodes:
                        visited_nodes.add(next_node)
                        node_info = self._get_node_info(edge.source_type, edge.source_id)
                        node_info.depth = depth + 1
                        all_nodes.append(node_info)
                        queue.append((edge.source_type, edge.source_id, depth + 1))
            
            else:  # downstream
                # Get edges where current entity is the source
                edges = self.db.exec(
                    select(DataLineageEdge).where(
                        and_(
                            DataLineageEdge.source_type == current_type,
                            DataLineageEdge.source_id == current_id,
                        )
                    )
                ).all()
                
                for edge in edges:
                    all_edges.append(edge)
                    next_node = (edge.target_type, edge.target_id)
                    if next_node not in visited_nodes:
                        visited_nodes.add(next_node)
                        node_info = self._get_node_info(edge.target_type, edge.target_id)
                        node_info.depth = depth + 1
                        all_nodes.append(node_info)
                        queue.append((edge.target_type, edge.target_id, depth + 1))
        
        return all_nodes, all_edges
    
    def _get_node_info(self, entity_type: EntityType, entity_id: UUID) -> LineageNode:
        """Get basic info about a node"""
        # Try to get metadata first
        metadata = self.db.exec(
            select(DataLineageMetadata).where(
                and_(
                    DataLineageMetadata.entity_type == entity_type,
                    DataLineageMetadata.entity_id == entity_id,
                )
            )
        ).first()
        
        if metadata:
            return LineageNode(
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=metadata.entity_name or "Unknown",
                is_source=metadata.upstream_count == 0,
                is_sink=metadata.downstream_count == 0,
            )
        
        # Fallback: get name from edges
        edge = self.db.exec(
            select(DataLineageEdge).where(
                or_(
                    and_(
                        DataLineageEdge.source_type == entity_type,
                        DataLineageEdge.source_id == entity_id,
                    ),
                    and_(
                        DataLineageEdge.target_type == entity_type,
                        DataLineageEdge.target_id == entity_id,
                    ),
                )
            )
        ).first()
        
        name = "Unknown"
        if edge:
            if edge.source_type == entity_type and edge.source_id == entity_id:
                name = edge.source_name or "Unknown"
            else:
                name = edge.target_name or "Unknown"
        
        return LineageNode(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=name,
        )
    
    def get_lineage_summary(
        self,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> LineageSummary:
        """Get quick summary of lineage for an entity"""
        metadata = self.db.exec(
            select(DataLineageMetadata).where(
                and_(
                    DataLineageMetadata.entity_type == entity_type,
                    DataLineageMetadata.entity_id == entity_id,
                )
            )
        ).first()
        
        if not metadata:
            # Create basic metadata
            self._update_metadata(entity_type, entity_id, "Unknown")
            metadata = self.db.exec(
                select(DataLineageMetadata).where(
                    and_(
                        DataLineageMetadata.entity_type == entity_type,
                        DataLineageMetadata.entity_id == entity_id,
                    )
                )
            ).first()
        
        # Get immediate source names
        upstream_edges = self.db.exec(
            select(DataLineageEdge).where(
                and_(
                    DataLineageEdge.target_type == entity_type,
                    DataLineageEdge.target_id == entity_id,
                )
            ).limit(10)
        ).all()
        
        immediate_sources = [edge.source_name for edge in upstream_edges if edge.source_name]
        
        # Get immediate target names
        downstream_edges = self.db.exec(
            select(DataLineageEdge).where(
                and_(
                    DataLineageEdge.source_type == entity_type,
                    DataLineageEdge.source_id == entity_id,
                )
            ).limit(10)
        ).all()
        
        immediate_targets = [edge.target_name for edge in downstream_edges if edge.target_name]
        
        return LineageSummary(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=metadata.entity_name or "Unknown",
            upstream_count=metadata.upstream_count,
            downstream_count=metadata.downstream_count,
            total_upstream_count=metadata.total_upstream_count,
            total_downstream_count=metadata.total_downstream_count,
            immediate_sources=immediate_sources,
            immediate_targets=immediate_targets,
            is_stale=metadata.is_stale,
            last_refreshed_at=metadata.last_refreshed_at,
        )
    
    # ========================================
    # Impact Analysis
    # ========================================
    
    def analyze_impact(
        self,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> LineageImpactAnalysis:
        """Analyze impact of changes to this entity"""
        # Get all downstream entities
        downstream_nodes, _ = self._traverse_lineage(
            entity_type, entity_id, max_depth=10, direction="downstream"
        )
        
        # Categorize by type
        affected_datasets = [n for n in downstream_nodes if n.entity_type == EntityType.DATASET]
        affected_models = [n for n in downstream_nodes if n.entity_type == EntityType.MODEL]
        affected_reports = [n for n in downstream_nodes if n.entity_type == EntityType.REPORT]
        
        # Determine risk level
        total_affected = len(downstream_nodes)
        if total_affected == 0:
            risk_level = "low"
        elif total_affected < 5:
            risk_level = "low"
        elif total_affected < 20:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Generate recommendations
        recommendations = []
        if affected_models:
            recommendations.append(f"⚠️ {len(affected_models)} ML model(s) may need retraining")
        if affected_reports:
            recommendations.append(f"📊 {len(affected_reports)} report(s) may need refresh")
        if affected_datasets:
            recommendations.append(f"💾 {len(affected_datasets)} downstream dataset(s) affected")
        if not recommendations:
            recommendations.append("✅ No downstream dependencies detected")
        
        metadata = self.db.exec(
            select(DataLineageMetadata).where(
                and_(
                    DataLineageMetadata.entity_type == entity_type,
                    DataLineageMetadata.entity_id == entity_id,
                )
            )
        ).first()
        
        entity_name = metadata.entity_name if metadata else "Unknown"
        
        return LineageImpactAnalysis(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            affected_downstream_count=total_affected,
            affected_entities=downstream_nodes[:50],  # Limit to 50
            risk_level=risk_level,
            recommendations=recommendations,
        )
    
    # ========================================
    # Utility Methods
    # ========================================
    
    def delete_lineage(
        self,
        entity_type: EntityType,
        entity_id: UUID,
    ):
        """Delete all lineage for an entity"""
        # Delete edges where entity is source
        self.db.exec(
            select(DataLineageEdge).where(
                and_(
                    DataLineageEdge.source_type == entity_type,
                    DataLineageEdge.source_id == entity_id,
                )
            )
        ).delete()
        
        # Delete edges where entity is target
        self.db.exec(
            select(DataLineageEdge).where(
                and_(
                    DataLineageEdge.target_type == entity_type,
                    DataLineageEdge.target_id == entity_id,
                )
            )
        ).delete()
        
        # Delete metadata
        self.db.exec(
            select(DataLineageMetadata).where(
                and_(
                    DataLineageMetadata.entity_type == entity_type,
                    DataLineageMetadata.entity_id == entity_id,
                )
            )
        ).delete()
        
        self.db.commit()
