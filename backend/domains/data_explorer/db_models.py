"""Database models for AI analysis results."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String


class AIAnalysisResult(SQLModel, table=True):
    """Stored AI analysis result."""
    __tablename__ = "ai_analysis_results"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(max_length=255)
    description: Optional[str] = None
    
    # Analysis configuration
    tables: List[Dict[str, str]] = SQLField(default=None, sa_column=Column(JSONB))  # [{"schema": "public", "table": "users"}]
    analysis_types: List[str] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    provider: str = SQLField(max_length=50)
    model: str = SQLField(max_length=100)
    context: Optional[str] = None
    
    # Analysis results
    insights: Dict[str, Any] = SQLField(default=None, sa_column=Column(JSONB))
    summary: str = SQLField(default="")
    recommendations: List[str] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    
    # Metadata
    execution_metadata: Dict[str, Any] = SQLField(default=None, sa_column=Column(JSONB))
    tags: List[str] = SQLField(default=[], sa_column=Column(ARRAY(String)))
    
    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    
    # Database connection used
    db_id: str = SQLField(default="default", max_length=100)

