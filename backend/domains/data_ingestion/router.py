"""
Data Ingestion Router

FastAPI endpoints for file upload, PE deals, and issue management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlmodel import Session

from db_session import get_session
from domains.data_ingestion.models import (
    FileAnalysisResponse,
    UploadError,
    UploadResponse,
    DealCreate,
    DealUpdate,
    DealResponse,
    DealSummary,
    IngestedFileResponse,
    IngestedFileDetail,
    IssueResponse,
    IssueAcknowledge,
    IssueSummary,
    ReAnalyzeRequest,
    ReAnalyzeResponse,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
    GrowthMetricsResponse,
    ReconciliationRequest,
    ReconciliationSummaryResponse,
    AIInsightsRequest,
    AIAnalysisReportResponse,
)
from domains.data_ingestion.service import DataIngestionService
from domains.data_ingestion.persistence_service import IngestionPersistenceService


router = APIRouter(prefix="/api/v1/ingest", tags=["data-ingestion"])

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {'.csv', '.tsv', '.xlsx', '.xls'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_persistence_service(session: Session = Depends(get_session)) -> IngestionPersistenceService:
    """Get persistence service with database session"""
    return IngestionPersistenceService(session)


# --- Upload Endpoints ---

@router.post(
    "/upload",
    response_model=FileAnalysisResponse,
    responses={
        400: {"model": UploadError, "description": "Invalid file"},
        413: {"model": UploadError, "description": "File too large"},
    },
)
async def upload_and_analyze(
    file: UploadFile = File(..., description="CSV or Excel file to analyze"),
):
    """
    Upload a CSV or Excel file for automatic schema detection and analysis.

    This endpoint analyzes the file without persisting it to the database.
    Use POST /upload/persist to save the file and analysis results.

    Returns:
    - Inferred column types (string, integer, currency, date, email, etc.)
    - Data quality assessment
    - Sample data preview
    - PE due diligence insights (detected data categories, potential issues)
    """
    content, filename, file_type = await _validate_and_read_file(file)

    try:
        service = DataIngestionService()
        result = service.analyze_file(
            file_content=content,
            filename=filename,
            file_type=file_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing file: {str(e)}",
        )


@router.post(
    "/upload/persist",
    response_model=UploadResponse,
    responses={
        400: {"model": UploadError, "description": "Invalid file"},
        413: {"model": UploadError, "description": "File too large"},
    },
)
async def upload_and_persist(
    file: UploadFile = File(..., description="CSV or Excel file to upload"),
    deal_id: Optional[str] = Form(None, description="PE deal ID to associate with"),
    uploaded_by: Optional[str] = Form(None, description="User who uploaded the file"),
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """
    Upload a CSV or Excel file, analyze it, and persist to the database.

    The file analysis results and any detected issues are saved for later review.
    Duplicate files (same content hash) are detected and return the existing record.
    """
    content, filename, file_type = await _validate_and_read_file(file)

    try:
        result = service.upload_and_persist(
            file_content=content,
            filename=filename,
            file_type=file_type,
            deal_id=UUID(deal_id) if deal_id else None,
            uploaded_by=uploaded_by,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}",
        )


async def _validate_and_read_file(file: UploadFile) -> tuple[bytes, str, str]:
    """Validate and read uploaded file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    ext = '.' + file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading file: {str(e)}",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    return content, file.filename, file.content_type or ext


# --- Deal Endpoints ---

@router.post("/deals", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    data: DealCreate,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Create a new PE deal to group uploaded files"""
    return service.create_deal(data)


@router.get("/deals", response_model=List[DealResponse])
async def list_deals(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """List all PE deals"""
    return service.list_deals(status=status, limit=limit, offset=offset)


@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: str,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Get a specific deal"""
    result = service.get_deal(UUID(deal_id))
    if not result:
        raise HTTPException(status_code=404, detail="Deal not found")
    return result


@router.patch("/deals/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: str,
    data: DealUpdate,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Update a deal"""
    result = service.update_deal(UUID(deal_id), data)
    if not result:
        raise HTTPException(status_code=404, detail="Deal not found")
    return result


@router.get("/deals/{deal_id}/summary", response_model=DealSummary)
async def get_deal_summary(
    deal_id: str,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Get deal summary with aggregated statistics"""
    result = service.get_deal_summary(UUID(deal_id))
    if not result:
        raise HTTPException(status_code=404, detail="Deal not found")
    return result


@router.get("/deals/{deal_id}/files", response_model=List[IngestedFileResponse])
async def get_deal_files(
    deal_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Get all files for a deal"""
    return service.list_files(deal_id=UUID(deal_id), limit=limit, offset=offset)


# --- File Endpoints ---

@router.get("/files", response_model=List[IngestedFileResponse])
async def list_files(
    deal_id: Optional[str] = Query(None, description="Filter by deal ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    upload_source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """List all ingested files"""
    return service.list_files(
        deal_id=UUID(deal_id) if deal_id else None,
        status=status,
        upload_source=upload_source,
        limit=limit,
        offset=offset,
    )


@router.get("/files/{file_id}", response_model=IngestedFileDetail)
async def get_file(
    file_id: str,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Get detailed file information including analysis and issues"""
    result = service.get_file(UUID(file_id))
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Delete an ingested file and its associated issues"""
    if not service.delete_file(UUID(file_id)):
        raise HTTPException(status_code=404, detail="File not found")


@router.post("/files/{file_id}/analyze", response_model=ReAnalyzeResponse)
async def reanalyze_file(
    file_id: str,
    request: ReAnalyzeRequest = ReAnalyzeRequest(),
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """
    Re-run anomaly detection and red flag scanning on an existing file.

    This endpoint runs the PE analysis engine on a previously uploaded file,
    detecting statistical anomalies and PE-specific red flags.
    """
    result = service.reanalyze_file(
        file_id=UUID(file_id),
        run_anomaly_detection=request.run_anomaly_detection,
        run_red_flag_scan=request.run_red_flag_scan,
    )
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return result


# --- Issue Endpoints ---

@router.get("/issues", response_model=List[IssueResponse])
async def list_issues(
    file_id: Optional[str] = Query(None, description="Filter by file ID"),
    deal_id: Optional[str] = Query(None, description="Filter by deal ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    issue_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """List all issues with optional filters"""
    return service.list_issues(
        file_id=UUID(file_id) if file_id else None,
        deal_id=UUID(deal_id) if deal_id else None,
        severity=severity,
        issue_type=issue_type,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/issues/summary", response_model=IssueSummary)
async def get_issues_summary(
    file_id: Optional[str] = Query(None, description="Filter by file ID"),
    deal_id: Optional[str] = Query(None, description="Filter by deal ID"),
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Get summary of issues by severity and type"""
    return service.get_issue_summary(
        file_id=UUID(file_id) if file_id else None,
        deal_id=UUID(deal_id) if deal_id else None,
    )


@router.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: str,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Get a specific issue"""
    result = service.get_issue(UUID(issue_id))
    if not result:
        raise HTTPException(status_code=404, detail="Issue not found")
    return result


@router.post("/issues/{issue_id}/acknowledge", response_model=IssueResponse)
async def acknowledge_issue(
    issue_id: str,
    data: IssueAcknowledge,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """Acknowledge an issue"""
    result = service.acknowledge_issue(
        issue_id=UUID(issue_id),
        acknowledged_by=data.acknowledged_by,
        resolution_notes=data.resolution_notes,
        new_status=data.new_status,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Issue not found")
    return result


# --- Analysis Endpoints ---

@router.post("/analysis/trends", response_model=TrendAnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """
    Run trend analysis on a specific column in an uploaded file.

    Analyzes growth rates (MoM, QoQ, YoY), seasonality, and generates insights.
    """
    from domains.data_ingestion.trend_analyzer import TrendAnalyzer
    import pandas as pd

    # Get file data
    file_detail = service.get_file(UUID(request.file_id))
    if not file_detail:
        raise HTTPException(status_code=404, detail="File not found")

    if not file_detail.schema_analysis or 'sheets' not in file_detail.schema_analysis:
        raise HTTPException(status_code=400, detail="File has no analysis data")

    # Try to reconstruct DataFrame from sample data
    # In production, would load from stored file
    sheets = file_detail.schema_analysis.get('sheets', [])
    if not sheets:
        raise HTTPException(status_code=400, detail="No sheets found in analysis")

    # Use first sheet
    sheet = sheets[0]
    columns = [c['name'] for c in sheet.get('columns', [])]
    sample_data = sheet.get('sample_data', [])

    if not sample_data:
        raise HTTPException(status_code=400, detail="No sample data available")

    df = pd.DataFrame(sample_data, columns=columns)

    if request.date_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Date column '{request.date_column}' not found")
    if request.value_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Value column '{request.value_column}' not found")

    analyzer = TrendAnalyzer()
    result = analyzer.analyze_time_series(
        df, request.date_column, request.value_column, request.metric_type
    )

    if not result:
        raise HTTPException(status_code=400, detail="Insufficient data for trend analysis")

    return TrendAnalysisResponse(
        column_name=result.column_name,
        metric_type=result.metric_type,
        growth_metrics=GrowthMetricsResponse(
            period_over_period=result.growth_metrics.period_over_period,
            mom_avg=result.growth_metrics.mom_avg,
            qoq_avg=result.growth_metrics.qoq_avg,
            yoy_avg=result.growth_metrics.yoy_avg,
            cagr=result.growth_metrics.cagr,
            trend_direction=result.growth_metrics.trend_direction.value,
            acceleration=result.growth_metrics.acceleration,
        ),
        seasonality=result.seasonality.value,
        seasonality_strength=result.seasonality_strength,
        trend_line_slope=result.trend_line_slope,
        trend_line_r_squared=result.trend_line_r_squared,
        forecast_next_period=result.forecast_next_period,
        anomaly_periods=result.anomaly_periods,
        insights=result.insights,
    )


@router.post("/analysis/reconcile", response_model=ReconciliationSummaryResponse)
async def reconcile_files(
    request: ReconciliationRequest,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """
    Reconcile data between two uploaded files.

    Compares matching columns and identifies discrepancies.
    """
    from domains.data_ingestion.reconciliation_service import ReconciliationService
    import pandas as pd

    # Get both files
    file_a = service.get_file(UUID(request.file_id_a))
    file_b = service.get_file(UUID(request.file_id_b))

    if not file_a:
        raise HTTPException(status_code=404, detail=f"File A not found: {request.file_id_a}")
    if not file_b:
        raise HTTPException(status_code=404, detail=f"File B not found: {request.file_id_b}")

    # Extract DataFrames from sample data
    def extract_df(file_detail):
        if not file_detail.schema_analysis or 'sheets' not in file_detail.schema_analysis:
            return None
        sheets = file_detail.schema_analysis.get('sheets', [])
        if not sheets:
            return None
        sheet = sheets[0]
        columns = [c['name'] for c in sheet.get('columns', [])]
        sample_data = sheet.get('sample_data', [])
        if not sample_data:
            return None
        return pd.DataFrame(sample_data, columns=columns)

    df_a = extract_df(file_a)
    df_b = extract_df(file_b)

    if df_a is None or df_b is None:
        raise HTTPException(status_code=400, detail="Unable to extract data from files")

    reconciler = ReconciliationService()

    if request.column_a and request.column_b:
        # Specific column reconciliation
        result = reconciler.reconcile_specific(
            df_a, df_b,
            request.column_a, request.column_b,
            request.join_column_a, request.join_column_b,
            file_a.filename, file_b.filename,
            request.tolerance,
        )
        summary = reconciler._create_summary([result])
    else:
        # Auto-detect reconciliation
        summary = reconciler.reconcile_dataframes(
            df_a, df_b,
            file_a.filename, file_b.filename,
        )

    return ReconciliationSummaryResponse(
        total_checks=summary.total_checks,
        passed=summary.passed,
        failed=summary.failed,
        critical_issues=summary.critical_issues,
        overall_confidence=summary.overall_confidence,
        results=[
            {
                "reconciliation_type": r.reconciliation_type.value,
                "source_a": r.source_a,
                "source_b": r.source_b,
                "field_a": r.field_a,
                "field_b": r.field_b,
                "matches": r.matches,
                "discrepancy_count": r.discrepancy_count,
                "discrepancy_percent": r.discrepancy_percent,
                "severity": r.severity.value,
                "total_variance": r.total_variance,
                "details": r.details,
                "recommendation": r.recommendation,
            }
            for r in summary.results
        ],
    )


@router.post("/analysis/ai-insights", response_model=AIAnalysisReportResponse)
async def generate_ai_insights(
    request: AIInsightsRequest,
    service: IngestionPersistenceService = Depends(get_persistence_service),
):
    """
    Generate AI-powered insights for an uploaded file.

    Uses LLM to provide executive summary, explain anomalies, and suggest follow-up questions.
    """
    from domains.data_ingestion.ai_insights_service import AIInsightsService

    # Get file details
    file_detail = service.get_file(UUID(request.file_id))
    if not file_detail:
        raise HTTPException(status_code=404, detail="File not found")

    # Compile analysis data
    analysis_data = {
        "filename": file_detail.filename,
        "total_rows": file_detail.row_count or 0,
        "overall_quality_score": file_detail.quality_score or 0,
        "detected_categories": file_detail.detected_categories or [],
        "potential_issues": [],
        "anomalies": [],
        "red_flags": [],
    }

    # Extract anomalies and red flags from schema analysis
    if file_detail.schema_analysis and 'sheets' in file_detail.schema_analysis:
        for sheet in file_detail.schema_analysis['sheets']:
            analysis_data['anomalies'].extend(sheet.get('anomalies', []))
            analysis_data['red_flags'].extend(sheet.get('red_flags', []))
            analysis_data['potential_issues'].extend(sheet.get('quality_issues', []))

    try:
        ai_service = AIInsightsService(provider=request.llm_provider)
        report = await ai_service.generate_full_report(
            file_analysis=analysis_data,
            anomalies=analysis_data['anomalies'],
            red_flags=analysis_data['red_flags'],
        )

        return AIAnalysisReportResponse(
            executive_summary=report.executive_summary,
            key_findings=report.key_findings,
            risk_assessment=report.risk_assessment,
            recommendations=report.recommendations,
            follow_up_questions=report.follow_up_questions,
            data_quality_assessment=report.data_quality_assessment,
            generated=True,
        )
    except Exception as e:
        # Return fallback response on error
        return AIAnalysisReportResponse(
            executive_summary=f"AI analysis unavailable: {str(e)}",
            key_findings=[
                f"Data quality score: {analysis_data['overall_quality_score']}/100",
                f"Anomalies detected: {len(analysis_data['anomalies'])}",
                f"Red flags detected: {len(analysis_data['red_flags'])}",
            ],
            risk_assessment="Manual review required",
            recommendations=["Review detected anomalies", "Investigate red flags"],
            follow_up_questions=["Request supporting documentation for flagged items"],
            data_quality_assessment=f"Quality score: {analysis_data['overall_quality_score']}/100",
            generated=False,
        )


# --- Health Check ---

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-ingestion"}
