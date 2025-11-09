"""create_quality_assessment_table

Revision ID: a1b2c3d4e5f6
Revises: cd0ee671309e
Create Date: 2025-01-15 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cd0ee671309e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create quality_assessments table
    op.create_table(
        'quality_assessments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('coherence', sa.Float(), nullable=True),
        sa.Column('faithfulness', sa.Float(), nullable=True),
        sa.Column('toxicity', sa.Float(), nullable=True),
        sa.Column('pii_flags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('readability', sa.Float(), nullable=True),
        sa.Column('completeness', sa.Float(), nullable=True),
        sa.Column('relevance', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('assessment_method', sa.String(), nullable=True),
        sa.Column('assessor_model', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_quality_assessments_entity_type'), 'quality_assessments', ['entity_type'], unique=False)
    op.create_index(op.f('ix_quality_assessments_entity_id'), 'quality_assessments', ['entity_id'], unique=False)
    op.create_index('ix_quality_assessments_entity', 'quality_assessments', ['entity_type', 'entity_id'], unique=False)
    
    # Remove old quality signal columns (but keep them for now to allow data migration)
    # We'll drop them in a later migration after data is migrated
    # op.drop_column('chunks', 'quality_scores_json')
    # op.drop_column('chunks', 'confidence')
    # op.drop_column('teacher_runs', 'quality_scores_json')
    # op.drop_column('teacher_runs', 'confidence')
    # op.drop_column('targets', 'quality_scores_json')
    # op.drop_column('targets', 'confidence')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_quality_assessments_entity', table_name='quality_assessments')
    op.drop_index(op.f('ix_quality_assessments_entity_id'), table_name='quality_assessments')
    op.drop_index(op.f('ix_quality_assessments_entity_type'), table_name='quality_assessments')
    
    # Drop table
    op.drop_table('quality_assessments')

