"""add distillation workbench tables

Revision ID: 015_add_distillation_workbench
Revises: 014_merge_dict_workflow_and_eval_packs
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID, ARRAY
# Note: pgvector embedding column commented out for now - can add later
# from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '015_add_distillation_workbench'
down_revision = '014_merge_heads'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # Domain & Topic Hierarchy
    # ========================================
    
    # Domains (Insurance, Finance, Retail, etc.)
    op.create_table(
        'distillation_domains',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),  # Hex color
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Topics within domains (hierarchical)
    op.create_table(
        'distillation_topics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_topic_id', UUID(as_uuid=True), sa.ForeignKey('distillation_topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('domain_id', 'name', name='uq_topic_domain_name'),
    )
    
    # Freeform tags
    op.create_table(
        'distillation_tags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('color', sa.String(7), nullable=True),  # Hex color for UI
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # ========================================
    # Task Library (Automated Capture)
    # ========================================
    
    op.create_table(
        'distillation_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Organization
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic_id', UUID(as_uuid=True), sa.ForeignKey('distillation_topics.id', ondelete='SET NULL'), nullable=True),
        
        # Task configuration
        sa.Column('task_type', sa.String(50), nullable=False),  # 'qa', 'summary', 'instruction', 'freeform'
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('variables', JSON, nullable=False, server_default='[]'),  # [{name, type, default, required}]
        
        # Model targeting
        sa.Column('target_models', ARRAY(sa.String), nullable=False),  # ['gpt-4o', 'claude-3.5-sonnet']
        
        # Scheduling
        sa.Column('schedule_cron', sa.String(100), nullable=True),  # null = manual only
        sa.Column('schedule_enabled', sa.Boolean(), nullable=False, server_default='false'),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        
        # Metadata
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # ========================================
    # Runs & Responses
    # ========================================
    
    op.create_table(
        'distillation_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('distillation_tasks.id', ondelete='SET NULL'), nullable=True),
        
        # For ad-hoc/interactive runs without a task
        sa.Column('ad_hoc_prompt', sa.Text(), nullable=True),
        sa.Column('ad_hoc_system_prompt', sa.Text(), nullable=True),
        sa.Column('ad_hoc_models', ARRAY(sa.String), nullable=True),
        
        # Execution context
        sa.Column('variables_used', JSON, nullable=False, server_default='{}'),
        sa.Column('trigger_type', sa.String(20), nullable=False),  # 'manual', 'scheduled', 'interactive'
        
        # Organization (can inherit from task or set manually)
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic_id', UUID(as_uuid=True), sa.ForeignKey('distillation_topics.id', ondelete='SET NULL'), nullable=True),
        
        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # 'pending', 'running', 'completed', 'failed'
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Timing
        sa.Column('scheduled_for', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_table(
        'distillation_responses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', UUID(as_uuid=True), sa.ForeignKey('distillation_runs.id', ondelete='CASCADE'), nullable=False),
        
        # Model info
        sa.Column('provider', sa.String(50), nullable=False),  # 'openai', 'anthropic', 'google'
        sa.Column('model', sa.String(100), nullable=False),  # 'gpt-4o', 'claude-3.5-sonnet'
        
        # Request/Response
        sa.Column('prompt_sent', sa.Text(), nullable=False),
        sa.Column('system_prompt_used', sa.Text(), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=False),
        
        # Metrics
        sa.Column('tokens_input', sa.Integer(), nullable=True),
        sa.Column('tokens_output', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        
        # For similarity search & dedup (commented out - add pgvector later)
        # sa.Column('embedding', Vector(1536), nullable=True),
        
        # Organization (can override from run)
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic_id', UUID(as_uuid=True), sa.ForeignKey('distillation_topics.id', ondelete='SET NULL'), nullable=True),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Response tags (many-to-many)
    op.create_table(
        'distillation_response_tags',
        sa.Column('response_id', UUID(as_uuid=True), sa.ForeignKey('distillation_responses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag_id', UUID(as_uuid=True), sa.ForeignKey('distillation_tags.id', ondelete='CASCADE'), nullable=False),
        sa.PrimaryKeyConstraint('response_id', 'tag_id'),
    )
    
    # ========================================
    # Banked Responses & Structuring
    # ========================================
    
    op.create_table(
        'distillation_banked',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('response_id', UUID(as_uuid=True), sa.ForeignKey('distillation_responses.id', ondelete='CASCADE'), nullable=False),
        
        # Can override organization from response
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic_id', UUID(as_uuid=True), sa.ForeignKey('distillation_topics.id', ondelete='SET NULL'), nullable=True),
        
        # Curation
        sa.Column('quality_score', sa.Float(), nullable=True),  # 0.0 - 1.0
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),  # 'draft', 'reviewed', 'approved', 'rejected'
        
        sa.Column('banked_by', sa.String(100), nullable=True),
        sa.Column('banked_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    
    op.create_table(
        'distillation_structured',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('banked_id', UUID(as_uuid=True), sa.ForeignKey('distillation_banked.id', ondelete='CASCADE'), nullable=False),
        
        # The extracted structure
        sa.Column('schema_name', sa.String(100), nullable=False),  # 'qa_pair', 'instruction', 'summary'
        sa.Column('structured_data', JSON, nullable=False),  # The actual structured content
        
        # Extraction metadata
        sa.Column('extraction_method', sa.String(50), nullable=True),  # 'manual', 'llm_assisted', 'rule_based'
        sa.Column('extracted_by', sa.String(100), nullable=True),
        sa.Column('extracted_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # ========================================
    # Comparisons & Voting
    # ========================================
    
    op.create_table(
        'distillation_comparisons',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', UUID(as_uuid=True), sa.ForeignKey('distillation_runs.id', ondelete='SET NULL'), nullable=True),
        
        # Comparison setup
        sa.Column('comparison_type', sa.String(20), nullable=False),  # 'side_by_side', 'blind', 'ab_preference'
        sa.Column('prompt_used', sa.Text(), nullable=False),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # 'pending', 'completed'
        
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_table(
        'distillation_comparison_responses',
        sa.Column('comparison_id', UUID(as_uuid=True), sa.ForeignKey('distillation_comparisons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('response_id', UUID(as_uuid=True), sa.ForeignKey('distillation_responses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('display_label', sa.String(10), nullable=True),  # 'A', 'B', 'C' for blind
        sa.PrimaryKeyConstraint('comparison_id', 'response_id'),
    )
    
    op.create_table(
        'distillation_votes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('comparison_id', UUID(as_uuid=True), sa.ForeignKey('distillation_comparisons.id', ondelete='CASCADE'), nullable=False),
        
        # The vote
        sa.Column('winner_response_id', UUID(as_uuid=True), sa.ForeignKey('distillation_responses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('vote_type', sa.String(20), nullable=False),  # 'winner', 'ranking', 'rating'
        sa.Column('rankings', JSON, nullable=True),  # [{response_id, rank}]
        sa.Column('ratings', JSON, nullable=True),  # [{response_id, score}]
        
        # Voter info
        sa.Column('voter', sa.String(100), nullable=True),
        sa.Column('voter_type', sa.String(20), nullable=False, server_default='user'),  # 'user', 'expert', 'automated'
        sa.Column('notes', sa.Text(), nullable=True),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # ========================================
    # Datasets
    # ========================================
    
    op.create_table(
        'distillation_datasets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Type
        sa.Column('dataset_type', sa.String(50), nullable=False),  # 'training', 'evaluation', 'benchmark'
        
        # Organization
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id', ondelete='SET NULL'), nullable=True),
        
        # Selection criteria
        sa.Column('selection_criteria', JSON, nullable=False, server_default='{}'),
        
        # Stats
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Export
        sa.Column('export_format', sa.String(20), nullable=True),  # 'jsonl', 'parquet', 'csv'
        sa.Column('export_path', sa.String(500), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),  # 'draft', 'building', 'ready', 'exported'
        
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.UniqueConstraint('name', 'version', name='uq_dataset_name_version'),
    )
    
    op.create_table(
        'distillation_dataset_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('distillation_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('banked_id', UUID(as_uuid=True), sa.ForeignKey('distillation_banked.id', ondelete='CASCADE'), nullable=True),
        sa.Column('structured_id', UUID(as_uuid=True), sa.ForeignKey('distillation_structured.id', ondelete='CASCADE'), nullable=True),
        
        # Split
        sa.Column('split', sa.String(20), nullable=False, server_default='train'),  # 'train', 'validation', 'test'
        
        # Order
        sa.Column('sequence_order', sa.Integer(), nullable=True),
        
        sa.Column('added_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # ========================================
    # Expert Review (Phase 6)
    # ========================================
    
    op.create_table(
        'distillation_review_queues',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Filtering criteria for auto-populating
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic_id', UUID(as_uuid=True), sa.ForeignKey('distillation_topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('min_quality_score', sa.Float(), nullable=True),
        
        # Assignment
        sa.Column('assigned_experts', ARRAY(sa.String()), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_table(
        'distillation_review_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('queue_id', UUID(as_uuid=True), sa.ForeignKey('distillation_review_queues.id', ondelete='CASCADE'), nullable=False),
        sa.Column('banked_id', UUID(as_uuid=True), sa.ForeignKey('distillation_banked.id', ondelete='CASCADE'), nullable=False),
        
        # Review status
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # 'pending', 'in_review', 'approved', 'rejected', 'needs_revision'
        sa.Column('assigned_to', sa.String(100), nullable=True),
        
        # Review outcome
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('review_score', sa.Float(), nullable=True),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        # Priority for ordering
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_table(
        'distillation_review_exports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('queue_id', UUID(as_uuid=True), sa.ForeignKey('distillation_review_queues.id', ondelete='CASCADE'), nullable=False),
        
        # Export details
        sa.Column('export_format', sa.String(20), nullable=False),  # 'csv', 'json', 'xlsx'
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Import tracking
        sa.Column('imported_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('items_updated', sa.Integer(), nullable=True),
        
        sa.Column('exported_by', sa.String(100), nullable=True),
        sa.Column('exported_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # ========================================
    # Indexes for performance
    # ========================================
    
    op.create_index('ix_distillation_runs_status', 'distillation_runs', ['status'])
    op.create_index('ix_distillation_runs_trigger', 'distillation_runs', ['trigger_type'])
    op.create_index('ix_distillation_runs_task', 'distillation_runs', ['task_id'])
    op.create_index('ix_distillation_responses_run', 'distillation_responses', ['run_id'])
    op.create_index('ix_distillation_responses_model', 'distillation_responses', ['provider', 'model'])
    op.create_index('ix_distillation_banked_status', 'distillation_banked', ['status'])
    op.create_index('ix_distillation_datasets_status', 'distillation_datasets', ['status'])
    op.create_index('ix_distillation_review_items_queue', 'distillation_review_items', ['queue_id'])
    op.create_index('ix_distillation_review_items_status', 'distillation_review_items', ['status'])
    op.create_index('ix_distillation_review_items_assigned', 'distillation_review_items', ['assigned_to'])


def downgrade():
    # Drop in reverse order
    op.drop_table('distillation_review_exports')
    op.drop_table('distillation_review_items')
    op.drop_table('distillation_review_queues')
    op.drop_table('distillation_dataset_items')
    op.drop_table('distillation_datasets')
    op.drop_table('distillation_votes')
    op.drop_table('distillation_comparison_responses')
    op.drop_table('distillation_comparisons')
    op.drop_table('distillation_structured')
    op.drop_table('distillation_banked')
    op.drop_table('distillation_response_tags')
    op.drop_table('distillation_responses')
    op.drop_table('distillation_runs')
    op.drop_table('distillation_tasks')
    op.drop_table('distillation_tags')
    op.drop_table('distillation_topics')
    op.drop_table('distillation_domains')
