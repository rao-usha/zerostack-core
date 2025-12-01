"""Add prompt_recipe_id and prompt_overrides to analysis_jobs.

Revision ID: 007_recipe_fields
Revises: 006_recipes
Create Date: 2025-12-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_recipe_fields'
down_revision = '006_recipes'
branch_labels = None
depends_on = None


def upgrade():
    """Add recipe-related columns to analysis_jobs table."""
    op.add_column('analysis_jobs', sa.Column('prompt_recipe_id', sa.Integer(), nullable=True))
    op.add_column('analysis_jobs', sa.Column('prompt_overrides', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    """Remove recipe-related columns from analysis_jobs table."""
    op.drop_column('analysis_jobs', 'prompt_overrides')
    op.drop_column('analysis_jobs', 'prompt_recipe_id')

