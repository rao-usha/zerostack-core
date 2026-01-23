"""Add Phase 2: Drift detection, scheduling improvements

Revision ID: 022_add_phase_2
Revises: 021_add_phase_b
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import inspect

revision = '022_add_phase_2'
down_revision = '021_add_phase_b'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # ========================================
    # 1. Drift Checks Table
    # ========================================
    if not table_exists('drift_checks'):
        op.create_table(
            'drift_checks',
            sa.Column('id', UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('asset_id', UUID(), sa.ForeignKey('ml_derived_assets.id', ondelete='CASCADE'), nullable=True),
            sa.Column('recipe_id', sa.String(255), nullable=True),
            sa.Column('metric', sa.String(100), nullable=False),
            sa.Column('threshold', sa.Numeric(10, 4), nullable=False),
            sa.Column('comparison', sa.String(50), nullable=False),  # 'absolute', 'percentage_increase', 'percentage_decrease', 'both'
            sa.Column('baseline_value', sa.Numeric(10, 4), nullable=True),
            sa.Column('latest_value', sa.Numeric(10, 4), nullable=True),
            sa.Column('is_breached', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('check_frequency', sa.String(50), server_default='on_run'),  # 'on_run', 'hourly', 'daily'
            sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index('ix_drift_checks_asset_id', 'drift_checks', ['asset_id'])
        op.create_index('ix_drift_checks_recipe_id', 'drift_checks', ['recipe_id'])
        op.create_index('ix_drift_checks_is_active', 'drift_checks', ['is_active'])
    
    # ========================================
    # 2. Drift Alerts Table
    # ========================================
    if not table_exists('drift_alerts'):
        op.create_table(
            'drift_alerts',
            sa.Column('id', UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('drift_check_id', UUID(), sa.ForeignKey('drift_checks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('run_id', sa.String(255), sa.ForeignKey('ml_run.id', ondelete='SET NULL'), nullable=True),
            sa.Column('severity', sa.String(50), nullable=False),  # 'warning', 'critical'
            sa.Column('baseline_value', sa.Numeric(10, 4), nullable=True),
            sa.Column('current_value', sa.Numeric(10, 4), nullable=True),
            sa.Column('change_percent', sa.Numeric(10, 4), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('acknowledged', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('acknowledged_by', sa.String(255), nullable=True),
            sa.Column('notification_sent', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('notification_channels', JSONB, server_default='[]'),  # ['email', 'slack']
            sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index('ix_drift_alerts_drift_check_id', 'drift_alerts', ['drift_check_id'])
        op.create_index('ix_drift_alerts_acknowledged', 'drift_alerts', ['acknowledged'])
        op.create_index('ix_drift_alerts_triggered_at', 'drift_alerts', ['triggered_at'])
    
    # ========================================
    # 3. Notification Settings Table
    # ========================================
    if not table_exists('notification_settings'):
        op.create_table(
            'notification_settings',
            sa.Column('id', UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('channel', sa.String(50), nullable=False),  # 'email', 'slack', 'webhook'
            sa.Column('is_enabled', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('config', JSONB, server_default='{}'),  # channel-specific config
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    
    # ========================================
    # 4. Extend ml_derived_assets for versioning
    # ========================================
    # Add parent_asset_id for version chains
    try:
        op.add_column('ml_derived_assets', 
            sa.Column('parent_asset_id', UUID(), sa.ForeignKey('ml_derived_assets.id'), nullable=True))
    except:
        pass  # Column may already exist
    
    # ========================================
    # 5. Extend run_schedules table
    # ========================================
    try:
        op.add_column('run_schedules', sa.Column('timezone', sa.String(100), server_default='UTC'))
        op.add_column('run_schedules', sa.Column('max_retries', sa.Integer(), server_default='2'))
        op.add_column('run_schedules', sa.Column('retry_delay_seconds', sa.Integer(), server_default='300'))
        op.add_column('run_schedules', sa.Column('use_reuse_engine', sa.Boolean(), server_default='true'))
        op.add_column('run_schedules', sa.Column('notify_on_failure', sa.Boolean(), server_default='true'))
        op.add_column('run_schedules', sa.Column('notify_on_success', sa.Boolean(), server_default='false'))
        op.add_column('run_schedules', sa.Column('notification_channels', JSONB, server_default='[]'))
    except:
        pass  # Columns may already exist


def downgrade() -> None:
    # Drop tables in reverse order
    if table_exists('notification_settings'):
        op.drop_table('notification_settings')
    
    if table_exists('drift_alerts'):
        op.drop_index('ix_drift_alerts_triggered_at', 'drift_alerts')
        op.drop_index('ix_drift_alerts_acknowledged', 'drift_alerts')
        op.drop_index('ix_drift_alerts_drift_check_id', 'drift_alerts')
        op.drop_table('drift_alerts')
    
    if table_exists('drift_checks'):
        op.drop_index('ix_drift_checks_is_active', 'drift_checks')
        op.drop_index('ix_drift_checks_recipe_id', 'drift_checks')
        op.drop_index('ix_drift_checks_asset_id', 'drift_checks')
        op.drop_table('drift_checks')
    
    # Remove added columns
    try:
        op.drop_column('ml_derived_assets', 'parent_asset_id')
        op.drop_column('run_schedules', 'timezone')
        op.drop_column('run_schedules', 'max_retries')
        op.drop_column('run_schedules', 'retry_delay_seconds')
        op.drop_column('run_schedules', 'use_reuse_engine')
        op.drop_column('run_schedules', 'notify_on_failure')
        op.drop_column('run_schedules', 'notify_on_success')
        op.drop_column('run_schedules', 'notification_channels')
    except:
        pass
