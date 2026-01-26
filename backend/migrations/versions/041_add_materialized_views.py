"""Add materialized_views table for tracking user-created materialized views.

Revision ID: 041_add_materialized_views
Revises: 040_add_data_exports
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP

# revision identifiers
revision = '041_add_materialized_views'
down_revision = '040_add_data_exports'
branch_labels = None
depends_on = None


def upgrade():
    # Materialized views tracking table
    op.create_table(
        'managed_materialized_views',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('schema_name', sa.String(128), nullable=False, server_default='public'),
        sa.Column('description', sa.Text, nullable=True),

        # Source definition
        sa.Column('source_query', sa.Text, nullable=False),
        sa.Column('connection_id', sa.String(64), server_default='default'),

        # Configuration
        sa.Column('with_data', sa.Boolean, server_default='true'),
        sa.Column('unique_indexes', JSON, server_default='[]'),  # List of unique index definitions
        sa.Column('indexes', JSON, server_default='[]'),  # List of regular index definitions

        # Refresh settings
        sa.Column('refresh_schedule', sa.String(64), nullable=True),  # Cron expression or null for manual
        sa.Column('refresh_concurrently', sa.Boolean, server_default='true'),
        sa.Column('last_refresh_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_refresh_duration_ms', sa.Integer, nullable=True),
        sa.Column('next_refresh_at', TIMESTAMP(timezone=True), nullable=True),

        # Status
        sa.Column('status', sa.String(32), server_default='active'),  # active, refreshing, failed, dropped
        sa.Column('row_count', sa.BigInteger, nullable=True),
        sa.Column('size_bytes', sa.BigInteger, nullable=True),

        # Error handling
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('error_count', sa.Integer, server_default='0'),

        # Audit
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('conversation_id', UUID, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),

        # Ensure unique name per schema
        sa.UniqueConstraint('schema_name', 'name', name='uq_managed_mv_schema_name'),
    )

    # Indexes
    op.create_index('ix_managed_mv_status', 'managed_materialized_views', ['status'])
    op.create_index('ix_managed_mv_created_by', 'managed_materialized_views', ['created_by'])
    op.create_index('ix_managed_mv_schema', 'managed_materialized_views', ['schema_name'])
    op.create_index('ix_managed_mv_next_refresh', 'managed_materialized_views', ['next_refresh_at'])


def downgrade():
    op.drop_index('ix_managed_mv_next_refresh')
    op.drop_index('ix_managed_mv_schema')
    op.drop_index('ix_managed_mv_created_by')
    op.drop_index('ix_managed_mv_status')
    op.drop_table('managed_materialized_views')
