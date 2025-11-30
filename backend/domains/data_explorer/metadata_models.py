"""
Enhanced metadata models for tracking database connections and analysis relationships.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String, Text


class DatabaseConnectionMetadata(SQLModel, table=True):
    """Metadata about external database connections used for analysis."""
    __tablename__ = "database_connection_metadata"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    connection_id: str = SQLField(max_length=100, unique=True, index=True)  # e.g., "default", "db2"
    
    # Connection details
    host: str = SQLField(max_length=255)
    port: int
    database_name: str = SQLField(max_length=255)
    
    # Descriptive info
    name: str = SQLField(max_length=255)
    description: Optional[str] = None
    
    # Schema tracking
    schemas: List[str] = SQLField(default=[], sa_column=Column(ARRAY(String)))
    table_count: Optional[int] = None
    
    # Stats
    first_connected_at: datetime = SQLField(default_factory=datetime.utcnow)
    last_connected_at: datetime = SQLField(default_factory=datetime.utcnow)
    total_analyses: int = SQLField(default=0)
    
    # Additional metadata
    metadata: Dict[str, Any] = SQLField(default=None, sa_column=Column(JSONB))


class TableAnalysisLink(SQLModel, table=True):
    """Link table between analyses and the tables they analyzed."""
    __tablename__ = "table_analysis_links"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    analysis_id: UUID = SQLField(foreign_key="ai_analysis_results.id", index=True)
    
    # Table identity
    database_id: str = SQLField(max_length=100, index=True)
    schema_name: str = SQLField(max_length=255, index=True)
    table_name: str = SQLField(max_length=255, index=True)
    
    # Analysis context
    row_count_at_analysis: Optional[int] = None
    column_count: Optional[int] = None
    
    # Findings for this specific table
    findings: Dict[str, Any] = SQLField(default=None, sa_column=Column(JSONB))
    quality_score: Optional[float] = None
    anomaly_count: Optional[int] = None
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    
    # Composite index for efficient lookups
    __table_args__ = (
        # Index for finding all analyses for a specific table
        {"schema": "public"},
    )

