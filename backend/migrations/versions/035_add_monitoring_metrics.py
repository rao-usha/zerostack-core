"""Add model monitoring metrics tables.

Revision ID: 035
Revises: 034
Create Date: 2026-01-23

Adds tables for tracking model latency, error rates, and SLA configuration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers
revision = '035_add_monitoring_metrics'
down_revision = '034_add_model_promotions'
branch_labels = None
depends_on = None


def upgrade():
    # Model latency metrics - percentile tracking
    op.create_table(
        'model_latency_metrics',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_id', sa.String(255), sa.ForeignKey('ml_model.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recorded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('p50_ms', sa.Numeric(10, 2), nullable=False),
        sa.Column('p95_ms', sa.Numeric(10, 2), nullable=False),
        sa.Column('p99_ms', sa.Numeric(10, 2), nullable=False),
        sa.Column('request_count', sa.Integer, nullable=False),
        sa.Column('window_minutes', sa.Integer, nullable=False, server_default='5'),
    )

    # Model error rates - error tracking with breakdown
    op.create_table(
        'model_error_rates',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_id', sa.String(255), sa.ForeignKey('ml_model.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recorded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('total_requests', sa.Integer, nullable=False),
        sa.Column('error_count', sa.Integer, nullable=False),
        sa.Column('error_types', JSONB, nullable=True),  # {"timeout": 5, "validation": 2}
        sa.Column('window_minutes', sa.Integer, nullable=False, server_default='5'),
    )

    # Model SLA configuration
    op.create_table(
        'model_sla_config',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_id', sa.String(255), sa.ForeignKey('ml_model.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('max_latency_p95_ms', sa.Integer, nullable=False, server_default='500'),
        sa.Column('max_error_rate_percent', sa.Numeric(5, 2), nullable=False, server_default='1.0'),
        sa.Column('alerting_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # SLA alerts - when SLA thresholds are breached
    op.create_table(
        'model_sla_alerts',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_id', sa.String(255), sa.ForeignKey('ml_model.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_type', sa.String(32), nullable=False),  # 'latency' or 'error_rate'
        sa.Column('threshold_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('actual_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('triggered_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
    )

    # Create indexes for efficient queries
    op.create_index('idx_latency_metrics_model', 'model_latency_metrics', ['model_id'])
    op.create_index('idx_latency_metrics_time', 'model_latency_metrics', ['recorded_at'])
    op.create_index('idx_latency_model_time', 'model_latency_metrics', ['model_id', 'recorded_at'])

    op.create_index('idx_error_rates_model', 'model_error_rates', ['model_id'])
    op.create_index('idx_error_rates_time', 'model_error_rates', ['recorded_at'])
    op.create_index('idx_error_model_time', 'model_error_rates', ['model_id', 'recorded_at'])

    op.create_index('idx_sla_alerts_model', 'model_sla_alerts', ['model_id'])
    op.create_index('idx_sla_alerts_time', 'model_sla_alerts', ['triggered_at'])
    op.create_index('idx_sla_alerts_unack', 'model_sla_alerts', ['model_id', 'acknowledged'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_sla_alerts_unack')
    op.drop_index('idx_sla_alerts_time')
    op.drop_index('idx_sla_alerts_model')

    op.drop_index('idx_error_model_time')
    op.drop_index('idx_error_rates_time')
    op.drop_index('idx_error_rates_model')

    op.drop_index('idx_latency_model_time')
    op.drop_index('idx_latency_metrics_time')
    op.drop_index('idx_latency_metrics_model')

    # Drop tables
    op.drop_table('model_sla_alerts')
    op.drop_table('model_sla_config')
    op.drop_table('model_error_rates')
    op.drop_table('model_latency_metrics')
