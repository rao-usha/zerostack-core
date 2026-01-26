"""Add managed_procedures table for tracking user-created stored procedures.

Revision ID: 042_add_managed_procedures
Revises: 041_add_materialized_views
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP

# revision identifiers
revision = '042_add_managed_procedures'
down_revision = '041_add_materialized_views'
branch_labels = None
depends_on = None


def upgrade():
    # Managed stored procedures tracking table
    op.create_table(
        'managed_procedures',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('schema_name', sa.String(128), nullable=False, server_default='public'),
        sa.Column('description', sa.Text, nullable=True),

        # Procedure definition
        sa.Column('language', sa.String(32), server_default='plpgsql'),  # plpgsql, sql
        sa.Column('source_code', sa.Text, nullable=False),
        sa.Column('parameters', JSON, server_default='[]'),  # [{name, type, default, mode}]
        sa.Column('return_type', sa.String(128), nullable=True),  # null for void
        sa.Column('returns_set', sa.Boolean, server_default='false'),  # RETURNS SETOF

        # Security
        sa.Column('security_definer', sa.Boolean, server_default='false'),
        sa.Column('allowed_roles', JSON, server_default='[]'),  # Roles that can execute

        # Configuration
        sa.Column('connection_id', sa.String(64), server_default='default'),
        sa.Column('volatility', sa.String(16), server_default='volatile'),  # volatile, stable, immutable
        sa.Column('parallel_safety', sa.String(16), server_default='unsafe'),  # unsafe, restricted, safe

        # Status
        sa.Column('status', sa.String(32), server_default='active'),  # active, failed, dropped

        # Execution stats
        sa.Column('execution_count', sa.BigInteger, server_default='0'),
        sa.Column('last_executed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('avg_execution_ms', sa.Integer, nullable=True),

        # Error handling
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('error_count', sa.Integer, server_default='0'),

        # Audit
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('conversation_id', UUID, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),

        # Ensure unique name per schema
        sa.UniqueConstraint('schema_name', 'name', name='uq_managed_proc_schema_name'),
    )

    # Indexes
    op.create_index('ix_managed_proc_status', 'managed_procedures', ['status'])
    op.create_index('ix_managed_proc_created_by', 'managed_procedures', ['created_by'])
    op.create_index('ix_managed_proc_schema', 'managed_procedures', ['schema_name'])
    op.create_index('ix_managed_proc_language', 'managed_procedures', ['language'])


def downgrade():
    op.drop_index('ix_managed_proc_language')
    op.drop_index('ix_managed_proc_schema')
    op.drop_index('ix_managed_proc_created_by')
    op.drop_index('ix_managed_proc_status')
    op.drop_table('managed_procedures')
