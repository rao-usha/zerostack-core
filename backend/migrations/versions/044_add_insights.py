"""Add insight_reports table for persisting generated insights.

Revision ID: 044_add_insights
Revises: 043_add_approval_requests
Create Date: 2026-01-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, TIMESTAMP

# revision identifiers
revision = '044_add_insights'
down_revision = '043_add_approval_requests'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'insight_reports',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('dataset_id', UUID, nullable=False),

        # Report metadata
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('context', sa.String(500), nullable=True),

        # Performance & executive metrics
        sa.Column('performance_score', JSONB, nullable=True),
        sa.Column('executive_kpis', JSONB, nullable=True),

        # Trend and growth data
        sa.Column('trend_data', JSONB, nullable=True),
        sa.Column('growth_metrics', JSONB, nullable=True),

        # Risk and distribution
        sa.Column('risk_indicators', JSONB, nullable=True),
        sa.Column('distribution_data', JSONB, nullable=True),

        # Recommendations
        sa.Column('recommendations', ARRAY(sa.String), nullable=True),

        # Summary
        sa.Column('summary', sa.Text, server_default=''),

        # Detailed analytics
        sa.Column('trends', JSONB, nullable=True),
        sa.Column('anomalies', JSONB, nullable=True),
        sa.Column('correlations', JSONB, nullable=True),
        sa.Column('key_metrics', JSONB, nullable=True),

        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_insight_reports_dataset_id', 'insight_reports', ['dataset_id'])
    op.create_index('ix_insight_reports_created_at', 'insight_reports', ['created_at'])


def downgrade():
    op.drop_index('ix_insight_reports_created_at')
    op.drop_index('ix_insight_reports_dataset_id')
    op.drop_table('insight_reports')
