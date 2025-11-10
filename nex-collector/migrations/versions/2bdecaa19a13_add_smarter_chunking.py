"""add_smarter_chunking

Revision ID: 2bdecaa19a13
Revises: adbf98c51dd5
Create Date: 2025-01-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2bdecaa19a13'
down_revision: Union[str, None] = 'adbf98c51dd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add smarter chunking fields to chunks table
    op.add_column('chunks', sa.Column('neighbors', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('chunks', sa.Column('section_hierarchy', sa.JSON(), nullable=True))
    op.add_column('chunks', sa.Column('chunk_type', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('overlap_start', sa.Integer(), nullable=True))
    op.add_column('chunks', sa.Column('overlap_end', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove smarter chunking fields from chunks table
    op.drop_column('chunks', 'overlap_end')
    op.drop_column('chunks', 'overlap_start')
    op.drop_column('chunks', 'chunk_type')
    op.drop_column('chunks', 'section_hierarchy')
    op.drop_column('chunks', 'neighbors')

