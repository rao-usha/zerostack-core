"""Add drift_history table for tracking metric values over time.

Revision ID: 045_add_drift_history
Revises: 044_add_insights
Create Date: 2026-02-02

Adds drift_history table to store every metric value checked,
enabling trend analysis and visualization of drift over time.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = '045_add_drift_history'
down_revision = '044_add_insights'
branch_labels = None
depends_on = None


def upgrade():
    # Drift history - stores every value checked for trending
    op.create_table(
        'drift_history',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('drift_check_id', UUID, sa.ForeignKey('drift_checks.id', ondelete='CASCADE'), nullable=False),

        # The recorded value
        sa.Column('value', sa.Numeric(20, 6), nullable=False),
        sa.Column('baseline_value', sa.Numeric(20, 6), nullable=True),
        sa.Column('change_percent', sa.Numeric(10, 4), nullable=True),

        # Status at time of recording
        sa.Column('is_breached', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('severity', sa.String(20), nullable=True),  # warning, critical, or null if not breached

        # Context
        sa.Column('run_id', sa.String(255), nullable=True),  # Which ML run this was from
        sa.Column('source', sa.String(50), nullable=False, server_default='run'),  # run, manual, scheduled

        # Timestamp
        sa.Column('recorded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Indexes for efficient querying
    op.create_index('idx_drift_history_check', 'drift_history', ['drift_check_id'])
    op.create_index('idx_drift_history_recorded', 'drift_history', ['recorded_at'])
    op.create_index('idx_drift_history_check_time', 'drift_history', ['drift_check_id', 'recorded_at'])
    op.create_index('idx_drift_history_breached', 'drift_history', ['is_breached'])


def downgrade():
    op.drop_index('idx_drift_history_breached')
    op.drop_index('idx_drift_history_check_time')
    op.drop_index('idx_drift_history_recorded')
    op.drop_index('idx_drift_history_check')
    op.drop_table('drift_history')
