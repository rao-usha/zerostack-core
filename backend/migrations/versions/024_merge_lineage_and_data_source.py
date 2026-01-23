"""Merge lineage tracking and data source branches

Revision ID: 024_merge_heads
Revises: 023_add_lineage_tracking, 023_add_source_to_dictionary
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '024_merge_heads'
down_revision = ('023_add_lineage_tracking', '023_add_source_to_dictionary')
branch_labels = None
depends_on = None


def upgrade():
    """Merge branches - no schema changes needed."""
    pass


def downgrade():
    """Merge downgrade - no schema changes needed."""
    pass
