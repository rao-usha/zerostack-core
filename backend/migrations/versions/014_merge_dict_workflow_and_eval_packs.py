"""Merge dictionary workflow and evaluation packs branches

Revision ID: 014_merge_heads
Revises: 013_dict_state_workflow, 010_add_evaluation_packs
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014_merge_heads'
down_revision = ('013_dict_state_workflow', '010_add_evaluation_packs')
branch_labels = None
depends_on = None


def upgrade():
    """Merge migration - no changes needed."""
    pass


def downgrade():
    """Merge migration - no changes needed."""
    pass
