"""Add quality_rating to distillation_responses

Revision ID: 016_add_response_quality_rating
Revises: 015_add_distillation_workbench
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '016_add_response_quality_rating'
down_revision = '015_add_distillation_workbench'
branch_labels = None
depends_on = None


def upgrade():
    # Add quality_rating column to distillation_responses
    op.add_column('distillation_responses', sa.Column('quality_rating', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('distillation_responses', 'quality_rating')
