"""Add state column for dictionary approval workflow

Revision ID: 013_add_dictionary_state_workflow
Revises: 012_add_dictionary_semantics
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_dict_state_workflow'
down_revision = '012_dict_semantics'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add state column to data_dictionary_entries to support approval workflow.
    
    States:
    - draft: Working copy, can be edited freely (default)
    - pending_approval: Submitted for review, cannot be edited
    - published: Approved and immutable, visible to all
    """
    # Add state column with default 'draft'
    op.add_column(
        'data_dictionary_entries',
        sa.Column('state', sa.String(length=50), nullable=False, server_default='draft')
    )
    
    # Add index on state for faster queries
    op.create_index(
        'ix_data_dictionary_entries_state',
        'data_dictionary_entries',
        ['state']
    )
    
    # Mark all existing entries as 'published' (they're already approved/active)
    # This ensures backward compatibility
    op.execute("""
        UPDATE data_dictionary_entries 
        SET state = 'published' 
        WHERE is_active = true
    """)
    
    # Draft entries (inactive) remain as draft
    # (Actually, most inactive are old versions, so let's mark them as published too)
    op.execute("""
        UPDATE data_dictionary_entries 
        SET state = 'published' 
        WHERE is_active = false
    """)


def downgrade():
    """Remove state column."""
    op.drop_index('ix_data_dictionary_entries_state', table_name='data_dictionary_entries')
    op.drop_column('data_dictionary_entries', 'state')
