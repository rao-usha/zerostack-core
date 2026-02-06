"""Add persona versioning and assignment tables.

Note: The main 'personas' table already exists in the schema.
This migration adds supplementary tables for version history and user assignments.

Revision ID: 048_add_personas_tables
Revises: 047_add_governance_tables
Create Date: 2026-02-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

# revision identifiers
revision = '048_add_personas_tables'
down_revision = '047_add_governance_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Persona versions table - tracks history of persona changes
    op.create_table(
        'persona_versions',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('persona_id', UUID, sa.ForeignKey('personas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(32), nullable=False),
        sa.Column('snapshot', JSONB, nullable=False),
        sa.Column('changes', JSONB, server_default='{}'),
        sa.Column('change_reason', sa.Text),
        sa.Column('created_by', UUID),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_persona_versions_persona_id', 'persona_versions', ['persona_id'])
    op.create_index('ix_persona_versions_version', 'persona_versions', ['persona_id', 'version'])

    # Persona assignments table - links personas to users
    op.create_table(
        'persona_assignments',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('persona_id', UUID, sa.ForeignKey('personas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID, nullable=False),
        sa.Column('is_primary', sa.String(1), server_default='N'),
        sa.Column('assigned_by', UUID),
        sa.Column('assigned_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', TIMESTAMP(timezone=True)),
        sa.Column('notes', sa.Text),
    )

    op.create_index('ix_persona_assignments_persona_id', 'persona_assignments', ['persona_id'])
    op.create_index('ix_persona_assignments_user_id', 'persona_assignments', ['user_id'])


def downgrade():
    op.drop_index('ix_persona_assignments_user_id')
    op.drop_index('ix_persona_assignments_persona_id')
    op.drop_table('persona_assignments')

    op.drop_index('ix_persona_versions_version')
    op.drop_index('ix_persona_versions_persona_id')
    op.drop_table('persona_versions')
