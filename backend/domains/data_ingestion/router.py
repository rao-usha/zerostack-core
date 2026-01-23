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


# --- Health Check ---

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-ingestion"}
