"""Add chat tables for persistent chat experience

Revision ID: 002
Revises: 001
Create Date: 2024-11-29

Tables:
- chat_conversations: Stores chat sessions with metadata
- chat_messages: Stores individual messages and tool calls
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chat_conversations table
    op.create_table(
        'chat_conversations',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.Text, nullable=True, comment='Auto-generated from first message if not provided'),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('provider', sa.Text, nullable=False, comment='LLM provider: openai, anthropic, google, xai'),
        sa.Column('model', sa.Text, nullable=False, comment='Model name: gpt-4-turbo, claude-3.5-sonnet, etc.'),
        sa.Column('connection_id', sa.Text, nullable=True, comment='DB connection ID from Data Explorer'),
        sa.Column('metadata', JSONB, nullable=True, comment='Additional metadata: tags, user_id, etc.'),
    )
    
    # Create indexes on chat_conversations
    op.create_index('ix_chat_conversations_updated_at', 'chat_conversations', ['updated_at'], postgresql_using='btree')
    op.create_index('ix_chat_conversations_provider', 'chat_conversations', ['provider'])
    op.create_index('ix_chat_conversations_created_at', 'chat_conversations', ['created_at'], postgresql_using='btree')
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', UUID, sa.ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Text, nullable=False, comment='Message role: system, user, assistant, tool'),
        sa.Column('content', sa.Text, nullable=True, comment='Message text content'),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('sequence', sa.BigInteger, nullable=False, comment='Monotonically increasing per conversation'),
        sa.Column('provider', sa.Text, nullable=True, comment='Provider used for this message'),
        sa.Column('model', sa.Text, nullable=True, comment='Model used for this message'),
        sa.Column('tool_name', sa.Text, nullable=True, comment='Tool name if role=tool'),
        sa.Column('tool_input', JSONB, nullable=True, comment='Tool input parameters'),
        sa.Column('tool_output', JSONB, nullable=True, comment='Tool output result'),
        sa.Column('raw_request', JSONB, nullable=True, comment='Raw provider request payload'),
        sa.Column('raw_response', JSONB, nullable=True, comment='Raw provider response payload'),
    )
    
    # Create indexes on chat_messages
    op.create_index('ix_chat_messages_conversation_id', 'chat_messages', ['conversation_id'])
    op.create_index('ix_chat_messages_conversation_sequence', 'chat_messages', ['conversation_id', 'sequence'], postgresql_using='btree')
    op.create_index('ix_chat_messages_role', 'chat_messages', ['role'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'], postgresql_using='btree')
    
    # Create trigger to update updated_at on chat_conversations
    op.execute("""
        CREATE OR REPLACE FUNCTION update_chat_conversation_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE chat_conversations
            SET updated_at = NOW()
            WHERE id = NEW.conversation_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER chat_messages_update_conversation_updated_at
        AFTER INSERT ON chat_messages
        FOR EACH ROW
        EXECUTE FUNCTION update_chat_conversation_updated_at();
    """)


def downgrade() -> None:
    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS chat_messages_update_conversation_updated_at ON chat_messages')
    op.execute('DROP FUNCTION IF EXISTS update_chat_conversation_updated_at()')
    
    # Drop indexes
    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_messages_role', table_name='chat_messages')
    op.drop_index('ix_chat_messages_conversation_sequence', table_name='chat_messages')
    op.drop_index('ix_chat_messages_conversation_id', table_name='chat_messages')
    
    op.drop_index('ix_chat_conversations_created_at', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_provider', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_updated_at', table_name='chat_conversations')
    
    # Drop tables
    op.drop_table('chat_messages')
    op.drop_table('chat_conversations')

