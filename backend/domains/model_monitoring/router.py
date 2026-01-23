"""Model Monitoring API Router.

Provides endpoints for:
- Monitoring summary and health score
- Latency and error metrics recording/retrieval
- SLA configuration and compliance checking
- Alert management
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

from .service import get_monitoring_service
from .models import (
    LatencyMetricsResponse,
    ErrorMetricsResponse,
    HealthScoreResponse,
    SLAConfigRequest,
    SLAConfigResponse,
    SLAStatusResponse,
    MonitoringSummaryResponse,
    RecordLatencyRequest,
    RecordErrorsRequest,
    SLAAlertResponse,
    AcknowledgeAlertRequest,
)

router = APIRouter(prefix="/api/v1/model-monitoring", tags=["Model Monitoring"])


@router.get("/{model_id}/summary", response_model=MonitoringSummaryResponse)
async def get_monitoring_summary(model_id: str):
    """
    Get complete monitoring summary for a model.

    Returns health score, SLA status, recent metrics, and active alerts.
    """
    service = get_monitoring_service()
    try:
        summary = service.get_monitoring_summary(model_id)
        return MonitoringSummaryResponse(
            model_id=summary.model_id,
            model_name=summary.model_name,
            health_score=HealthScoreResponse(
                overall=summary.health_score.overall,
                latency_score=summary.health_score.latency_score,
                error_score=summary.health_score.error_score,
                latency_details=summary.health_score.latency_details,
                error_details=summary.health_score.error_details,
            ),
            sla_status=SLAStatusResponse(
                model_id=summary.sla_status.model_id,
                is_compliant=summary.sla_status.is_compliant,
                latency_compliant=summary.sla_status.latency_compliant,
                error_rate_compliant=summary.sla_status.error_rate_compliant,
                current_p95_ms=summary.sla_status.current_p95_ms,
                current_error_rate=summary.sla_status.current_error_rate,
                sla_config=SLAConfigResponse(
                    id=summary.sla_status.sla_config.id,
                    model_id=summary.sla_status.sla_config.model_id,
                    max_latency_p95_ms=summary.sla_status.sla_config.max_latency_p95_ms,
                    max_error_rate_percent=summary.sla_status.sla_config.max_error_rate_percent,
                    alerting_enabled=summary.sla_status.sla_config.alerting_enabled,
                ),
                message=summary.sla_status.message,
            ) if summary.sla_status else None,
            recent_latency=[
                LatencyMetricsResponse(
                    id=m.id,
                    model_id=m.model_id,
                    recorded_at=m.recorded_at,
                    p50_ms=m.p50_ms,
                    p95_ms=m.p95_ms,
                    p99_ms=m.p99_ms,
                    request_count=m.request_count,
                    window_minutes=m.window_minutes,
                )
                for m in summary.recent_latency
            ],
            recent_errors=[
                ErrorMetricsResponse(
                    id=m.id,
                    model_id=m.model_id,
                    recorded_at=m.recorded_at,
                    total_requests=m.total_requests,
                    error_count=m.error_count,
                    error_rate=m.error_rate,
                    error_types=m.error_types,
                    window_minutes=m.window_minutes,
                )
                for m in summary.recent_errors
            ],
            active_alerts=summary.active_alerts,
            total_requests_24h=summary.total_requests_24h,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/health-score", response_model=HealthScoreResponse)
async def get_health_score(model_id: str):
    """
    Get health score for a model.

    Health score is calculated from latency and error metrics compared to SLA thresholds.
    """
    service = get_monitoring_service()
    try:
        health = service.calculate_health_score(model_id)
        return HealthScoreResponse(
            overall=health.overall,
            latency_score=health.latency_score,
            error_score=health.error_score,
            latency_details=health.latency_details,
            error_details=health.error_details,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/latency", response_model=List[LatencyMetricsResponse])
async def get_latency_history(
    model_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history")
):
    """
    Get latency metrics history for a model.

    Returns P50, P95, P99 latency percentiles over time.
    """
    service = get_monitoring_service()
    try:
        history = service.get_latency_history(model_id, hours=hours)
        return [
            LatencyMetricsResponse(
                id=m.id,
                model_id=m.model_id,
                recorded_at=m.recorded_at,
                p50_ms=m.p50_ms,
                p95_ms=m.p95_ms,
                p99_ms=m.p99_ms,
                request_count=m.request_count,
                window_minutes=m.window_minutes,
            )
            for m in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/errors", response_model=List[ErrorMetricsResponse])
async def get_error_history(
    model_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history")
):
    """
    Get error rate history for a model.

    Returns error counts and rates over time with breakdown by error type.
    """
    service = get_monitoring_service()
    try:
        history = service.get_error_history(model_id, hours=hours)
        return [
            ErrorMetricsResponse(
                id=m.id,
                model_id=m.model_id,
                recorded_at=m.recorded_at,
                total_requests=m.total_requests,
                error_count=m.error_count,
                error_rate=m.error_rate,
                error_types=m.error_types,
                window_minutes=m.window_minutes,
            )
            for m in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/record/latency")
async def record_latency_metrics(model_id: str, request: RecordLatencyRequest):
    """
    Record latency metrics for a model.

    Accepts a list of latency values (in milliseconds) and calculates percentiles.
    """
    service = get_monitoring_service()
    try:
        record_id = service.record_latency_metrics(
            model_id=model_id,
            latencies_ms=request.latencies_ms,
            window_minutes=request.window_minutes,
        )
        return {"id": record_id, "message": "Latency metrics recorded"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/record/errors")
async def record_error_metrics(model_id: str, request: RecordErrorsRequest):
    """
    Record error rate metrics for a model.

    Records total requests and error count for a time window.
    """
    service = get_monitoring_service()
    try:
        record_id = service.record_error(
            model_id=model_id,
            total_requests=request.total_requests,
            error_count=request.error_count,
            error_types=request.error_types,
            window_minutes=request.window_minutes,
        )
        return {"id": record_id, "message": "Error metrics recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/sla", response_model=SLAConfigResponse)
async def get_sla_config(model_id: str):
    """
    Get SLA configuration for a model.

    Returns None if no SLA is configured.
    """
    service = get_monitoring_service()
    config = service.get_sla_config(model_id)
    if not config:
        raise HTTPException(status_code=404, detail="No SLA configuration found")
    return SLAConfigResponse(
        id=config.id,
        model_id=config.model_id,
        max_latency_p95_ms=config.max_latency_p95_ms,
        max_error_rate_percent=config.max_error_rate_percent,
        alerting_enabled=config.alerting_enabled,
    )


@router.post("/{model_id}/sla", response_model=SLAConfigResponse)
async def create_or_update_sla(model_id: str, request: SLAConfigRequest):
    """
    Create or update SLA configuration for a model.

    SLA defines thresholds for latency and error rate that trigger alerts.
    """
    service = get_monitoring_service()
    try:
        sla_id = service.create_or_update_sla(
            model_id=model_id,
            max_latency_p95_ms=request.max_latency_p95_ms,
            max_error_rate_percent=request.max_error_rate_percent,
            alerting_enabled=request.alerting_enabled,
        )
        config = service.get_sla_config(model_id)
        return SLAConfigResponse(
            id=config.id,
            model_id=config.model_id,
            max_latency_p95_ms=config.max_latency_p95_ms,
            max_error_rate_percent=config.max_error_rate_percent,
            alerting_enabled=config.alerting_enabled,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/sla/status", response_model=SLAStatusResponse)
async def get_sla_status(model_id: str):
    """
    Check SLA compliance status for a model.

    Returns current compliance status with details on any breaches.
    """
    service = get_monitoring_service()
    try:
        status = service.check_sla_compliance(model_id)
        return SLAStatusResponse(
            model_id=status.model_id,
            is_compliant=status.is_compliant,
            latency_compliant=status.latency_compliant,
            error_rate_compliant=status.error_rate_compliant,
            current_p95_ms=status.current_p95_ms,
            current_error_rate=status.current_error_rate,
            sla_config=SLAConfigResponse(
                id=status.sla_config.id,
                model_id=status.sla_config.model_id,
                max_latency_p95_ms=status.sla_config.max_latency_p95_ms,
                max_error_rate_percent=status.sla_config.max_error_rate_percent,
                alerting_enabled=status.sla_config.alerting_enabled,
            ),
            message=status.message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[SLAAlertResponse])
async def get_active_alerts(
    model_id: Optional[str] = Query(default=None, description="Filter by model ID")
):
    """
    Get active (unacknowledged, unresolved) SLA alerts.

    Optionally filter by model ID.
    """
    service = get_monitoring_service()
    try:
        alerts = service.get_active_alerts(model_id=model_id)
        return [
            SLAAlertResponse(
                id=str(a['id']),
                model_id=a['model_id'],
                model_name=a.get('model_name'),
                alert_type=a['alert_type'],
                threshold_value=float(a['threshold_value']),
                actual_value=float(a['actual_value']),
                triggered_at=a['triggered_at'],
                resolved_at=a.get('resolved_at'),
                acknowledged=a['acknowledged'],
                acknowledged_by=a.get('acknowledged_by'),
            )
            for a in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: AcknowledgeAlertRequest):
    """
    Acknowledge an SLA alert.

    Acknowledged alerts are still visible but marked as reviewed.
    """
    service = get_monitoring_service()
    success = service.acknowledge_alert(alert_id, request.acknowledged_by)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged"}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """
    Mark an alert as resolved.

    Resolved alerts are no longer shown in active alerts list.
    """
    service = get_monitoring_service()
    success = service.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved"}


# Production models overview endpoint
@router.get("/production-models")
async def get_production_models_monitoring():
    """
    Get monitoring overview for all production models.

    Returns summary data for quick dashboard view.
    """
    from sqlalchemy import create_engine, text
    from core.config import settings

    engine = create_engine(settings.database_url)
    service = get_monitoring_service()

    query = """
        SELECT id, name, model_family
        FROM ml_model
        WHERE status = 'production'
        ORDER BY name
    """

    with engine.connect() as conn:
        result = conn.execute(text(query))
        models = [dict(row._mapping) for row in result]

    summaries = []
    for model in models:
        try:
            health = service.calculate_health_score(model['id'])
            sla = service.check_sla_compliance(model['id'])
            summaries.append({
                'model_id': model['id'],
                'model_name': model['name'],
                'model_family': model['model_family'],
                'health_score': health.overall,
                'is_sla_compliant': sla.is_compliant,
                'current_p95_ms': sla.current_p95_ms,
                'current_error_rate': sla.current_error_rate,
            })
        except Exception:
            summaries.append({
                'model_id': model['id'],
                'model_name': model['name'],
                'model_family': model['model_family'],
                'health_score': None,
                'is_sla_compliant': None,
                'current_p95_ms': None,
                'current_error_rate': None,
            })

    return {'models': summaries}
