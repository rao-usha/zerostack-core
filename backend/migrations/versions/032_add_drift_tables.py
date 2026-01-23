"""Add drift detection tables.

Revision ID: 032
Revises: 031
Create Date: 2026-01-23

Adds tables for drift detection:
- drift_checks: Configuration for metric drift monitoring
- drift_alerts: Alerts triggered when drift is detected
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = '032_add_drift_tables'
down_revision = '031_add_contexts'
branch_labels = None
depends_on = None


def upgrade():
    # Drift checks - configuration for monitoring specific metrics
    op.create_table(
        'drift_checks',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metric', sa.String(255), nullable=False),
        sa.Column('threshold', sa.Numeric(10, 6), nullable=False),
        sa.Column('comparison', sa.String(50), nullable=False, server_default='percentage_both'),

        # Scope - what this check applies to
        sa.Column('recipe_id', sa.String(255), sa.ForeignKey('ml_recipe.id', ondelete='SET NULL'), nullable=True),
        sa.Column('asset_id', UUID, sa.ForeignKey('ml_derived_assets.id', ondelete='SET NULL'), nullable=True),

        # Current state
        sa.Column('baseline_value', sa.Numeric(20, 6), nullable=True),
        sa.Column('latest_value', sa.Numeric(20, 6), nullable=True),
        sa.Column('is_breached', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),

        # Scheduling
        sa.Column('check_frequency', sa.String(50), nullable=False, server_default='on_run'),
        sa.Column('last_checked_at', sa.TIMESTAMP(timezone=True), nullable=True),

        # Notification config
        sa.Column('notification_channels', sa.JSON, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Drift alerts - individual alert instances
    op.create_table(
        'drift_alerts',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('drift_check_id', UUID, sa.ForeignKey('drift_checks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_id', sa.String(255), nullable=True),

        # Alert details
        sa.Column('severity', sa.String(20), nullable=False),  # warning, critical
        sa.Column('baseline_value', sa.Numeric(20, 6), nullable=True),
        sa.Column('current_value', sa.Numeric(20, 6), nullable=True),
        sa.Column('change_percent', sa.Numeric(10, 4), nullable=True),
        sa.Column('message', sa.Text, nullable=True),

        # Acknowledgment
        sa.Column('acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),

        # Timestamps
        sa.Column('triggered_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes for common queries
    op.create_index('idx_drift_checks_recipe', 'drift_checks', ['recipe_id'])
    op.create_index('idx_drift_checks_active', 'drift_checks', ['is_active'])
    op.create_index('idx_drift_checks_breached', 'drift_checks', ['is_breached'])
    op.create_index('idx_drift_alerts_check', 'drift_alerts', ['drift_check_id'])
    op.create_index('idx_drift_alerts_unacknowledged', 'drift_alerts', ['acknowledged'])
    op.create_index('idx_drift_alerts_severity', 'drift_alerts', ['severity'])
    op.create_index('idx_drift_alerts_triggered', 'drift_alerts', ['triggered_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_drift_alerts_triggered')
    op.drop_index('idx_drift_alerts_severity')
    op.drop_index('idx_drift_alerts_unacknowledged')
    op.drop_index('idx_drift_alerts_check')
    op.drop_index('idx_drift_checks_breached')
    op.drop_index('idx_drift_checks_active')
    op.drop_index('idx_drift_checks_recipe')

    # Drop tables
    op.drop_table('drift_alerts')
    op.drop_table('drift_checks')
