"""Database models for AI analysis results, prompt recipes, and data dictionary."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, JSON
from sqlalchemy import String, Text


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


class PromptRecipe(SQLModel, table=True):
    """Editable prompt recipes for different analysis types."""
    __tablename__ = "prompt_recipes"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    
    # Recipe identity
    name: str = SQLField(index=True, max_length=255)  # e.g. "Data Profiling - Default v1"
    action_type: str = SQLField(index=True, max_length=100)  # "profiling", "quality", "anomaly", etc.
    
    # Optional defaults; can be null if the recipe is model-agnostic
    default_provider: Optional[str] = SQLField(default=None, index=True, max_length=50)
    default_model: Optional[str] = SQLField(default=None, max_length=100)
    
    # The actual prompt pieces
    system_message: str = SQLField(sa_column=Column(Text, nullable=False))
    user_template: str = SQLField(sa_column=Column(Text, nullable=False))  # contains {{schema_summary}}, {{sample_rows}}
    
    # JSON metadata for tags, version info, etc.
    recipe_metadata: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB, nullable=True))
    
    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DataDictionaryEntry(SQLModel, table=True):
    """Data dictionary entry for column-level documentation."""
    __tablename__ = "data_dictionary_entries"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    
    # Table/column identity
    database_name: str = SQLField(max_length=255, index=True)
    schema_name: str = SQLField(max_length=255, index=True)
    table_name: str = SQLField(max_length=255, index=True)
    column_name: str = SQLField(max_length=255, index=True)
    
    # Business documentation
    business_name: Optional[str] = SQLField(default=None, max_length=255)
    business_description: Optional[str] = None
    technical_description: Optional[str] = None
    
    # Technical details
    data_type: Optional[str] = SQLField(default=None, max_length=100)
    examples: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSON))
    tags: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSON))
    
    # Metadata
    source: str = SQLField(default="llm_initial", max_length=50)  # "llm_initial", "human_edited", etc.
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)

