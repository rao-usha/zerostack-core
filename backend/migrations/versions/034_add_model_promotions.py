"""Add model promotion history table.

Revision ID: 034
Revises: 033
Create Date: 2026-01-23

Adds table for tracking model promotion/demotion history.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers
revision = '034_add_model_promotions'
down_revision = '033_add_cost_budgets'
branch_labels = None
depends_on = None


def upgrade():
    # Model promotions - history of status changes
    op.create_table(
        'ml_model_promotions',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_id', sa.String(255), sa.ForeignKey('ml_model.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_status', sa.String(32), nullable=False),
        sa.Column('to_status', sa.String(32), nullable=False),
        sa.Column('promoted_by', sa.String(255), nullable=True),
        sa.Column('promotion_notes', sa.Text, nullable=True),
        sa.Column('validation_results', JSONB, nullable=True),  # Results of promotion validation
        sa.Column('promoted_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_model_promotions_model', 'ml_model_promotions', ['model_id'])
    op.create_index('idx_model_promotions_time', 'ml_model_promotions', ['promoted_at'])
    op.create_index('idx_model_promotions_to_status', 'ml_model_promotions', ['to_status'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_model_promotions_to_status')
    op.drop_index('idx_model_promotions_time')
    op.drop_index('idx_model_promotions_model')

    # Drop table
    op.drop_table('ml_model_promotions')
