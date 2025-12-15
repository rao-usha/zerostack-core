"""Add prompt_recipes table for editable analysis prompts.

Revision ID: 006_add_prompt_recipes
Revises: 005_add_analysis_jobs
Create Date: 2025-12-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_recipes'
down_revision = '005_jobs'
branch_labels = None
depends_on = None


def upgrade():
    """Create prompt_recipes table."""
    op.create_table(
        'prompt_recipes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('default_provider', sa.String(length=50), nullable=True),
        sa.Column('default_model', sa.String(length=100), nullable=True),
        sa.Column('system_message', sa.Text(), nullable=False),
        sa.Column('user_template', sa.Text(), nullable=False),
        sa.Column('recipe_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_recipes_name', 'prompt_recipes', ['name'])
    op.create_index('ix_prompt_recipes_action_type', 'prompt_recipes', ['action_type'])
    op.create_index('ix_prompt_recipes_default_provider', 'prompt_recipes', ['default_provider'])


def downgrade():
    """Drop prompt_recipes table."""
    op.drop_index('ix_prompt_recipes_default_provider', table_name='prompt_recipes')
    op.drop_index('ix_prompt_recipes_action_type', table_name='prompt_recipes')
    op.drop_index('ix_prompt_recipes_name', table_name='prompt_recipes')
    op.drop_table('prompt_recipes')

