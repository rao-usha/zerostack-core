"""add_quality_signals

Revision ID: adbf98c51dd5
Revises: 3263bfa77cad
Create Date: 2025-01-15 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'adbf98c51dd5'
down_revision: Union[str, None] = '3263bfa77cad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add quality signals to chunks table
    op.add_column('chunks', sa.Column('quality_scores_json', sa.JSON(), nullable=True))
    op.add_column('chunks', sa.Column('confidence', sa.Float(), nullable=True))
    
    # Add quality signals to teacher_runs table
    op.add_column('teacher_runs', sa.Column('quality_scores_json', sa.JSON(), nullable=True))
    op.add_column('teacher_runs', sa.Column('confidence', sa.Float(), nullable=True))
    
    # Add quality signals to targets table
    op.add_column('targets', sa.Column('quality_scores_json', sa.JSON(), nullable=True))
    op.add_column('targets', sa.Column('confidence', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove quality signals from targets table
    op.drop_column('targets', 'confidence')
    op.drop_column('targets', 'quality_scores_json')
    
    # Remove quality signals from teacher_runs table
    op.drop_column('teacher_runs', 'confidence')
    op.drop_column('teacher_runs', 'quality_scores_json')
    
    # Remove quality signals from chunks table
    op.drop_column('chunks', 'confidence')
    op.drop_column('chunks', 'quality_scores_json')

