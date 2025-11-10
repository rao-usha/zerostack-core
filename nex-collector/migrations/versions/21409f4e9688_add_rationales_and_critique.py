"""add_rationales_and_critique

Revision ID: 21409f4e9688
Revises: 8f3c2d1a4e5b
Create Date: 2025-01-15 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '21409f4e9688'
down_revision: Union[str, None] = '8f3c2d1a4e5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add rationale_json to teacher_runs table
    op.add_column('teacher_runs', sa.Column('rationale_json', sa.JSON(), nullable=True))
    
    # Add justification and faithfulness_score to targets table
    op.add_column('targets', sa.Column('justification', sa.Text(), nullable=True))
    op.add_column('targets', sa.Column('faithfulness_score', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove rationale and critique fields
    op.drop_column('targets', 'faithfulness_score')
    op.drop_column('targets', 'justification')
    op.drop_column('teacher_runs', 'rationale_json')

