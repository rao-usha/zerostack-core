"""add_provenance_fields

Revision ID: 3263bfa77cad
Revises: b55c2ae4aae0
Create Date: 2025-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3263bfa77cad'
down_revision: Union[str, None] = '9e99adff2396'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add provenance fields to chunks table
    op.add_column('chunks', sa.Column('source_uri', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('source_span', sa.JSON(), nullable=True))
    op.add_column('chunks', sa.Column('citation_ids', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('chunks', sa.Column('text_hash', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('license', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('usage_rights', sa.String(), nullable=True))
    op.create_index(op.f('ix_chunks_text_hash'), 'chunks', ['text_hash'], unique=False)
    
    # Add provenance fields to synthetic_examples table
    op.add_column('synthetic_examples', sa.Column('source_uri', sa.String(), nullable=True))
    op.add_column('synthetic_examples', sa.Column('source_span', sa.JSON(), nullable=True))
    op.add_column('synthetic_examples', sa.Column('citation_ids', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('synthetic_examples', sa.Column('text_hash', sa.String(), nullable=True))
    op.add_column('synthetic_examples', sa.Column('license', sa.String(), nullable=True))
    op.add_column('synthetic_examples', sa.Column('usage_rights', sa.String(), nullable=True))
    op.create_index(op.f('ix_synthetic_examples_text_hash'), 'synthetic_examples', ['text_hash'], unique=False)
    
    # Add provenance fields to targets table
    op.add_column('targets', sa.Column('source_uri', sa.String(), nullable=True))
    op.add_column('targets', sa.Column('source_span', sa.JSON(), nullable=True))
    op.add_column('targets', sa.Column('citation_ids', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    # Remove provenance fields from targets table
    op.drop_column('targets', 'citation_ids')
    op.drop_column('targets', 'source_span')
    op.drop_column('targets', 'source_uri')
    
    # Remove provenance fields from synthetic_examples table
    op.drop_index(op.f('ix_synthetic_examples_text_hash'), table_name='synthetic_examples')
    op.drop_column('synthetic_examples', 'usage_rights')
    op.drop_column('synthetic_examples', 'license')
    op.drop_column('synthetic_examples', 'text_hash')
    op.drop_column('synthetic_examples', 'citation_ids')
    op.drop_column('synthetic_examples', 'source_span')
    op.drop_column('synthetic_examples', 'source_uri')
    
    # Remove provenance fields from chunks table
    op.drop_index(op.f('ix_chunks_text_hash'), table_name='chunks')
    op.drop_column('chunks', 'usage_rights')
    op.drop_column('chunks', 'license')
    op.drop_column('chunks', 'text_hash')
    op.drop_column('chunks', 'citation_ids')
    op.drop_column('chunks', 'source_span')
    op.drop_column('chunks', 'source_uri')

