"""Chat domain models."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, Column, JSON, Relationship
from sqlalchemy.dialects.postgresql import JSONB


# Database Models
class ChatConversation(SQLModel, table=True):
    """Chat conversation with metadata."""
    __tablename__ = "chat_conversations"
    
    model_config = {"protected_namespaces": ()}
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    title: Optional[str] = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    provider: str  # openai, anthropic, google, xai
    model: str  # gpt-4-turbo, claude-3.5-sonnet, etc.
    connection_id: Optional[str] = None  # DB connection ID
    # Use 'meta' instead of 'metadata' to avoid SQLAlchemy reserved name
    meta: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column("metadata", JSONB))
    
    # Relationships
    messages: List["ChatMessage"] = Relationship(back_populates="conversation")


class ChatMessage(SQLModel, table=True):
    """Individual chat message or tool call."""
    __tablename__ = "chat_messages"
    
    model_config = {"protected_namespaces": ()}
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = SQLField(foreign_key="chat_conversations.id")
    role: str  # system, user, assistant, tool
    content: Optional[str] = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    sequence: int  # Monotonically increasing per conversation
    provider: Optional[str] = None
    model: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    tool_output: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    raw_request: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    raw_response: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Relationships
    conversation: Optional[ChatConversation] = Relationship(back_populates="messages")


# API Request/Response Models
class ConversationCreate(BaseModel):
    """Request to create a new conversation."""
    title: Optional[str] = None
    provider: str = Field(..., description="LLM provider: openai, anthropic, google, xai")
    model: str = Field(..., description="Model name")
    connection_id: Optional[str] = Field(default="default", description="DB connection ID")
    meta: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """Request to update a conversation."""
    title: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response for a conversation."""
    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    provider: str
    model: str
    connection_id: Optional[str]
    meta: Optional[Dict[str, Any]]
    message_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Request to send a message in a conversation."""
    content: str = Field(..., min_length=1, max_length=50000)
    provider: Optional[str] = None  # Override conversation provider
    model: Optional[str] = None  # Override conversation model
    connection_id: Optional[str] = None  # Override connection
    stream: bool = Field(default=True, description="Stream response")


class MessageResponse(BaseModel):
    """Response for a message."""
    id: UUID
    conversation_id: UUID
    role: str
    content: Optional[str]
    created_at: datetime
    sequence: int
    provider: Optional[str]
    model: Optional[str]
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_output: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with full message history."""
    messages: List[MessageResponse]


class StreamEvent(BaseModel):
    """Server-sent event for streaming."""
    event: str  # delta, tool_call, tool_result, done, error
    data: Dict[str, Any]


class ChatCompletionRequest(BaseModel):
    """Internal request for LLM completion."""
    messages: List[Dict[str, Any]]
    provider: str
    model: str
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    stream: bool = True
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

