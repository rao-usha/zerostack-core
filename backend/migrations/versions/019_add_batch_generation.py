"""Add batch generation tables for prompt loop feature.

Revision ID: 019_add_batch_generation
Revises: 018_add_gdrive_support
Create Date: 2026-01-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = '019_add_batch_generation'
down_revision = '018_add_gdrive_support'
branch_labels = None
depends_on = None


def upgrade():
    # Generation Templates
    op.create_table(
        'generation_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('template_type', sa.String(50), nullable=False),  # 'qa_pair', 'reps_warrants', 'summary', 'classification', 'custom'
        sa.Column('system_prompt', sa.Text, nullable=True),
        sa.Column('user_template', sa.Text, nullable=False),
        sa.Column('output_schema', JSONB, server_default='{}'),
        sa.Column('parse_json', sa.Boolean, server_default='false'),
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id'), nullable=True),
        sa.Column('is_builtin', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    
    # Batch Jobs
    op.create_table(
        'batch_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('generation_templates.id'), nullable=True),
        sa.Column('target_models', ARRAY(sa.String), server_default='{}'),
        sa.Column('system_prompt', sa.Text, nullable=True),
        sa.Column('user_template', sa.Text, nullable=True),
        sa.Column('input_type', sa.String(20), nullable=False),  # 'text', 'csv', 'json'
        sa.Column('input_data', JSONB, server_default='[]'),
        sa.Column('parallelism', sa.Integer, server_default='3'),
        sa.Column('auto_bank', sa.Boolean, server_default='false'),
        sa.Column('auto_bank_threshold', sa.Float, nullable=True),
        sa.Column('domain_id', UUID(as_uuid=True), sa.ForeignKey('distillation_domains.id'), nullable=True),
        sa.Column('topic_id', UUID(as_uuid=True), sa.ForeignKey('distillation_topics.id'), nullable=True),
        sa.Column('status', sa.String(20), server_default="'pending'"),
        sa.Column('total_items', sa.Integer, server_default='0'),
        sa.Column('completed_items', sa.Integer, server_default='0'),
        sa.Column('failed_items', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_failed', sa.Boolean, server_default='true'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    
    # Batch Job Items
    op.create_table(
        'batch_job_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('batch_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence', sa.Integer, nullable=False),
        sa.Column('input_data', JSONB, server_default='{}'),
        sa.Column('rendered_prompt', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), server_default="'pending'"),
        sa.Column('target_model', sa.String(100), nullable=True),
        sa.Column('response_id', UUID(as_uuid=True), sa.ForeignKey('distillation_responses.id'), nullable=True),
        sa.Column('output_text', sa.Text, nullable=True),
        sa.Column('output_parsed', JSONB, nullable=True),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('was_banked', sa.Boolean, server_default='false'),
        sa.Column('banked_id', UUID(as_uuid=True), sa.ForeignKey('distillation_banked.id'), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    
    # Indexes for performance
    op.create_index('idx_batch_jobs_status', 'batch_jobs', ['status'])
    op.create_index('idx_batch_jobs_created_at', 'batch_jobs', ['created_at'])
    op.create_index('idx_batch_job_items_job_id', 'batch_job_items', ['job_id'])
    op.create_index('idx_batch_job_items_status', 'batch_job_items', ['status'])
    op.create_index('idx_generation_templates_type', 'generation_templates', ['template_type'])
    
    # Insert built-in templates
    op.execute("""
        INSERT INTO generation_templates (name, description, template_type, system_prompt, user_template, output_schema, parse_json, is_builtin) VALUES
        (
            'QA Pair Generator',
            'Generate question-answer pairs from input text or topic',
            'qa_pair',
            'You are an expert at creating high-quality question-answer pairs for training data. Generate clear, specific questions and comprehensive answers.',
            'Generate a question-answer pair based on the following input:\n\n{input}\n\nRespond in JSON format:\n{"question": "...", "answer": "..."}',
            '{"question": {"type": "string", "required": true}, "answer": {"type": "string", "required": true}}',
            true,
            true
        ),
        (
            'Reps & Warrants Extractor',
            'Extract representations and warranties from legal or business text',
            'reps_warrants',
            'You are a legal expert specializing in contract analysis. Extract representations and warranties from the provided text, categorizing them appropriately.',
            'Extract all representations and warranties from the following text:\n\n{input}\n\nRespond in JSON format:\n{"representations": [{"statement": "...", "party": "...", "category": "..."}], "warranties": [{"statement": "...", "party": "...", "duration": "...", "category": "..."}]}',
            '{"representations": {"type": "array"}, "warranties": {"type": "array"}}',
            true,
            true
        ),
        (
            'Summary Generator',
            'Generate concise summaries of input text',
            'summary',
            'You are an expert summarizer. Create clear, concise summaries that capture the key points.',
            'Summarize the following text:\n\n{input}\n\nProvide a concise summary in 2-3 paragraphs.',
            '{}',
            false,
            true
        ),
        (
            'Text Classifier',
            'Classify text into predefined categories',
            'classification',
            'You are a text classification expert. Analyze the input and classify it accurately.',
            'Classify the following text:\n\n{input}\n\nRespond in JSON format:\n{"category": "...", "confidence": 0.0-1.0, "reasoning": "..."}',
            '{"category": {"type": "string", "required": true}, "confidence": {"type": "number"}, "reasoning": {"type": "string"}}',
            true,
            true
        ),
        (
            'Instruction-Response Generator',
            'Generate instruction-following training data',
            'custom',
            'You are an AI assistant helping create training data. Generate helpful, detailed responses to instructions.',
            'Given the following instruction, provide a helpful and detailed response:\n\nInstruction: {input}\n\nResponse:',
            '{}',
            false,
            true
        )
    """)


def downgrade():
    op.drop_index('idx_generation_templates_type')
    op.drop_index('idx_batch_job_items_status')
    op.drop_index('idx_batch_job_items_job_id')
    op.drop_index('idx_batch_jobs_created_at')
    op.drop_index('idx_batch_jobs_status')
    op.drop_table('batch_job_items')
    op.drop_table('batch_jobs')
    op.drop_table('generation_templates')
