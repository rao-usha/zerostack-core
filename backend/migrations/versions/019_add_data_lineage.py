"""Add data lineage tracking tables

Revision ID: 019_add_data_lineage
Revises: 018_add_gdrive_support
Create Date: 2024-01-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

# revision identifiers
revision = '019_add_data_lineage'
down_revision = '018_add_gdrive_support'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # Data Lineage Edges Table
    # Tracks relationships between data entities
    # ========================================
    op.create_table(
        'data_lineage_edges',
        sa.Column('id', UUID, primary_key=True),
        
        # Source (where data came from)
        sa.Column('source_type', sa.String(50), nullable=False, index=True),
        # Types: 'file', 'file_table', 'database_table', 'dataset', 'notebook', 'query', 'model'
        sa.Column('source_id', UUID, nullable=False, index=True),
        sa.Column('source_name', sa.String(500), nullable=True),
        sa.Column('source_schema', sa.String(200), nullable=True),  # DB schema if applicable
        
        # Target (what data became)
        sa.Column('target_type', sa.String(50), nullable=False, index=True),
        # Types: 'file_table', 'database_table', 'dataset', 'model', 'report', 'notebook_output'
        sa.Column('target_id', UUID, nullable=False, index=True),
        sa.Column('target_name', sa.String(500), nullable=True),
        sa.Column('target_schema', sa.String(200), nullable=True),
        
        # Relationship details
        sa.Column('edge_type', sa.String(50), nullable=False, index=True),
        # Types: 'derived_from', 'published', 'transformed', 'joined', 'aggregated', 'filtered', 'trained_on'
        sa.Column('transform_sql', sa.Text, nullable=True),  # SQL query if applicable
        sa.Column('transform_config', JSONB, nullable=True),  # JSON config for transformations
        
        # Metadata
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID, nullable=True),  # User who created this relationship
        
        # Data flow metrics
        sa.Column('source_row_count', sa.BigInteger, nullable=True),
        sa.Column('target_row_count', sa.BigInteger, nullable=True),
        sa.Column('source_column_count', sa.Integer, nullable=True),
        sa.Column('target_column_count', sa.Integer, nullable=True),
        
        # Create composite index for efficient lineage queries
        sa.Index('idx_lineage_source', 'source_type', 'source_id'),
        sa.Index('idx_lineage_target', 'target_type', 'target_id'),
        sa.Index('idx_lineage_edge_type', 'edge_type'),
        sa.Index('idx_lineage_created_at', 'created_at'),
    )
    
    # ========================================
    # Data Lineage Metadata Table
    # Summary statistics for each entity
    # ========================================
    op.create_table(
        'data_lineage_metadata',
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', UUID, nullable=False),
        sa.Column('entity_name', sa.String(500), nullable=True),
        
        # Lineage statistics
        sa.Column('upstream_count', sa.Integer, nullable=False, server_default='0'),  # Direct sources
        sa.Column('downstream_count', sa.Integer, nullable=False, server_default='0'),  # Direct targets
        sa.Column('total_upstream_count', sa.Integer, nullable=False, server_default='0'),  # All ancestors
        sa.Column('total_downstream_count', sa.Integer, nullable=False, server_default='0'),  # All descendants
        sa.Column('lineage_depth', sa.Integer, nullable=False, server_default='0'),  # Hops from original source
        
        # Freshness tracking
        sa.Column('last_refreshed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('upstream_last_modified_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_stale', sa.Boolean, nullable=False, server_default='false'),  # True if upstream changed
        
        # Usage tracking
        sa.Column('access_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_accessed_at', TIMESTAMP(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Primary key on (entity_type, entity_id)
        sa.PrimaryKeyConstraint('entity_type', 'entity_id'),
        sa.Index('idx_lineage_metadata_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_lineage_metadata_stale', 'is_stale'),
    )
    
    # ========================================
    # Column-Level Lineage Table (Optional, for detailed tracking)
    # ========================================
    op.create_table(
        'data_lineage_columns',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('edge_id', UUID, sa.ForeignKey('data_lineage_edges.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Source column
        sa.Column('source_column', sa.String(200), nullable=False),
        sa.Column('source_data_type', sa.String(100), nullable=True),
        
        # Target column
        sa.Column('target_column', sa.String(200), nullable=False),
        sa.Column('target_data_type', sa.String(100), nullable=True),
        
        # Transformation applied
        sa.Column('transformation', sa.String(50), nullable=True),  # 'direct', 'cast', 'calculated', 'aggregated'
        sa.Column('transformation_expression', sa.Text, nullable=True),  # SQL expression if applicable
        
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        
        sa.Index('idx_lineage_columns_edge', 'edge_id'),
        sa.Index('idx_lineage_columns_source', 'source_column'),
        sa.Index('idx_lineage_columns_target', 'target_column'),
    )
    
    print("✅ Created data lineage tables")


def downgrade():
    op.drop_table('data_lineage_columns')
    op.drop_table('data_lineage_metadata')
    op.drop_table('data_lineage_edges')
    print("✅ Dropped data lineage tables")
