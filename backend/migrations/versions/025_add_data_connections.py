"""Add data connections and scanning tables

Revision ID: 025_add_data_connections
Revises: 024_merge_heads
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '025_add_data_connections'
down_revision = '024_merge_heads'
branch_labels = None
depends_on = None


def upgrade():
    """Create data_connections, table_scans, and recipe_compatibility tables."""
    
    # Data connections table
    op.create_table(
        'data_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('connection_type', sa.String(64), nullable=False),
        
        # Connection config
        sa.Column('host', sa.String(512)),
        sa.Column('port', sa.Integer),
        sa.Column('database', sa.String(255)),
        sa.Column('username', sa.String(255)),
        sa.Column('password_encrypted', sa.Text),
        sa.Column('extra_config', postgresql.JSON, server_default='{}'),
        
        # Status
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('last_connected_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('last_error', sa.Text),
        
        # Scan state
        sa.Column('last_scan_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('scan_status', sa.String(32), server_default='never'),
        sa.Column('tables_count', sa.Integer, server_default='0'),
        sa.Column('total_rows', sa.Integer, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Table scans table
    op.create_table(
        'table_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('data_connections.id', ondelete='CASCADE'), nullable=False),
        
        # Table identification
        sa.Column('schema_name', sa.String(255)),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(512), nullable=False),
        
        # Basic stats
        sa.Column('row_count', sa.Integer),
        sa.Column('column_count', sa.Integer),
        sa.Column('size_bytes', sa.BigInteger),
        
        # Column details
        sa.Column('columns', postgresql.JSON, server_default='[]'),
        
        # Time series detection
        sa.Column('date_column', sa.String(255)),
        sa.Column('date_min', sa.TIMESTAMP(timezone=True)),
        sa.Column('date_max', sa.TIMESTAMP(timezone=True)),
        sa.Column('date_span_days', sa.Integer),
        
        # Quality metrics
        sa.Column('completeness_score', sa.Float),
        sa.Column('quality_issues', postgresql.JSON, server_default='[]'),
        
        # Sample data
        sa.Column('sample_rows', postgresql.JSON, server_default='[]'),
        
        # Timestamps
        sa.Column('scanned_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Recipe compatibility table
    op.create_table(
        'recipe_compatibility',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_scan_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('table_scans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipe_id', sa.String(255), nullable=False),
        
        # Compatibility assessment
        sa.Column('compatibility_score', sa.Float),
        sa.Column('status', sa.String(32), nullable=False),
        
        # Requirements check
        sa.Column('requirements_met', postgresql.JSON, server_default='[]'),
        sa.Column('requirements_missing', postgresql.JSON, server_default='[]'),
        sa.Column('requirements_partial', postgresql.JSON, server_default='[]'),
        
        # Recommendations
        sa.Column('recommendations', postgresql.JSON, server_default='[]'),
        
        sa.Column('assessed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_data_connections_type', 'data_connections', ['connection_type'])
    op.create_index('ix_data_connections_status', 'data_connections', ['status'])
    op.create_index('ix_table_scans_connection', 'table_scans', ['connection_id'])
    op.create_index('ix_table_scans_full_name', 'table_scans', ['full_name'])
    op.create_index('ix_recipe_compatibility_scan', 'recipe_compatibility', ['table_scan_id'])
    op.create_index('ix_recipe_compatibility_recipe', 'recipe_compatibility', ['recipe_id'])


def downgrade():
    """Drop data connection tables."""
    op.drop_index('ix_recipe_compatibility_recipe')
    op.drop_index('ix_recipe_compatibility_scan')
    op.drop_index('ix_table_scans_full_name')
    op.drop_index('ix_table_scans_connection')
    op.drop_index('ix_data_connections_status')
    op.drop_index('ix_data_connections_type')
    
    op.drop_table('recipe_compatibility')
    op.drop_table('table_scans')
    op.drop_table('data_connections')
