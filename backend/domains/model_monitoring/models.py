"""Pydantic models for Model Monitoring API."""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class LatencyMetricsResponse(BaseModel):
    """Response for latency metrics."""
    id: str
    model_id: str
    recorded_at: datetime
    p50_ms: float
    p95_ms: float
    p99_ms: float
    request_count: int
    window_minutes: int


class ErrorMetricsResponse(BaseModel):
    """Response for error rate metrics."""
    id: str
    model_id: str
    recorded_at: datetime
    total_requests: int
    error_count: int
    error_rate: float
    error_types: Dict[str, int] = Field(default_factory=dict)
    window_minutes: int


class HealthScoreResponse(BaseModel):
    """Response for health score."""
    overall: int = Field(ge=0, le=100, description="Overall health score 0-100")
    latency_score: int = Field(ge=0, le=100)
    error_score: int = Field(ge=0, le=100)
    latency_details: str
    error_details: str


class SLAConfigResponse(BaseModel):
    """Response for SLA configuration."""
    id: str
    model_id: str
    max_latency_p95_ms: int
    max_error_rate_percent: float
    alerting_enabled: bool


class SLAConfigRequest(BaseModel):
    """Request to create/update SLA configuration."""
    max_latency_p95_ms: int = Field(default=500, ge=1, description="Max P95 latency in milliseconds")
    max_error_rate_percent: float = Field(default=1.0, ge=0, le=100, description="Max error rate percentage")
    alerting_enabled: bool = Field(default=True)


class SLAStatusResponse(BaseModel):
    """Response for SLA compliance status."""
    model_id: str
    is_compliant: bool
    latency_compliant: bool
    error_rate_compliant: bool
    current_p95_ms: Optional[float] = None
    current_error_rate: Optional[float] = None
    sla_config: SLAConfigResponse
    message: str


class MonitoringSummaryResponse(BaseModel):
    """Response for complete monitoring summary."""
    model_id: str
    model_name: str
    health_score: HealthScoreResponse
    sla_status: Optional[SLAStatusResponse] = None
    recent_latency: List[LatencyMetricsResponse] = Field(default_factory=list)
    recent_errors: List[ErrorMetricsResponse] = Field(default_factory=list)
    active_alerts: int
    total_requests_24h: int


class RecordLatencyRequest(BaseModel):
    """Request to record latency metrics."""
    latencies_ms: List[float] = Field(..., min_length=1, description="List of latency values in ms")
    window_minutes: int = Field(default=5, ge=1)


class RecordErrorsRequest(BaseModel):
    """Request to record error metrics."""
    total_requests: int = Field(..., ge=0)
    error_count: int = Field(..., ge=0)
    error_types: Optional[Dict[str, int]] = Field(default=None)
    window_minutes: int = Field(default=5, ge=1)


class SLAAlertResponse(BaseModel):
    """Response for SLA alert."""
    id: str
    model_id: str
    model_name: Optional[str] = None
    alert_type: str
    threshold_value: float
    actual_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool
    acknowledged_by: Optional[str] = None


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""
    acknowledged_by: str
