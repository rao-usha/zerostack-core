"""add_retrieval_context_ids

Revision ID: 69a1af4915b7
Revises: 2bdecaa19a13
Create Date: 2025-01-15 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '69a1af4915b7'
down_revision: Union[str, None] = '2bdecaa19a13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add retrieval_context_ids to synthetic_examples table for MMR tracking
    op.add_column('synthetic_examples', sa.Column('retrieval_context_ids', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    # Remove retrieval_context_ids from synthetic_examples table
    op.drop_column('synthetic_examples', 'retrieval_context_ids')

