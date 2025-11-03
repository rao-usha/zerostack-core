"""Insights models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class InsightType(str):
    """Insight types."""
    SUMMARY = "summary"
    TREND = "trend"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    PREDICTION = "prediction"


class Insight(BaseModel):
    """Insight definition."""
    id: UUID
    name: str
    description: Optional[str] = None
    insight_type: str
    dataset_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    data: Dict[str, Any] = Field(default_factory=dict)  # Insight data/visualizations
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class InsightCreate(BaseModel):
    """Request to create an insight."""
    name: str
    description: Optional[str] = None
    insight_type: str
    dataset_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class InsightReport(BaseModel):
    """Insight report."""
    id: UUID
    title: str
    insights: List[Insight] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

