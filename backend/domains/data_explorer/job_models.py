"""Job queue models for async analysis."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String


class AnalysisJob(SQLModel, table=True):
    """Analysis job for async processing."""
    __tablename__ = "analysis_jobs"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = None
    name: str = SQLField(max_length=255)
    description: Optional[str] = None
    
    # Configuration
    tables: List[Dict[str, str]] = SQLField(default=None, sa_column=Column(JSONB))
    analysis_types: List[str] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    provider: str = SQLField(max_length=50)
    model: str = SQLField(max_length=100)
    context: Optional[str] = None
    db_id: str = SQLField(default="default", max_length=100)
    
    # Prompt recipe (optional - if specified, prompts are rendered from recipe)
    prompt_recipe_id: Optional[int] = None
    prompt_overrides: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Status
    status: str = SQLField(default="pending", max_length=50)
    progress: int = SQLField(default=0)
    current_stage: Optional[str] = SQLField(default=None, max_length=255)
    
    # Results
    result_id: Optional[UUID] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Timing
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Metadata
    job_metadata: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    tags: List[str] = SQLField(default=[], sa_column=Column(ARRAY(String)))

