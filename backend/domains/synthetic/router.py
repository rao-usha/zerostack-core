"""Synthetic data generation API router."""
import logging
import io
from typing import Optional
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from .models import (
    SyntheticGenerateRequest, JobResponse, JobStatus, JobStatusResponse,
    SyntheticDatasetResponse, SyntheticDatasetListResponse,
    QualityReportResponse, SynthesizersListResponse, SynthesizerInfo,
)
from .service import SyntheticDataService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/synthetic", tags=["synthetic-data"])


# ============================================================================
# SESSION DEPENDENCY
# ============================================================================

async def get_async_session():
    """Get async database session."""
    async_url = settings.database_url.replace('postgresql+psycopg', 'postgresql+asyncpg')
    if 'asyncpg' not in async_url:
        async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(async_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.commit()


# In-memory storage for synthetic data (temporary - should use MinIO in production)
_synthetic_data_cache: dict[UUID, pd.DataFrame] = {}


# ============================================================================
# SYNTHESIZER INFO
# ============================================================================

@router.get("/synthesizers", response_model=SynthesizersListResponse)
async def list_synthesizers():
    """List available synthesizer algorithms.
    
    Returns information about each synthesizer including:
    - Speed and quality characteristics
    - GPU requirements
    - Best use cases
    - Configuration options
    """
    infos = SyntheticDataService.get_synthesizer_info()
    return SynthesizersListResponse(
        synthesizers=[SynthesizerInfo(**info) for info in infos]
    )


# ============================================================================
# GENERATION
# ============================================================================

@router.post("/generate", response_model=JobResponse, status_code=202)
async def generate_synthetic_data(
    request: SyntheticGenerateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Start synthetic data generation job.
    
    This endpoint creates a generation job and runs it synchronously for now.
    For large datasets or deep learning synthesizers, consider using async processing.
    
    **Synthesizer options:**
    - `gaussian_copula`: Fast, good default for most data
    - `ctgan`: Best quality, slower, benefits from GPU
    - `tvae`: Good quality, more stable than CTGAN
    
    **Privacy options:**
    - `level`: standard (default), enhanced (PII detection), strict (DP)
    - `auto_detect_pii`: Automatically detect PII columns
    - `anonymize_pii`: Replace PII with fake data
    """
    service = SyntheticDataService(session)
    
    # For now, we need the source data to be provided
    # In the future, this could load from dataset_id or connection_id
    if request.source.type == "dataset":
        if not request.source.dataset_id:
            raise HTTPException(
                status_code=400, 
                detail="dataset_id required for dataset source type"
            )
        # TODO: Load dataset from storage
        raise HTTPException(
            status_code=501,
            detail="Dataset source not yet implemented. Use /generate-from-csv endpoint."
        )
    elif request.source.type == "table":
        if not request.source.connection_id or not request.source.table_ref:
            raise HTTPException(
                status_code=400,
                detail="connection_id and table_ref required for table source type"
            )
        # TODO: Load table from connection
        raise HTTPException(
            status_code=501,
            detail="Table source not yet implemented. Use /generate-from-csv endpoint."
        )
    
    raise HTTPException(status_code=400, detail="Invalid source type")


@router.post("/generate-from-csv", response_model=JobResponse, status_code=202)
async def generate_from_csv(
    file: UploadFile = File(..., description="CSV file to synthesize"),
    num_rows: int = Query(1000, ge=10, le=100000, description="Number of synthetic rows"),
    synthesizer: str = Query("gaussian_copula", description="Synthesizer type"),
    output_name: Optional[str] = Query(None, description="Name for output dataset"),
    session: AsyncSession = Depends(get_async_session),
):
    """Generate synthetic data from an uploaded CSV file.
    
    This is a convenience endpoint that:
    1. Reads the uploaded CSV
    2. Creates a generation job
    3. Runs synthesis synchronously
    4. Returns job info with results
    
    For production use, prefer the async /generate endpoint with stored datasets.
    """
    from .models import SourceConfig, SynthesizerType
    
    # Read CSV
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        logger.info(f"Loaded CSV with {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")
    
    if len(df) < 10:
        raise HTTPException(status_code=400, detail="Source data must have at least 10 rows")
    
    # Validate synthesizer type
    try:
        synth_type = SynthesizerType(synthesizer)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid synthesizer: {synthesizer}. Must be one of: gaussian_copula, ctgan, tvae"
        )
    
    # Create request
    request = SyntheticGenerateRequest(
        source=SourceConfig(type="dataset", dataset_id=None),
        num_rows=num_rows,
        synthesizer=synth_type,
        output_name=output_name,
    )
    
    service = SyntheticDataService(session)
    
    # Create job
    job_id = await service.create_job(request)
    
    # Run job synchronously (for simplicity)
    try:
        dataset_id, synthetic_df = await service.run_job(
            job_id, 
            source_data=df,
            output_name=output_name,
        )
        
        # Cache synthetic data for download
        _synthetic_data_cache[dataset_id] = synthetic_df
        
        # Get job status
        job_status = await service.get_job_status(job_id)
        
        return JobResponse(
            job_id=job_id,
            status=job_status.status,
            message=f"Generated {len(synthetic_df)} synthetic rows. Quality score: {job_status.quality_score:.2f}",
            estimated_seconds=0,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# JOB STATUS
# ============================================================================

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get the status of a synthetic generation job."""
    service = SyntheticDataService(session)
    status = await service.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status


# ============================================================================
# DATASETS
# ============================================================================

@router.get("/datasets", response_model=SyntheticDatasetListResponse)
async def list_synthetic_datasets(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """List all synthetic datasets."""
    service = SyntheticDataService(session)
    datasets, total = await service.list_datasets(limit=limit, offset=offset)
    
    return SyntheticDatasetListResponse(datasets=datasets, total=total)


@router.get("/datasets/{dataset_id}", response_model=SyntheticDatasetResponse)
async def get_synthetic_dataset(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get a synthetic dataset by ID."""
    service = SyntheticDataService(session)
    dataset = await service.get_dataset(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset


@router.get("/datasets/{dataset_id}/download")
async def download_synthetic_dataset(
    dataset_id: UUID,
    format: str = Query("csv", pattern="^(csv|parquet)$"),
    session: AsyncSession = Depends(get_async_session),
):
    """Download synthetic dataset as CSV or Parquet."""
    # Check if we have it cached
    if dataset_id not in _synthetic_data_cache:
        raise HTTPException(
            status_code=404, 
            detail="Dataset not found in cache. Data is only available for recently generated datasets."
        )
    
    df = _synthetic_data_cache[dataset_id]
    
    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=synthetic_{dataset_id.hex[:8]}.csv"
            }
        )
    else:  # parquet
        output = io.BytesIO()
        df.to_parquet(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=synthetic_{dataset_id.hex[:8]}.parquet"
            }
        )


@router.get("/datasets/{dataset_id}/preview")
async def preview_synthetic_dataset(
    dataset_id: UUID,
    limit: int = Query(100, le=1000),
    session: AsyncSession = Depends(get_async_session),
):
    """Preview rows from a synthetic dataset."""
    if dataset_id not in _synthetic_data_cache:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found in cache"
        )
    
    df = _synthetic_data_cache[dataset_id]
    preview_df = df.head(limit)
    
    return {
        "dataset_id": str(dataset_id),
        "total_rows": len(df),
        "showing": len(preview_df),
        "columns": [
            {"name": col, "dtype": str(df[col].dtype)}
            for col in df.columns
        ],
        "rows": preview_df.to_dict(orient="records"),
    }


# ============================================================================
# QUALITY
# ============================================================================

@router.get("/datasets/{dataset_id}/quality", response_model=QualityReportResponse)
async def get_quality_report(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get the quality evaluation report for a synthetic dataset."""
    service = SyntheticDataService(session)
    report = await service.get_quality_report(dataset_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Quality report not found")
    
    return report


# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

@router.post("/generate-legacy")
async def generate_synthetic_legacy(
    dataset_id: str,
    num_rows: int = 1000,
):
    """Legacy endpoint for backward compatibility.
    
    This mimics the old /api/synthetic/generate endpoint.
    Deprecated - use /generate-from-csv instead.
    """
    raise HTTPException(
        status_code=501,
        detail="Legacy endpoint not implemented. Use /api/v1/synthetic/generate-from-csv instead."
    )
