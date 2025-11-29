"""add_teacher_ensemble_fields

Revision ID: 8f3c2d1a4e5b
Revises: 69a1af4915b7
Create Date: 2025-01-15 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8f3c2d1a4e5b'
down_revision: Union[str, None] = '69a1af4915b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add teacher ensemble & reproducibility fields to teacher_runs table
    op.add_column('teacher_runs', sa.Column('rand_seed', sa.Integer(), nullable=True))
    op.add_column('teacher_runs', sa.Column('temperature', sa.Float(), nullable=True))
    op.add_column('teacher_runs', sa.Column('decoding_params', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove teacher ensemble fields from teacher_runs table
    op.drop_column('teacher_runs', 'decoding_params')
    op.drop_column('teacher_runs', 'temperature')
    op.drop_column('teacher_runs', 'rand_seed')

