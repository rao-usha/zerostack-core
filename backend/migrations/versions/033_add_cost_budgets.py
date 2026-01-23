"""Add cost budget tables.

Revision ID: 033
Revises: 032
Create Date: 2026-01-23

Adds tables for cost budget tracking:
- cost_budgets: Budget configuration
- cost_budget_alerts: Alerts when thresholds are exceeded
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = '033_add_cost_budgets'
down_revision = '032_add_drift_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Cost budgets - budget configuration
    op.create_table(
        'cost_budgets',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('budget_amount_usd', sa.Numeric(12, 4), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),  # daily, weekly, monthly
        sa.Column('alert_threshold_percent', sa.Integer, nullable=False, server_default='80'),

        # Scope - what the budget applies to
        sa.Column('scope_type', sa.String(20), nullable=False, server_default='global'),  # global, provider, model
        sa.Column('scope_id', sa.String(255), nullable=True),  # Provider name or model ID

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Cost budget alerts - alerts triggered when thresholds exceeded
    op.create_table(
        'cost_budget_alerts',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('budget_id', UUID, sa.ForeignKey('cost_budgets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('triggered_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('current_spend_usd', sa.Numeric(12, 4), nullable=False),
        sa.Column('budget_amount_usd', sa.Numeric(12, 4), nullable=False),
        sa.Column('percent_used', sa.Integer, nullable=False),
    )

    # Create indexes
    op.create_index('idx_cost_budgets_active', 'cost_budgets', ['is_active'])
    op.create_index('idx_cost_budgets_scope', 'cost_budgets', ['scope_type', 'scope_id'])
    op.create_index('idx_cost_budget_alerts_budget', 'cost_budget_alerts', ['budget_id'])
    op.create_index('idx_cost_budget_alerts_triggered', 'cost_budget_alerts', ['triggered_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_cost_budget_alerts_triggered')
    op.drop_index('idx_cost_budget_alerts_budget')
    op.drop_index('idx_cost_budgets_scope')
    op.drop_index('idx_cost_budgets_active')

    # Drop tables
    op.drop_table('cost_budget_alerts')
    op.drop_table('cost_budgets')
