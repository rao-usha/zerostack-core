"""Investor Ingestion API router - Upload and ingest FO/LP data."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, BackgroundTasks

from .service import InvestorIngestionService
from .models import (
    UploadPreviewResponse,
    IngestionRequest,
    IngestionJobDetail,
    IngestionJobListResponse,
    IngestionJobSummary,
    TargetEntityType,
    FieldMapping,
    TemplateListResponse,
    CreateTemplateRequest,
    MappingTemplate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/investor-ingestion", tags=["investor-ingestion"])


# ========================================
# Upload Endpoints
# ========================================

@router.post("/upload/preview", response_model=UploadPreviewResponse)
async def preview_upload(
    file: UploadFile = File(..., description="CSV or Excel file to upload")
):
    """
    Preview an uploaded file and get mapping suggestions.

    Analyzes the file structure and suggests:
    - Target entity type (family_office, lp_fund, etc.)
    - Field mappings with confidence scores
    - Sample data preview
    """
    try:
        content = await file.read()

        preview = InvestorIngestionService.preview_upload(
            file_content=content,
            filename=file.filename,
            file_type=file.content_type
        )

        return preview

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview file")


@router.post("/upload", response_model=IngestionJobDetail)
async def upload_and_ingest(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV or Excel file to upload"),
    target_entity: TargetEntityType = Form(..., description="Target entity type"),
    field_mappings_json: str = Form(..., description="JSON array of field mappings"),
    parent_id: Optional[int] = Form(None, description="Parent entity ID"),
    process_async: bool = Form(False, description="Process in background")
):
    """
    Upload a file and start ingestion.

    The field_mappings_json should be a JSON string like:
    ```json
    [
        {"source_field": "Name", "target_field": "name"},
        {"source_field": "AUM (USD)", "target_field": "aum", "transform": "float"}
    ]
    ```

    Supported transforms:
    - uppercase, lowercase, strip
    - date_parse
    - float, int
    """
    import json

    try:
        # Parse field mappings
        try:
            mappings_data = json.loads(field_mappings_json)
            field_mappings = [FieldMapping(**m) for m in mappings_data]
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field_mappings_json: {e}"
            )

        content = await file.read()

        # Create job
        job = InvestorIngestionService.create_job(
            file_content=content,
            filename=file.filename,
            file_type=file.content_type,
            target_entity=target_entity,
            field_mappings=field_mappings,
            parent_id=parent_id
        )

        if process_async:
            # Process in background
            background_tasks.add_task(
                InvestorIngestionService.process_job,
                job.id,
                content
            )
            return InvestorIngestionService.get_job(job.id)
        else:
            # Process synchronously
            return InvestorIngestionService.process_job(job.id, content)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process upload")


# ========================================
# Job Endpoints
# ========================================

@router.get("/jobs", response_model=IngestionJobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    target_entity: Optional[str] = Query(None, description="Filter by target entity")
):
    """
    List ingestion jobs with optional filtering.

    Supports filtering by:
    - status: pending, validating, mapping, processing, completed, failed
    - target_entity: family_office, fo_contact, lp_fund, etc.
    """
    try:
        jobs, total = InvestorIngestionService.list_jobs(
            page=page,
            page_size=page_size,
            status=status,
            target_entity=target_entity
        )

        return IngestionJobListResponse(
            jobs=jobs,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.get("/jobs/{job_id}", response_model=IngestionJobDetail)
async def get_job(job_id: str):
    """
    Get full detail for an ingestion job.

    Returns:
    - Job status and progress
    - Row counts (processed, inserted, updated, failed)
    - Field mappings used
    - Errors encountered (up to 100)
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    try:
        job = InvestorIngestionService.get_job(job_uuid)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job")


# ========================================
# Template Endpoints
# ========================================

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    target_entity: Optional[TargetEntityType] = Query(
        None, description="Filter by target entity"
    )
):
    """
    List saved field mapping templates.

    Templates can be reused for consistent field mappings across uploads.
    """
    try:
        templates = InvestorIngestionService.list_templates(target_entity)

        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.post("/templates", response_model=MappingTemplate)
async def create_template(request: CreateTemplateRequest):
    """
    Save a field mapping template for reuse.

    Templates store:
    - Name for identification
    - Target entity type
    - Field mappings with optional transforms
    """
    try:
        template = InvestorIngestionService.save_template(
            name=request.name,
            target_entity=request.target_entity,
            field_mappings=request.field_mappings
        )

        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.get("/templates/{template_id}", response_model=MappingTemplate)
async def get_template(template_id: str):
    """Get a mapping template by ID."""
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    try:
        template = InvestorIngestionService.get_template(template_uuid)

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} not found"
            )

        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template")


# ========================================
# Utility Endpoints
# ========================================

@router.get("/entity-types")
async def list_entity_types():
    """
    List available target entity types.

    Returns all entity types that can be used as ingestion targets.
    """
    return {
        "entity_types": [
            {"value": e.value, "label": e.name.replace("_", " ").title()}
            for e in TargetEntityType
        ]
    }


@router.get("/target-fields/{entity_type}")
async def get_target_fields(entity_type: TargetEntityType):
    """
    Get target fields for an entity type.

    Returns the available target fields that can be mapped to for the given entity.
    """
    from .field_mapper import FieldMapper

    fields = FieldMapper.get_target_fields(entity_type)

    return {
        "entity_type": entity_type.value,
        "fields": fields
    }
