"""Add notebooks tables for SQL workbench.

Revision ID: 026_add_notebooks
Revises: 025_add_data_connections
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP

# revision identifiers
revision = '026_add_notebooks'
down_revision = '025_add_data_connections'
branch_labels = None
depends_on = None


def upgrade():
    # Notebooks table
    op.create_table(
        'notebooks',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('folder', sa.String(255), server_default=''),
        sa.Column('tags', JSON, server_default='[]'),
        sa.Column('default_connection_id', UUID, sa.ForeignKey('data_connections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by', sa.String(100)),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Notebook cells table
    op.create_table(
        'notebook_cells',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('notebook_id', UUID, sa.ForeignKey('notebooks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cell_type', sa.String(32), nullable=False),
        sa.Column('content', sa.Text, nullable=False, server_default=''),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('last_run_at', TIMESTAMP(timezone=True)),
        sa.Column('last_run_duration_ms', sa.Integer),
        sa.Column('last_run_status', sa.String(32)),
        sa.Column('last_run_error', sa.Text),
        sa.Column('last_run_row_count', sa.Integer),
        sa.Column('cached_results', JSON),
        sa.Column('cached_results_uri', sa.String(500)),
        sa.Column('connection_id', UUID, sa.ForeignKey('data_connections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('settings', JSON, server_default='{}'),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Notebook datasets table
    op.create_table(
        'notebook_datasets',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('source_notebook_id', UUID, sa.ForeignKey('notebooks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_cell_id', UUID, sa.ForeignKey('notebook_cells.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_query', sa.Text),
        sa.Column('storage_uri', sa.String(500)),
        sa.Column('storage_format', sa.String(32), server_default='parquet'),
        sa.Column('row_count', sa.Integer),
        sa.Column('column_count', sa.Integer),
        sa.Column('size_bytes', sa.Integer),
        sa.Column('columns', JSON),
        sa.Column('created_by', sa.String(100)),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Indexes
    op.create_index('ix_notebooks_folder', 'notebooks', ['folder'])
    op.create_index('ix_notebooks_name', 'notebooks', ['name'])
    op.create_index('ix_notebook_cells_notebook_id', 'notebook_cells', ['notebook_id'])
    op.create_index('ix_notebook_cells_position', 'notebook_cells', ['notebook_id', 'position'])
    op.create_index('ix_notebook_datasets_name', 'notebook_datasets', ['name'])


def downgrade():
    op.drop_table('notebook_datasets')
    op.drop_table('notebook_cells')
    op.drop_table('notebooks')
