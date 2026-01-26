"""Database models for insights domain."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String, Text


class InsightReport(SQLModel, table=True):
    """Stored insight report with analytics data."""
    __tablename__ = "insight_reports"

    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    dataset_id: UUID = SQLField(index=True)

    # Report metadata
    title: str = SQLField(max_length=255)
    context: Optional[str] = SQLField(default=None, max_length=500)

    # Performance & executive metrics (JSONB for complex nested data)
    performance_score: Dict[str, Any] = SQLField(default=None, sa_column=Column(JSONB))
    executive_kpis: List[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))

    # Trend and growth data
    trend_data: List[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    growth_metrics: Dict[str, Any] = SQLField(default=None, sa_column=Column(JSONB))

    # Risk and distribution
    risk_indicators: List[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    distribution_data: Dict[str, List[Dict[str, Any]]] = SQLField(default=None, sa_column=Column(JSONB))

    # Recommendations
    recommendations: List[str] = SQLField(default=None, sa_column=Column(ARRAY(String)))

    # Summary text
    summary: str = SQLField(default="", sa_column=Column(Text))

    # Detailed analytics
    trends: List[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    anomalies: List[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    correlations: List[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    key_metrics: Dict[str, Any] = SQLField(default=None, sa_column=Column(JSONB))

    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
