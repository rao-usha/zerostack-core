"""bootstrap nex schema

Revision ID: 001_bootstrap
Revises: 
Create Date: 2025-11-02 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_bootstrap'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import metadata and models to create all tables
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        from backend.db.meta import METADATA
        from backend.db import models  # noqa: F401
    except ImportError:
        from db.meta import METADATA
        from db import models  # noqa: F401
    
    # Create all tables
    METADATA.create_all(op.get_bind())


def downgrade() -> None:
    # Drop all tables in reverse order
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        from backend.db.meta import METADATA
    except ImportError:
        from db.meta import METADATA
    
    for table in reversed(METADATA.sorted_tables):
        op.drop_table(table.name)

