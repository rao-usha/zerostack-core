"""Add AI analysis tables for storing analysis results

Revision ID: 003
Revises: 002
Create Date: 2024-11-30

Tables:
- ai_analysis_results: Stores AI-powered data analysis results and insights
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, ARRAY

# revision identifiers, used by Alembic.
revision = '003_ai_analysis'
down_revision = '002_chat'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_analysis_results table
    op.create_table(
        'ai_analysis_results',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, comment='User-friendly name for the analysis'),
        sa.Column('description', sa.Text, nullable=True, comment='Optional description'),
        
        # Analysis configuration
        sa.Column('tables', JSONB, nullable=False, comment='List of tables analyzed: [{"schema": "x", "table": "y"}]'),
        sa.Column('analysis_types', ARRAY(sa.String), nullable=False, comment='Types of analysis performed'),
        sa.Column('provider', sa.String(50), nullable=False, comment='LLM provider used: openai, anthropic, google, xai'),
        sa.Column('model', sa.String(100), nullable=False, comment='Model name used for analysis'),
        sa.Column('context', sa.Text, nullable=True, comment='Business context provided'),
        
        # Analysis results
        sa.Column('insights', JSONB, nullable=False, comment='Structured analysis insights'),
        sa.Column('summary', sa.Text, nullable=False, comment='Executive summary of findings'),
        sa.Column('recommendations', ARRAY(sa.String), nullable=True, comment='Actionable recommendations'),
        
        # Metadata
        sa.Column('execution_metadata', JSONB, nullable=True, comment='Execution metrics: time, tokens, etc.'),
        sa.Column('tags', ARRAY(sa.String), nullable=True, comment='User-defined tags for organization'),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        
        # Database connection
        sa.Column('db_id', sa.String(100), nullable=False, server_default='default', comment='Database connection ID'),
    )
    
    # Create indexes
    op.create_index('ix_ai_analysis_results_created_at', 'ai_analysis_results', ['created_at'], postgresql_using='btree')
    op.create_index('ix_ai_analysis_results_provider', 'ai_analysis_results', ['provider'])
    op.create_index('ix_ai_analysis_results_db_id', 'ai_analysis_results', ['db_id'])
    op.create_index('ix_ai_analysis_results_name', 'ai_analysis_results', ['name'])
    
    # Create GIN indexes for JSONB columns (for efficient querying)
    op.create_index('ix_ai_analysis_results_tables_gin', 'ai_analysis_results', ['tables'], postgresql_using='gin')
    op.create_index('ix_ai_analysis_results_insights_gin', 'ai_analysis_results', ['insights'], postgresql_using='gin')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_ai_analysis_results_insights_gin', table_name='ai_analysis_results')
    op.drop_index('ix_ai_analysis_results_tables_gin', table_name='ai_analysis_results')
    op.drop_index('ix_ai_analysis_results_name', table_name='ai_analysis_results')
    op.drop_index('ix_ai_analysis_results_db_id', table_name='ai_analysis_results')
    op.drop_index('ix_ai_analysis_results_provider', table_name='ai_analysis_results')
    op.drop_index('ix_ai_analysis_results_created_at', table_name='ai_analysis_results')
    
    # Drop table
    op.drop_table('ai_analysis_results')

