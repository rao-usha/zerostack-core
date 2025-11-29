"""add_deduplication_and_drift_control

Revision ID: cd0ee671309e
Revises: 21409f4e9688
Create Date: 2025-01-15 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cd0ee671309e'
down_revision: Union[str, None] = '21409f4e9688'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add semantic_hash to synthetic_examples table for near-duplicate detection
    op.add_column('synthetic_examples', sa.Column('semantic_hash', sa.String(), nullable=True))
    op.create_index(op.f('ix_synthetic_examples_semantic_hash'), 'synthetic_examples', ['semantic_hash'], unique=False)
    
    # Add embedding_centroid to context_docs table for drift detection
    op.add_column('context_docs', sa.Column('embedding_centroid', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove embedding_centroid from context_docs table
    op.drop_column('context_docs', 'embedding_centroid')
    
    # Remove semantic_hash from synthetic_examples table
    op.drop_index(op.f('ix_synthetic_examples_semantic_hash'), table_name='synthetic_examples')
    op.drop_column('synthetic_examples', 'semantic_hash')

