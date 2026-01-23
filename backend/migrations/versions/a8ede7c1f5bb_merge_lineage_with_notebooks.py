"""merge lineage with notebooks

Revision ID: a8ede7c1f5bb
Revises: 019_add_data_lineage, 026_add_notebooks
Create Date: 2026-01-15 20:24:33.465000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8ede7c1f5bb'
down_revision: Union[str, None] = ('019_add_data_lineage', '026_add_notebooks')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

