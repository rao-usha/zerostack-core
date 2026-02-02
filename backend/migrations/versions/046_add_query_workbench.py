"""Add Query Workbench tables for saved queries and execution history.

Revision ID: 046_add_query_workbench
Revises: 045_add_drift_history
Create Date: 2026-02-02

Adds tables for Query Workbench feature:
- saved_queries: Store reusable SQL queries with metadata
- query_executions: Track execution history for analytics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


# revision identifiers
revision = '046_add_query_workbench'
down_revision = '045_add_drift_history'
branch_labels = None
depends_on = None


def upgrade():
    # Saved queries table
    op.create_table(
        'saved_queries',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('sql', sa.Text, nullable=False),
        sa.Column('db_id', sa.String(100), nullable=False, server_default='default'),

        # Organization
        sa.Column('folder', sa.String(255), nullable=True),  # For organizing queries
        sa.Column('tags', ARRAY(sa.String), nullable=True),

        # Parameters (for parameterized queries like {{start_date}})
        sa.Column('parameters', JSONB, nullable=True),  # [{name, type, default, description}]

        # Sharing and permissions
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_by', sa.String(255), nullable=True),

        # Scheduling (optional)
        sa.Column('schedule_cron', sa.String(100), nullable=True),  # Cron expression
        sa.Column('schedule_enabled', sa.Boolean, nullable=False, server_default='false'),

        # Caching
        sa.Column('cache_ttl_seconds', sa.Integer, nullable=True),  # Result caching duration
        sa.Column('last_cached_at', sa.TIMESTAMP(timezone=True), nullable=True),

        # Stats
        sa.Column('run_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_run_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('avg_execution_time_ms', sa.Float, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Query executions table - tracks every run
    op.create_table(
        'query_executions',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('saved_query_id', UUID, sa.ForeignKey('saved_queries.id', ondelete='CASCADE'), nullable=True),

        # Query snapshot (in case saved query is modified later)
        sa.Column('sql_snapshot', sa.Text, nullable=False),
        sa.Column('db_id', sa.String(100), nullable=False),

        # Parameters used in this execution
        sa.Column('parameters_used', JSONB, nullable=True),

        # Execution details
        sa.Column('status', sa.String(20), nullable=False),  # running, success, error, cancelled
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('execution_time_ms', sa.Float, nullable=True),

        # Results summary
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('column_count', sa.Integer, nullable=True),
        sa.Column('result_preview', JSONB, nullable=True),  # First N rows for quick view

        # Error info
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),

        # User context
        sa.Column('executed_by', sa.String(255), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='manual'),  # manual, scheduled, api
    )

    # Indexes for saved_queries
    op.create_index('idx_saved_queries_db_id', 'saved_queries', ['db_id'])
    op.create_index('idx_saved_queries_folder', 'saved_queries', ['folder'])
    op.create_index('idx_saved_queries_created_by', 'saved_queries', ['created_by'])
    op.create_index('idx_saved_queries_is_public', 'saved_queries', ['is_public'])
    op.create_index('idx_saved_queries_created_at', 'saved_queries', ['created_at'])
    op.create_index('idx_saved_queries_tags', 'saved_queries', ['tags'], postgresql_using='gin')

    # Indexes for query_executions
    op.create_index('idx_query_executions_saved_query', 'query_executions', ['saved_query_id'])
    op.create_index('idx_query_executions_status', 'query_executions', ['status'])
    op.create_index('idx_query_executions_started_at', 'query_executions', ['started_at'])
    op.create_index('idx_query_executions_db_id', 'query_executions', ['db_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_query_executions_db_id')
    op.drop_index('idx_query_executions_started_at')
    op.drop_index('idx_query_executions_status')
    op.drop_index('idx_query_executions_saved_query')

    op.drop_index('idx_saved_queries_tags')
    op.drop_index('idx_saved_queries_created_at')
    op.drop_index('idx_saved_queries_is_public')
    op.drop_index('idx_saved_queries_created_by')
    op.drop_index('idx_saved_queries_folder')
    op.drop_index('idx_saved_queries_db_id')

    # Drop tables
    op.drop_table('query_executions')
    op.drop_table('saved_queries')
