"""merge versioning and ml branches

Revision ID: 297d473edc6b
Revises: 009_versioning, 009_ml_development
Create Date: 2025-12-14 23:51:24.552153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '297d473edc6b'
down_revision: Union[str, None] = ('009_versioning', '009_ml_development')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

