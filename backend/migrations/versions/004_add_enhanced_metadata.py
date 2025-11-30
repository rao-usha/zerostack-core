"""Add enhanced metadata tables for database connections and table analysis tracking

Revision ID: 004
Revises: 003
Create Date: 2024-11-30

Tables:
- database_connection_metadata: Track external database connections
- table_analysis_links: Link analyses to specific tables with detailed metadata
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, ARRAY

# revision identifiers, used by Alembic.
revision = '004_metadata'
down_revision = '003_ai_analysis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create database_connection_metadata table
    op.create_table(
        'database_connection_metadata',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('connection_id', sa.String(100), nullable=False, unique=True, comment='Connection identifier (default, db2, etc.)'),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('database_name', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, comment='User-friendly name'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('schemas', ARRAY(sa.String), nullable=True, comment='List of schemas in this database'),
        sa.Column('table_count', sa.Integer, nullable=True),
        sa.Column('first_connected_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_connected_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('total_analyses', sa.Integer, nullable=False, server_default='0'),
        sa.Column('metadata', JSONB, nullable=True, comment='Additional connection metadata'),
    )
    
    # Create indexes
    op.create_index('ix_database_metadata_connection_id', 'database_connection_metadata', ['connection_id'])
    op.create_index('ix_database_metadata_host', 'database_connection_metadata', ['host'])
    
    # Create table_analysis_links table
    op.create_table(
        'table_analysis_links',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', UUID, sa.ForeignKey('ai_analysis_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('database_id', sa.String(100), nullable=False, comment='Database connection ID'),
        sa.Column('schema_name', sa.String(255), nullable=False),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('row_count_at_analysis', sa.Integer, nullable=True),
        sa.Column('column_count', sa.Integer, nullable=True),
        sa.Column('findings', JSONB, nullable=True, comment='Specific findings for this table'),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('anomaly_count', sa.Integer, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create indexes for efficient lookups
    op.create_index('ix_table_links_analysis_id', 'table_analysis_links', ['analysis_id'])
    op.create_index('ix_table_links_database_id', 'table_analysis_links', ['database_id'])
    op.create_index('ix_table_links_schema', 'table_analysis_links', ['schema_name'])
    op.create_index('ix_table_links_table', 'table_analysis_links', ['table_name'])
    # Composite index for finding all analyses for a specific table
    op.create_index('ix_table_links_table_lookup', 'table_analysis_links', ['database_id', 'schema_name', 'table_name'])
    # Composite index for finding all tables in an analysis
    op.create_index('ix_table_links_analysis_tables', 'table_analysis_links', ['analysis_id', 'table_name'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_table_links_analysis_tables', table_name='table_analysis_links')
    op.drop_index('ix_table_links_table_lookup', table_name='table_analysis_links')
    op.drop_index('ix_table_links_table', table_name='table_analysis_links')
    op.drop_index('ix_table_links_schema', table_name='table_analysis_links')
    op.drop_index('ix_table_links_database_id', table_name='table_analysis_links')
    op.drop_index('ix_table_links_analysis_id', table_name='table_analysis_links')
    
    op.drop_index('ix_database_metadata_host', table_name='database_connection_metadata')
    op.drop_index('ix_database_metadata_connection_id', table_name='database_connection_metadata')
    
    # Drop tables
    op.drop_table('table_analysis_links')
    op.drop_table('database_connection_metadata')

