"""remove_underwriting_runs_table

Revision ID: 9e99adff2396
Revises: b55c2ae4aae0
Create Date: 2025-11-08 20:58:33.127380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9e99adff2396'
down_revision: Union[str, None] = 'b55c2ae4aae0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the underwriting_runs table
    op.drop_table('underwriting_runs')
    
    # Drop the UnderwritingDecision enum if it exists and is not used elsewhere
    # Note: PostgreSQL doesn't automatically drop enums, so we check first
    op.execute("DROP TYPE IF EXISTS underwritingdecision")


def downgrade() -> None:
    # Recreate the enum if it doesn't exist
    op.execute("DO $$ BEGIN CREATE TYPE underwritingdecision AS ENUM ('approve', 'hold', 'reject'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Recreate the table
    op.create_table('underwriting_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('variant_id', sa.String(), nullable=False),
    sa.Column('rubric_id', sa.String(), nullable=True),
    sa.Column('metrics_json', sa.JSON(), nullable=False),
    sa.Column('risk_score', sa.Integer(), nullable=False),
    sa.Column('utility_score', sa.Integer(), nullable=False),
    sa.Column('decision', postgresql.ENUM('approve', 'hold', 'reject', name='underwritingdecision'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['variant_id'], ['context_variants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

