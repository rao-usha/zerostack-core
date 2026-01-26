"""Insights Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


# Request models
class InsightGenerateRequest(BaseModel):
    """Request to generate insights for a dataset."""
    dataset_id: UUID
    context: str = Field(default="general business", description="Context for generating insights")
    title: Optional[str] = Field(default=None, description="Custom title for the report")
    persist: bool = Field(default=True, description="Whether to persist the insight report to database")


# Response models
class InsightReportResponse(BaseModel):
    """Full insight report response."""
    id: UUID
    dataset_id: UUID
    title: str
    context: Optional[str] = None

    # Performance & executive metrics
    performance_score: Dict[str, Any] = Field(default_factory=dict)
    executive_kpis: List[Dict[str, Any]] = Field(default_factory=list)

    # Trend and growth data
    trend_data: List[Dict[str, Any]] = Field(default_factory=list)
    growth_metrics: Dict[str, Any] = Field(default_factory=dict)

    # Risk and distribution
    risk_indicators: List[Dict[str, Any]] = Field(default_factory=list)
    distribution_data: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    # Summary
    summary: str = ""

    # Detailed analytics
    trends: List[Dict[str, Any]] = Field(default_factory=list)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    correlations: List[Dict[str, Any]] = Field(default_factory=list)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InsightListItem(BaseModel):
    """Summary item for listing insights."""
    id: UUID
    dataset_id: UUID
    title: str
    context: Optional[str] = None
    summary: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    """Paginated list of insight reports."""
    items: List[InsightListItem]
    total: int
    page: int = 1
    page_size: int = 20


# Legacy models (kept for backward compatibility)
class InsightType(str):
    """Insight types."""
    SUMMARY = "summary"
    TREND = "trend"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    PREDICTION = "prediction"


class Insight(BaseModel):
    """Insight definition (legacy)."""
    id: UUID
    name: str
    description: Optional[str] = None
    insight_type: str
    dataset_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class InsightCreate(BaseModel):
    """Request to create an insight (legacy)."""
    name: str
    description: Optional[str] = None
    insight_type: str
    dataset_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class InsightReport(BaseModel):
    """Insight report (legacy)."""
    id: UUID
    title: str
    insights: List[Insight] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
