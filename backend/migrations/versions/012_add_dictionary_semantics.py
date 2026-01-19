"""Add dictionary semantics, grains, and relationships.

Revision ID: 012_dict_semantics
Revises: 011_enhanced_dict
Create Date: 2025-12-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_dict_semantics'
down_revision = '011_enhanced_dict'
branch_labels = None
depends_on = None


def upgrade():
    """Create dictionary semantics tables."""
    
    # 1. Create unified dictionary_entries table (if not exists, else we'll use existing data_dictionary_entries)
    # Since data_dictionary_entries exists for columns, we'll create a new unified one
    op.create_table(
        'dictionary_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entry_type', sa.String(length=50), nullable=False),  # database, schema, table, column, concept
        sa.Column('database_name', sa.String(length=255), nullable=True),
        sa.Column('schema_name', sa.String(length=255), nullable=True),
        sa.Column('table_name', sa.String(length=255), nullable=True),
        sa.Column('column_name', sa.String(length=255), nullable=True),
        sa.Column('concept_name', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for dictionary_entries
    op.create_index('ix_dict_entries_type', 'dictionary_entries', ['entry_type'])
    op.create_index('ix_dict_entries_database', 'dictionary_entries', ['database_name'])
    op.create_index('ix_dict_entries_schema', 'dictionary_entries', ['schema_name'])
    op.create_index('ix_dict_entries_table', 'dictionary_entries', ['table_name'])
    op.create_index('ix_dict_entries_column', 'dictionary_entries', ['column_name'])
    op.create_index('ix_dict_entries_concept', 'dictionary_entries', ['concept_name'])
    
    # Composite index for lookups
    op.create_index(
        'ix_dict_entries_lookup',
        'dictionary_entries',
        ['entry_type', 'database_name', 'schema_name', 'table_name', 'column_name']
    )
    
    # 2. Create dictionary_entry_versions table
    op.create_table(
        'dictionary_entry_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entry_id'], ['dictionary_entries.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_dict_versions_entry_id', 'dictionary_entry_versions', ['entry_id'])
    op.create_index('ix_dict_versions_version', 'dictionary_entry_versions', ['version'])
    op.create_unique_constraint(
        'uq_dict_version',
        'dictionary_entry_versions',
        ['entry_id', 'version']
    )
    
    # 3. Create dictionary_entry_semantics table
    op.create_table(
        'dictionary_entry_semantics',
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('semantic_guarantees', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('validation_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('entry_id'),
        sa.ForeignKeyConstraint(['entry_id'], ['dictionary_entries.id'], ondelete='CASCADE')
    )
    
    # 4. Create dictionary_grains table
    op.create_table(
        'dictionary_grains',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity', sa.Text(), nullable=False),
        sa.Column('primary_key', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('time_grain', sa.String(length=100), nullable=True),
        sa.Column('natural_key', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entry_id'], ['dictionary_entries.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_dict_grains_entry_id', 'dictionary_grains', ['entry_id'])
    op.create_unique_constraint('uq_dict_grain_entry', 'dictionary_grains', ['entry_id'])
    
    # 5. Create dictionary_relationships table
    op.create_table(
        'dictionary_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('relationship_kind', sa.String(length=50), nullable=False),  # candidate, semantic
        sa.Column('status', sa.String(length=50), nullable=False, server_default='suggested'),  # suggested, approved, rejected, deprecated
        sa.Column('left_entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('right_entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('left_ref', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('right_ref', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('relationship_type', sa.String(length=100), nullable=False),
        sa.Column('cardinality', sa.String(length=50), nullable=True),
        sa.Column('match_rate_sample', sa.Float(), nullable=True),
        sa.Column('left_null_rate', sa.Float(), nullable=True),
        sa.Column('right_unique', sa.Boolean(), nullable=True),
        sa.Column('suggested_join_sql', sa.Text(), nullable=True),
        sa.Column('grain_compatibility', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('semantic_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['left_entry_id'], ['dictionary_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['right_entry_id'], ['dictionary_entries.id'], ondelete='CASCADE')
    )
    
    # Indexes for dictionary_relationships
    op.create_index('ix_dict_rels_left_entry', 'dictionary_relationships', ['left_entry_id'])
    op.create_index('ix_dict_rels_right_entry', 'dictionary_relationships', ['right_entry_id'])
    op.create_index('ix_dict_rels_kind', 'dictionary_relationships', ['relationship_kind'])
    op.create_index('ix_dict_rels_status', 'dictionary_relationships', ['status'])
    op.create_index('ix_dict_rels_type', 'dictionary_relationships', ['relationship_type'])
    
    # 6. Create dictionary_inference_jobs table for tracking inference runs
    op.create_table(
        'dictionary_inference_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('connection_id', sa.String(length=100), nullable=False),
        sa.Column('schema_name', sa.String(length=255), nullable=True),
        sa.Column('include_tables', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('exclude_tables', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('max_samples', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_stage', sa.String(length=255), nullable=True),
        sa.Column('relationships_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tables_scanned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_dict_infer_jobs_status', 'dictionary_inference_jobs', ['status'])
    op.create_index('ix_dict_infer_jobs_created', 'dictionary_inference_jobs', ['created_at'])


def downgrade():
    """Drop dictionary semantics tables."""
    op.drop_table('dictionary_inference_jobs')
    op.drop_table('dictionary_relationships')
    op.drop_table('dictionary_grains')
    op.drop_table('dictionary_entry_semantics')
    op.drop_table('dictionary_entry_versions')
    op.drop_table('dictionary_entries')

