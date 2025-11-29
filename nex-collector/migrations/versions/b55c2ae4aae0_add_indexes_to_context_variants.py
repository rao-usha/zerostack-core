"""add_indexes_to_context_variants

Revision ID: b55c2ae4aae0
Revises: fa550a1d08b9
Create Date: 2025-11-08 20:35:24.159993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b55c2ae4aae0'
down_revision: Union[str, None] = 'fa550a1d08b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes to context_variants for better query performance
    op.create_index(op.f('ix_context_variants_context_id'), 'context_variants', ['context_id'], unique=False)
    op.create_index(op.f('ix_context_variants_domain'), 'context_variants', ['domain'], unique=False)
    op.create_index(op.f('ix_context_variants_persona'), 'context_variants', ['persona'], unique=False)
    op.create_index(op.f('ix_context_variants_task'), 'context_variants', ['task'], unique=False)


def downgrade() -> None:
    # Remove indexes (with if_exists check)
    op.execute("DROP INDEX IF EXISTS ix_context_variants_task")
    op.execute("DROP INDEX IF EXISTS ix_context_variants_persona")
    op.execute("DROP INDEX IF EXISTS ix_context_variants_domain")
    op.execute("DROP INDEX IF EXISTS ix_context_variants_context_id")

