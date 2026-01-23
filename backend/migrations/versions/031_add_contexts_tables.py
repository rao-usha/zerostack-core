"""add contexts tables

Revision ID: 031_add_contexts
Revises: 030_add_feature_store
Create Date: 2025-01-20

Creates the contexts, context_layers, context_versions, context_dictionaries,
context_documents, orgs, and related tables if they don't exist.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '031_add_contexts'
down_revision: Union[str, None] = ('030_add_feature_store', 'a8ede7c1f5bb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists."""
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :name)"
    ), {"name": table_name})
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # Create orgs table if not exists
    if not table_exists(conn, 'orgs'):
        op.create_table(
            'orgs',
            sa.Column('id', postgresql.UUID(), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False, unique=True),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )

    # Create contexts table if not exists
    if not table_exists(conn, 'contexts'):
        op.create_table(
            'contexts',
            sa.Column('id', postgresql.UUID(), primary_key=True),
            sa.Column('org_id', postgresql.UUID(), sa.ForeignKey('orgs.id'), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('metadata', postgresql.JSON(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )

    # Create context_versions table if not exists
    if not table_exists(conn, 'context_versions'):
        op.create_table(
            'context_versions',
            sa.Column('id', postgresql.UUID(), primary_key=True),
            sa.Column('context_id', postgresql.UUID(), sa.ForeignKey('contexts.id'), nullable=False),
            sa.Column('version', sa.String(64), nullable=False),
            sa.Column('digest', sa.String(64), nullable=False),
            sa.Column('data_refs', postgresql.JSON(), nullable=False, server_default='[]'),
            sa.Column('layers', postgresql.JSON(), nullable=False, server_default='[]'),
            sa.Column('diff_summary', sa.Text()),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )

    # Create context_layers table if not exists
    if not table_exists(conn, 'context_layers'):
        op.create_table(
            'context_layers',
            sa.Column('id', postgresql.UUID(), primary_key=True),
            sa.Column('context_id', postgresql.UUID(), sa.ForeignKey('contexts.id'), nullable=False),
            sa.Column('kind', sa.String(64), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('spec', postgresql.JSON(), nullable=False, server_default='{}'),
            sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
            sa.Column('order', sa.Integer(), nullable=False, default=0),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )

    # Create context_dictionaries table if not exists
    if not table_exists(conn, 'context_dictionaries'):
        op.create_table(
            'context_dictionaries',
            sa.Column('id', postgresql.UUID(), primary_key=True),
            sa.Column('context_id', postgresql.UUID(), sa.ForeignKey('contexts.id'), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('entries', postgresql.JSON(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )

    # Create context_documents table if not exists
    if not table_exists(conn, 'context_documents'):
        op.create_table(
            'context_documents',
            sa.Column('id', postgresql.UUID(), primary_key=True),
            sa.Column('context_id', postgresql.UUID(), sa.ForeignKey('contexts.id'), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('filename', sa.String(512), nullable=False),
            sa.Column('storage_path', sa.String(512), nullable=False),
            sa.Column('content_type', sa.String(128), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('sha256', sa.String(64), nullable=True),
            sa.Column('summary', sa.Text()),
            sa.Column('text_content', sa.Text()),
            sa.Column('metadata', postgresql.JSON(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        )


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_table('context_documents')
    op.drop_table('context_dictionaries')
    op.drop_table('context_layers')
    op.drop_table('context_versions')
    op.drop_table('contexts')
    op.drop_table('orgs')
