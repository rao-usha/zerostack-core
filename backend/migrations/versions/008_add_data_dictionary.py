"""Add data_dictionary_entries table for persistent column documentation.

Revision ID: 008_dictionary
Revises: 007_recipe_fields
Create Date: 2025-12-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_dictionary'
down_revision = '007_recipe_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Create data_dictionary_entries table."""
    op.create_table(
        'data_dictionary_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('database_name', sa.String(length=255), nullable=False),
        sa.Column('schema_name', sa.String(length=255), nullable=False),
        sa.Column('table_name', sa.String(length=255), nullable=False),
        sa.Column('column_name', sa.String(length=255), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('business_description', sa.Text(), nullable=True),
        sa.Column('technical_description', sa.Text(), nullable=True),
        sa.Column('data_type', sa.String(length=100), nullable=True),
        sa.Column('examples', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_data_dictionary_entries_database_name', 'data_dictionary_entries', ['database_name'])
    op.create_index('ix_data_dictionary_entries_schema_name', 'data_dictionary_entries', ['schema_name'])
    op.create_index('ix_data_dictionary_entries_table_name', 'data_dictionary_entries', ['table_name'])
    op.create_index('ix_data_dictionary_entries_column_name', 'data_dictionary_entries', ['column_name'])
    
    # Create unique constraint on (database, schema, table, column)
    op.create_unique_constraint(
        'uq_dictionary_entry',
        'data_dictionary_entries',
        ['database_name', 'schema_name', 'table_name', 'column_name']
    )


def downgrade():
    """Drop data_dictionary_entries table."""
    op.drop_constraint('uq_dictionary_entry', 'data_dictionary_entries', type_='unique')
    op.drop_index('ix_data_dictionary_entries_column_name', table_name='data_dictionary_entries')
    op.drop_index('ix_data_dictionary_entries_table_name', table_name='data_dictionary_entries')
    op.drop_index('ix_data_dictionary_entries_schema_name', table_name='data_dictionary_entries')
    op.drop_index('ix_data_dictionary_entries_database_name', table_name='data_dictionary_entries')
    op.drop_table('data_dictionary_entries')

