"""Synthetic data generation API router."""
import logging
import io
from typing import Optional, Tuple
from uuid import UUID
from collections import OrderedDict

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from core.rate_limit import limiter
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from .models import (
    SyntheticGenerateRequest, JobResponse, JobStatus, JobStatusResponse,
    SyntheticDatasetResponse, SyntheticDatasetListResponse,
    QualityReportResponse, SynthesizersListResponse, SynthesizerInfo,
    PrivacyLevel, ConditionalGenerateRequest, GenerationCondition,
)
from .service import SyntheticDataService
from .storage import SyntheticDataStorage, get_synthetic_storage
from .quality import (
    MLUtilityEvaluator,
    DetectionEvaluator,
    QualityVisualizer,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/synthetic", tags=["synthetic-data"])


# ============================================================================
# LRU CACHE FOR RECENT DATA
# ============================================================================

class LRUCache:
    """Simple LRU cache for DataFrames."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._cache: OrderedDict[UUID, pd.DataFrame] = OrderedDict()
    
    def get(self, key: UUID) -> Optional[pd.DataFrame]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def put(self, key: UUID, value: pd.DataFrame):
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
        self._cache[key] = value
    
    def __contains__(self, key: UUID) -> bool:
        return key in self._cache


# Caches for recently accessed data (for quality visualizations)
_synthetic_cache = LRUCache(max_size=10)
_source_cache = LRUCache(max_size=10)


def _get_storage() -> SyntheticDataStorage:
    """Get storage service instance."""
    try:
        return get_synthetic_storage()
    except Exception as e:
        logger.warning(f"Object store not available: {e}")
        return None


async def _load_data_pair(
    dataset_id: UUID,
    storage: Optional[SyntheticDataStorage],
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Load synthetic and source data from cache or storage.
    
    Returns:
        Tuple of (synthetic_df, source_df), either can be None
    """
    synthetic_df = _synthetic_cache.get(dataset_id)
    source_df = _source_cache.get(dataset_id)
    
    # Try loading from storage if not in cache
    if storage and synthetic_df is None:
        try:
            synthetic_df = storage.load_dataset(dataset_id)
            _synthetic_cache.put(dataset_id, synthetic_df)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Failed to load synthetic data: {e}")
    
    if storage and source_df is None:
        try:
            source_df = storage.load_source_sample(dataset_id)
            if source_df is not None:
                _source_cache.put(dataset_id, source_df)
        except Exception as e:
            logger.warning(f"Failed to load source sample: {e}")
    
    return synthetic_df, source_df


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
@limiter.limit("5/minute")
async def generate_synthetic_data(
    request_obj: Request,
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
@limiter.limit("5/minute")
async def generate_from_csv(
    request: Request,
    file: UploadFile = File(..., description="CSV file to synthesize"),
    num_rows: int = Query(1000, ge=10, le=100000, description="Number of synthetic rows"),
    synthesizer: str = Query("gaussian_copula", description="Synthesizer type"),
    privacy_level: str = Query("standard", description="Privacy level: standard, enhanced, strict"),
    auto_detect_pii: bool = Query(True, description="Auto-detect PII columns"),
    anonymize_pii: bool = Query(True, description="Replace detected PII with fake data"),
    output_name: Optional[str] = Query(None, description="Name for output dataset"),
    session: AsyncSession = Depends(get_async_session),
):
    """Generate synthetic data from an uploaded CSV file.
    
    This is a convenience endpoint that:
    1. Reads the uploaded CSV
    2. Detects PII columns (if privacy_level != standard)
    3. Creates a generation job
    4. Runs synthesis with PII handling
    5. Returns job info with results
    
    **Privacy levels:**
    - `standard`: No PII detection, basic synthesis
    - `enhanced`: Auto-detect and anonymize PII, assess privacy risk
    - `strict`: Enhanced + more aggressive privacy protection
    """
    from .models import SourceConfig, SynthesizerType, PrivacyConfig
    
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
    
    # Validate privacy level
    try:
        priv_level = PrivacyLevel(privacy_level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid privacy level: {privacy_level}. Must be one of: standard, enhanced, strict"
        )
    
    # Create privacy config
    privacy_config = PrivacyConfig(
        level=priv_level,
        auto_detect_pii=auto_detect_pii,
        anonymize_pii=anonymize_pii,
    )
    
    # Create request
    request = SyntheticGenerateRequest(
        source=SourceConfig(type="dataset", dataset_id=None),
        num_rows=num_rows,
        synthesizer=synth_type,
        privacy=privacy_config,
        output_name=output_name,
    )
    
    service = SyntheticDataService(session)
    storage = _get_storage()
    
    # Create job
    job_id = await service.create_job(request)
    
    # Run job synchronously (for simplicity)
    try:
        dataset_id, synthetic_df = await service.run_job(
            job_id, 
            source_data=df,
            output_name=output_name,
            privacy_level=priv_level,
            auto_detect_pii=auto_detect_pii,
        )
        
        # Get column info
        columns_info = [
            {"name": col, "dtype": str(synthetic_df[col].dtype)}
            for col in synthetic_df.columns
        ]
        
        # Save to persistent storage
        storage_uri = None
        if storage:
            try:
                storage_uri, file_size = storage.save_dataset(
                    dataset_id=dataset_id,
                    df=synthetic_df,
                    job_id=job_id,
                    synthesizer_type=synth_type.value,
                    columns_info=columns_info,
                    quality_score=None,  # Will be updated after quality report
                )
                
                # Save source sample for quality comparisons
                storage.save_source_sample(dataset_id, df)
                
                # Update database with storage URI
                await service.update_dataset_storage(dataset_id, storage_uri, file_size)
                
                logger.info(f"Saved synthetic dataset to {storage_uri}")
            except Exception as e:
                logger.warning(f"Failed to save to object store: {e}")
        
        # Cache for quick access
        _synthetic_cache.put(dataset_id, synthetic_df)
        _source_cache.put(dataset_id, df)
        
        # Get job status
        job_status = await service.get_job_status(job_id)
        
        # Build response message
        quality_str = f"Quality: {job_status.quality_score:.2f}" if job_status.quality_score else ""
        storage_str = " Saved to storage." if storage_uri else ""
        
        return JobResponse(
            job_id=job_id,
            status=job_status.status,
            message=f"Generated {len(synthetic_df)} synthetic rows. {quality_str}{storage_str}",
            estimated_seconds=0,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-conditional", response_model=JobResponse, status_code=202)
@limiter.limit("5/minute")
async def generate_conditional(
    request: Request,
    file: UploadFile = File(..., description="CSV file to synthesize"),
    num_rows: int = Query(1000, ge=10, le=100000, description="Number of synthetic rows"),
    synthesizer: str = Query("gaussian_copula", description="Synthesizer type"),
    conditions_json: str = Query(
        ...,
        description='JSON array of conditions, e.g. [{"column":"region","operator":"eq","value":"US"}]'
    ),
    privacy_level: str = Query("standard", description="Privacy level: standard, enhanced, strict"),
    auto_detect_pii: bool = Query(True, description="Auto-detect PII columns"),
    anonymize_pii: bool = Query(True, description="Replace detected PII with fake data"),
    output_name: Optional[str] = Query(None, description="Name for output dataset"),
    max_tries_per_batch: int = Query(100, ge=10, le=1000, description="Max sampling attempts per batch"),
    oversample_factor: float = Query(2.0, ge=1.1, le=10.0, description="Oversample factor for range conditions"),
    session: AsyncSession = Depends(get_async_session),
):
    """Generate synthetic data with conditions from an uploaded CSV file.

    This endpoint allows generating synthetic data that matches specified conditions.

    **Example conditions:**
    ```json
    [
      {"column": "region", "operator": "eq", "value": "US"},
      {"column": "age", "operator": "gte", "value": 25},
      {"column": "status", "operator": "in", "value": ["active", "premium"]}
    ]
    ```

    **Supported operators:**
    - `eq`: Equal to value
    - `ne`: Not equal to value
    - `gt`, `gte`: Greater than (or equal)
    - `lt`, `lte`: Less than (or equal)
    - `in`: Value in list
    - `not_in`: Value not in list
    - `between`: Between [min, max]

    **Synthesizer recommendations:**
    - `gaussian_copula`: Best for conditional generation (native support)
    - `ctgan`/`tvae`: Use reject sampling (slower but works)
    """
    import json
    from .models import SourceConfig, SynthesizerType, PrivacyConfig, ConditionOperator
    from .conditions import ConditionProcessor, ConditionValidationError

    # Read CSV
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        logger.info(f"Loaded CSV with {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")

    if len(df) < 10:
        raise HTTPException(status_code=400, detail="Source data must have at least 10 rows")

    # Parse conditions
    try:
        conditions_raw = json.loads(conditions_json)
        if not isinstance(conditions_raw, list):
            raise ValueError("Conditions must be a JSON array")

        conditions = [
            GenerationCondition(
                column=c["column"],
                operator=ConditionOperator(c["operator"]),
                value=c["value"],
            )
            for c in conditions_raw
        ]
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in conditions: {str(e)}")
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid condition format: {str(e)}")

    # Validate conditions
    processor = ConditionProcessor()
    try:
        warnings = processor.validate_conditions(conditions, df)
    except ConditionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate synthesizer type
    try:
        synth_type = SynthesizerType(synthesizer)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid synthesizer: {synthesizer}. Must be one of: gaussian_copula, ctgan, tvae"
        )

    # Validate privacy level
    try:
        priv_level = PrivacyLevel(privacy_level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid privacy level: {privacy_level}. Must be one of: standard, enhanced, strict"
        )

    # Create privacy config
    privacy_config = PrivacyConfig(
        level=priv_level,
        auto_detect_pii=auto_detect_pii,
        anonymize_pii=anonymize_pii,
    )

    # Create request
    gen_request = SyntheticGenerateRequest(
        source=SourceConfig(type="dataset", dataset_id=None),
        num_rows=num_rows,
        synthesizer=synth_type,
        privacy=privacy_config,
        output_name=output_name,
    )

    service = SyntheticDataService(session)
    storage = _get_storage()

    # Create job
    job_id = await service.create_job(gen_request)

    # Run job with conditions
    try:
        dataset_id, synthetic_df = await service.run_job(
            job_id,
            source_data=df,
            output_name=output_name,
            privacy_level=priv_level,
            auto_detect_pii=auto_detect_pii,
            conditions=conditions,
            max_tries_per_batch=max_tries_per_batch,
            oversample_factor=oversample_factor,
        )

        # Get column info
        columns_info = [
            {"name": col, "dtype": str(synthetic_df[col].dtype)}
            for col in synthetic_df.columns
        ]

        # Save to persistent storage
        storage_uri = None
        if storage:
            try:
                storage_uri, file_size = storage.save_dataset(
                    dataset_id=dataset_id,
                    df=synthetic_df,
                    job_id=job_id,
                    synthesizer_type=synth_type.value,
                    columns_info=columns_info,
                    quality_score=None,
                )

                # Save source sample for quality comparisons
                storage.save_source_sample(dataset_id, df)

                # Update database with storage URI
                await service.update_dataset_storage(dataset_id, storage_uri, file_size)

                logger.info(f"Saved conditional synthetic dataset to {storage_uri}")
            except Exception as e:
                logger.warning(f"Failed to save to object store: {e}")

        # Cache for quick access
        _synthetic_cache.put(dataset_id, synthetic_df)
        _source_cache.put(dataset_id, df)

        # Get job status
        job_status = await service.get_job_status(job_id)

        # Build response message
        quality_str = f"Quality: {job_status.quality_score:.2f}" if job_status.quality_score else ""
        storage_str = " Saved to storage." if storage_uri else ""
        cond_str = f" ({len(conditions)} conditions applied)"

        return JobResponse(
            job_id=job_id,
            status=job_status.status,
            message=f"Generated {len(synthetic_df)} conditional synthetic rows.{cond_str} {quality_str}{storage_str}",
            estimated_seconds=0,
        )
    except Exception as e:
        logger.error(f"Conditional generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-conditional-json", response_model=JobResponse, status_code=202)
@limiter.limit("5/minute")
async def generate_conditional_json(
    request: Request,
    body: ConditionalGenerateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Generate conditional synthetic data (JSON body version).

    This endpoint accepts the full request as JSON body. Use this when you have
    the source data already loaded or are calling from a programmatic client.

    Note: This endpoint requires source data to be available via dataset_id or table_ref.
    For CSV upload, use /generate-conditional instead.
    """
    from .conditions import ConditionProcessor, ConditionValidationError

    service = SyntheticDataService(session)

    # For now, we need the source data to be provided
    if body.source.type == "dataset":
        if not body.source.dataset_id:
            raise HTTPException(
                status_code=400,
                detail="dataset_id required for dataset source type"
            )
        raise HTTPException(
            status_code=501,
            detail="Dataset source not yet implemented. Use /generate-conditional endpoint with CSV upload."
        )
    elif body.source.type == "table":
        if not body.source.connection_id or not body.source.table_ref:
            raise HTTPException(
                status_code=400,
                detail="connection_id and table_ref required for table source type"
            )
        raise HTTPException(
            status_code=501,
            detail="Table source not yet implemented. Use /generate-conditional endpoint with CSV upload."
        )

    raise HTTPException(status_code=400, detail="Invalid source type")


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
    use_presigned: bool = Query(False, description="Use presigned URL redirect"),
    session: AsyncSession = Depends(get_async_session),
):
    """Download synthetic dataset as CSV or Parquet.
    
    Options:
    - Direct download (default): Streams data through the API
    - Presigned URL: Redirects to S3/MinIO for large files
    """
    storage = _get_storage()
    
    # Try presigned URL for large files
    if use_presigned and storage:
        try:
            if storage.exists(dataset_id):
                url = storage.get_download_url(dataset_id, format=format, expires_in=3600)
                return RedirectResponse(url=url, status_code=307)
        except Exception as e:
            logger.warning(f"Presigned URL failed: {e}")
    
    # Try cache first
    df = _synthetic_cache.get(dataset_id)
    
    # Try loading from storage
    if df is None and storage:
        try:
            df = storage.load_dataset(dataset_id, format=format)
            _synthetic_cache.put(dataset_id, df)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Failed to load from storage: {e}")
    
    if df is None:
        raise HTTPException(
            status_code=404, 
            detail="Dataset not found. It may have been deleted or storage is unavailable."
        )
    
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
    storage = _get_storage()
    
    # Try cache first
    df = _synthetic_cache.get(dataset_id)
    
    # Try loading from storage
    if df is None and storage:
        try:
            df = storage.load_dataset(dataset_id)
            _synthetic_cache.put(dataset_id, df)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Failed to load from storage: {e}")
    
    if df is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )
    
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


@router.delete("/datasets/{dataset_id}")
async def delete_synthetic_dataset(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Delete a synthetic dataset and its storage.
    
    This permanently removes:
    - Database records (dataset, quality report)
    - Object storage files (parquet, csv, manifest)
    """
    service = SyntheticDataService(session)
    
    # Check if exists
    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Delete
    await service.delete_dataset(dataset_id)
    
    # Clear from cache
    if dataset_id in _synthetic_cache:
        del _synthetic_cache._cache[dataset_id]
    if dataset_id in _source_cache:
        del _source_cache._cache[dataset_id]
    
    return {"message": f"Dataset {dataset_id} deleted", "dataset_id": str(dataset_id)}


@router.get("/datasets/{dataset_id}/storage-info")
async def get_storage_info(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get storage information for a synthetic dataset.
    
    Returns details about stored files, sizes, and availability.
    """
    storage = _get_storage()
    
    if not storage:
        raise HTTPException(status_code=503, detail="Object storage not available")
    
    try:
        info = storage.get_storage_info(dataset_id)
        return {
            "dataset_id": str(dataset_id),
            **info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage info: {str(e)}")


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
# QUALITY VISUALIZATIONS
# ============================================================================

@router.get("/datasets/{dataset_id}/distributions")
async def get_distribution_comparison(
    dataset_id: UUID,
    columns: Optional[str] = Query(None, description="Comma-separated column names"),
    session: AsyncSession = Depends(get_async_session),
):
    """Get distribution comparison data for visualizations.
    
    Returns histogram data for numeric columns and category counts for categorical columns.
    Data is formatted for easy frontend charting (e.g., Chart.js, Recharts, Plotly).
    
    Response includes:
    - Histogram bins and counts for numeric columns
    - Category counts and percentages for categorical columns  
    - Summary statistics for both real and synthetic data
    """
    storage = _get_storage()
    synthetic_df, source_df = await _load_data_pair(dataset_id, storage)
    
    if synthetic_df is None:
        raise HTTPException(status_code=404, detail="Synthetic dataset not found")
    if source_df is None:
        raise HTTPException(status_code=404, detail="Source data not available")
    
    # Parse columns
    col_list = None
    if columns:
        col_list = [c.strip() for c in columns.split(",")]
    
    visualizer = QualityVisualizer()
    comparison = visualizer.generate_distribution_comparison(source_df, synthetic_df, col_list)
    
    return {
        "dataset_id": str(dataset_id),
        "numeric_columns": [
            {
                "column_name": h.column_name,
                "dtype": h.dtype,
                "bins": h.bins,
                "real_counts": h.real_counts,
                "synthetic_counts": h.synthetic_counts,
                "real_density": h.real_density,
                "synthetic_density": h.synthetic_density,
                "statistics": h.statistics,
            }
            for h in comparison.numeric_columns
        ],
        "categorical_columns": [
            {
                "column_name": c.column_name,
                "categories": c.categories,
                "real_counts": c.real_counts,
                "synthetic_counts": c.synthetic_counts,
                "real_percentages": c.real_percentages,
                "synthetic_percentages": c.synthetic_percentages,
            }
            for c in comparison.categorical_columns
        ],
        "summary": comparison.summary,
    }


@router.get("/datasets/{dataset_id}/correlations")
async def get_correlation_comparison(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get correlation matrix comparison for heatmap visualization.
    
    Returns correlation matrices for real and synthetic data, plus the difference.
    Use this data to render correlation heatmaps in the frontend.
    
    Response includes:
    - Column names
    - Real data correlation matrix
    - Synthetic data correlation matrix
    - Difference matrix (real - synthetic)
    - Summary statistics (mean/max absolute difference)
    """
    storage = _get_storage()
    synthetic_df, source_df = await _load_data_pair(dataset_id, storage)
    
    if synthetic_df is None:
        raise HTTPException(status_code=404, detail="Synthetic dataset not found")
    if source_df is None:
        raise HTTPException(status_code=404, detail="Source data not available")
    
    visualizer = QualityVisualizer()
    comparison = visualizer.generate_correlation_comparison(source_df, synthetic_df)
    
    return {
        "dataset_id": str(dataset_id),
        "columns": comparison.columns,
        "real_correlation": comparison.real_correlation,
        "synthetic_correlation": comparison.synthetic_correlation,
        "difference": comparison.difference,
        "summary": comparison.summary,
    }


@router.get("/datasets/{dataset_id}/stats")
async def get_summary_statistics(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get summary statistics comparison.
    
    Returns per-column statistics for real vs synthetic data:
    - Numeric: mean, std, min, max, null %
    - Categorical: unique count, mode, null %
    """
    storage = _get_storage()
    synthetic_df, source_df = await _load_data_pair(dataset_id, storage)
    
    if synthetic_df is None:
        raise HTTPException(status_code=404, detail="Synthetic dataset not found")
    if source_df is None:
        raise HTTPException(status_code=404, detail="Source data not available")
    
    visualizer = QualityVisualizer()
    stats = visualizer.generate_summary_stats(source_df, synthetic_df)
    
    return {
        "dataset_id": str(dataset_id),
        **stats,
    }


@router.get("/datasets/{dataset_id}/ml-utility")
async def get_ml_utility(
    dataset_id: UUID,
    target_column: str = Query(..., description="Target column for ML task"),
    task_type: Optional[str] = Query(None, description="classification or regression (auto-detected if not specified)"),
    session: AsyncSession = Depends(get_async_session),
):
    """Evaluate ML utility of synthetic data.
    
    Tests how well a model trained on synthetic data performs on real data.
    Uses TSTR (Train on Synthetic, Test on Real) methodology.
    
    Response includes:
    - Overall utility score (0-1)
    - TSTR metrics (accuracy/F1 for classification, R2/RMSE for regression)
    - TRTR baseline metrics (trained on real data)
    - Utility ratio (TSTR / TRTR)
    - Feature importance correlation
    """
    storage = _get_storage()
    synthetic_df, source_df = await _load_data_pair(dataset_id, storage)
    
    if synthetic_df is None:
        raise HTTPException(status_code=404, detail="Synthetic dataset not found")
    if source_df is None:
        raise HTTPException(status_code=404, detail="Source data not available")
    
    if target_column not in source_df.columns:
        raise HTTPException(
            status_code=400, 
            detail=f"Target column '{target_column}' not found in data"
        )
    
    evaluator = MLUtilityEvaluator()
    
    try:
        report = evaluator.evaluate(
            source_df, 
            synthetic_df, 
            target_column,
            task_type=task_type,
        )
        
        return {
            "dataset_id": str(dataset_id),
            "target_column": report.target_column,
            "task_type": report.task_type,
            "overall_score": report.overall_score,
            "tstr": {
                "score": report.tstr_score,
                "metrics": report.tstr_metrics,
            },
            "trtr": {
                "score": report.trtr_score,
                "metrics": report.trtr_metrics,
            },
            "utility_ratio": report.utility_ratio,
            "feature_importance_correlation": report.feature_importance_correlation,
            "recommendations": report.recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML utility evaluation failed: {str(e)}")


@router.get("/datasets/{dataset_id}/detection")
async def get_detection_score(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Evaluate how distinguishable synthetic data is from real.
    
    Tests if a classifier can tell real from synthetic records.
    A good synthetic dataset should be indistinguishable (accuracy ≈ 0.5).
    
    Response includes:
    - Overall score (higher = less detectable = better)
    - Detection accuracy and AUC
    - Cross-validation scores
    - Most distinguishing features (columns that give it away)
    """
    storage = _get_storage()
    synthetic_df, source_df = await _load_data_pair(dataset_id, storage)
    
    if synthetic_df is None:
        raise HTTPException(status_code=404, detail="Synthetic dataset not found")
    if source_df is None:
        raise HTTPException(status_code=404, detail="Source data not available")
    
    evaluator = DetectionEvaluator()
    
    try:
        report = evaluator.evaluate(source_df, synthetic_df)
        
        return {
            "dataset_id": str(dataset_id),
            "overall_score": report.overall_score,
            "detection_accuracy": report.detection_accuracy,
            "detection_auc": report.detection_auc,
            "cross_validation": {
                "scores": report.cv_scores,
                "mean": report.cv_mean,
                "std": report.cv_std,
            },
            "model_results": report.model_results,
            "distinguishing_features": [
                {"column": f[0], "importance": f[1]} 
                for f in report.distinguishing_features
            ],
            "recommendations": report.recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection evaluation failed: {str(e)}")


@router.get("/datasets/{dataset_id}/quality-dashboard")
async def get_quality_dashboard(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get comprehensive quality dashboard data.
    
    Combines all quality metrics in a single response:
    - Quality report (overall scores)
    - Summary statistics
    - Distribution previews (first 5 columns)
    - Correlation summary
    
    For detailed visualizations, use the specific endpoints.
    """
    storage = _get_storage()
    synthetic_df, source_df = await _load_data_pair(dataset_id, storage)
    
    if synthetic_df is None:
        raise HTTPException(status_code=404, detail="Synthetic dataset not found")
    if source_df is None:
        raise HTTPException(status_code=404, detail="Source data not available")
    
    # Get quality report from database
    service = SyntheticDataService(session)
    quality_report = await service.get_quality_report(dataset_id)
    
    # Generate visualization summaries
    visualizer = QualityVisualizer()
    
    # Get first 5 columns for preview
    preview_cols = list(synthetic_df.columns)[:5]
    dist_comparison = visualizer.generate_distribution_comparison(source_df, synthetic_df, preview_cols)
    corr_comparison = visualizer.generate_correlation_comparison(source_df, synthetic_df)
    summary_stats = visualizer.generate_summary_stats(source_df, synthetic_df)
    
    return {
        "dataset_id": str(dataset_id),
        "quality_report": {
            "overall_score": quality_report.overall_score if quality_report else None,
            "statistical_fidelity_score": quality_report.statistical_fidelity_score if quality_report else None,
            "correlation_score": quality_report.correlation_score if quality_report else None,
            "privacy_score": quality_report.privacy_score if quality_report else None,
            "recommendations": quality_report.recommendations if quality_report else [],
            "warnings": quality_report.warnings if quality_report else [],
        },
        "summary_stats": {
            "real_rows": summary_stats["real_rows"],
            "synthetic_rows": summary_stats["synthetic_rows"],
            "total_columns": summary_stats["total_columns"],
        },
        "distribution_preview": {
            "numeric_count": len(dist_comparison.numeric_columns),
            "categorical_count": len(dist_comparison.categorical_columns),
            "columns_shown": preview_cols,
        },
        "correlation_summary": corr_comparison.summary,
        "available_endpoints": {
            "distributions": f"/api/v1/synthetic/datasets/{dataset_id}/distributions",
            "correlations": f"/api/v1/synthetic/datasets/{dataset_id}/correlations",
            "stats": f"/api/v1/synthetic/datasets/{dataset_id}/stats",
            "ml_utility": f"/api/v1/synthetic/datasets/{dataset_id}/ml-utility?target_column=<column>",
            "detection": f"/api/v1/synthetic/datasets/{dataset_id}/detection",
            "privacy_risk": f"/api/v1/synthetic/datasets/{dataset_id}/privacy-risk",
        },
    }


# ============================================================================
# PRIVACY
# ============================================================================

@router.post("/detect-pii")
async def detect_pii_in_csv(
    file: UploadFile = File(..., description="CSV file to analyze for PII"),
    session: AsyncSession = Depends(get_async_session),
):
    """Detect PII columns in an uploaded CSV file.
    
    Analyzes the file for common PII patterns:
    - Email addresses
    - Phone numbers
    - SSN/Tax IDs
    - Names (first, last, full)
    - Addresses, cities, states, zip codes
    - Credit card numbers
    - IP addresses
    - Dates of birth
    
    Returns detected columns with confidence scores and recommendations.
    """
    # Read CSV
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")
    
    service = SyntheticDataService(session)
    result = service.detect_pii(df)
    
    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "pii_detection": result,
    }


@router.get("/datasets/{dataset_id}/privacy-risk")
async def get_privacy_risk_assessment(
    dataset_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get privacy risk assessment for a synthetic dataset.
    
    Evaluates:
    - Uniqueness risk: columns that could be quasi-identifiers
    - Similarity risk: synthetic records too close to real records
    - Outlier risk: extreme values that might be re-identifiable
    
    Returns risk level (low/medium/high) and recommendations.
    """
    storage = _get_storage()
    synthetic_df, source_df = await _load_data_pair(dataset_id, storage)
    
    if synthetic_df is None:
        raise HTTPException(
            status_code=404,
            detail="Synthetic dataset not found"
        )
    
    if source_df is None:
        raise HTTPException(
            status_code=404,
            detail="Source data not available for privacy assessment."
        )
    
    service = SyntheticDataService(session)
    risk_assessment = service.assess_privacy_risk(source_df, synthetic_df)
    
    return {
        "dataset_id": str(dataset_id),
        "assessment": risk_assessment,
    }


@router.get("/privacy/pii-types")
async def list_pii_types():
    """List all supported PII types that can be detected and generated."""
    from .privacy import PIIType, FakerPIIGenerator
    
    return {
        "supported_types": [
            {
                "type": pii_type.value,
                "description": f"Detects and generates fake {pii_type.value.replace('_', ' ')}",
            }
            for pii_type in PIIType
        ],
        "generator_info": FakerPIIGenerator.get_generator_info(),
    }


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


# ============================================================================
# TABDIT ENDPOINTS
# ============================================================================

@router.post("/tabdit/models", status_code=201)
async def create_tabdit_model(
    request: Request,
    name: str = Query(..., description="Model name"),
    description: Optional[str] = Query(None, description="Model description"),
    source_table_ref: Optional[str] = Query(None, description="Source table reference (schema.table)"),
    vae_latent_dim: int = Query(128, ge=32, le=512, description="VAE latent dimension"),
    vae_epochs: int = Query(100, ge=10, le=500, description="VAE training epochs"),
    diffusion_layers: int = Query(6, ge=2, le=12, description="Diffusion transformer layers"),
    diffusion_epochs: int = Query(200, ge=50, le=1000, description="Diffusion training epochs"),
    inference_steps: int = Query(50, ge=10, le=200, description="Generation inference steps"),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new TabDiT model for training.

    TabDiT is a diffusion-based synthesizer that produces high-quality synthetic data.
    Training happens in two phases:
    1. VAE training - learns to compress data to latent space
    2. Diffusion training - learns to generate latent vectors

    After creation, training must be initiated separately (e.g., via GPU job queue).
    """
    from .service import TabDiTService

    vae_config = {
        "latent_dim": vae_latent_dim,
        "epochs": vae_epochs,
    }
    diffusion_config = {
        "num_layers": diffusion_layers,
        "epochs": diffusion_epochs,
        "num_inference_steps": inference_steps,
    }

    service = TabDiTService(session)
    model_id = await service.create_model(
        name=name,
        description=description,
        source_table_ref=source_table_ref,
        vae_config=vae_config,
        diffusion_config=diffusion_config,
    )

    return {
        "model_id": str(model_id),
        "name": name,
        "status": "pending",
        "message": "TabDiT model created. Training must be initiated separately.",
    }


@router.get("/tabdit/models")
async def list_tabdit_models(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """List all TabDiT models."""
    from .service import TabDiTService

    service = TabDiTService(session)
    models, total = await service.list_models(limit=limit, offset=offset)

    return {
        "models": models,
        "total": total,
    }


@router.get("/tabdit/models/{model_id}")
async def get_tabdit_model(
    model_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get TabDiT model details and training status."""
    from .service import TabDiTService

    service = TabDiTService(session)
    model = await service.get_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="TabDiT model not found")

    return model


@router.delete("/tabdit/models/{model_id}")
async def delete_tabdit_model(
    model_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Delete a TabDiT model and its checkpoints."""
    from .service import TabDiTService

    service = TabDiTService(session)
    model = await service.get_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="TabDiT model not found")

    await service.delete_model(model_id)

    return {
        "message": f"TabDiT model {model_id} deleted",
        "model_id": str(model_id),
    }


@router.post("/tabdit/models/{model_id}/generate")
@limiter.limit("5/minute")
async def generate_from_tabdit(
    request: Request,
    model_id: UUID,
    num_rows: int = Query(1000, ge=10, le=100000, description="Number of rows to generate"),
    output_name: Optional[str] = Query(None, description="Name for output dataset"),
    session: AsyncSession = Depends(get_async_session),
):
    """Generate synthetic data using a trained TabDiT model.

    The model must be in 'completed' status (both VAE and diffusion trained).
    Generation uses DDIM sampling with configurable inference steps.
    """
    from .service import TabDiTService

    service = TabDiTService(session)
    model = await service.get_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="TabDiT model not found")

    if model["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Model is not ready for generation. Status: {model['status']}"
        )

    # Check checkpoints exist
    if not model.get("vae_checkpoint_uri") or not model.get("diffusion_checkpoint_uri"):
        raise HTTPException(
            status_code=400,
            detail="Model checkpoints not found. Training may not have completed properly."
        )

    # Note: Actual generation would be done asynchronously or via a job queue
    # This endpoint returns information about how to trigger generation
    return {
        "model_id": str(model_id),
        "num_rows": num_rows,
        "status": "queued",
        "message": (
            "Generation request received. In production, this would be processed "
            "by a GPU worker. For local testing, use the TabDiTSynthesizer directly."
        ),
        "vae_checkpoint": model["vae_checkpoint_uri"],
        "diffusion_checkpoint": model["diffusion_checkpoint_uri"],
    }


@router.get("/tabdit/models/{model_id}/sample-preview")
async def tabdit_sample_preview(
    model_id: UUID,
    num_rows: int = Query(10, ge=1, le=100, description="Number of preview rows"),
    session: AsyncSession = Depends(get_async_session),
):
    """Generate a small preview sample from a TabDiT model.

    Quick preview of generated data (limited to 100 rows).
    For larger generations, use the /generate endpoint.
    """
    from .service import TabDiTService

    service = TabDiTService(session)
    model = await service.get_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="TabDiT model not found")

    if model["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Model is not ready for generation. Status: {model['status']}"
        )

    return {
        "model_id": str(model_id),
        "preview_rows": num_rows,
        "status": "preview_not_implemented",
        "message": (
            "Preview generation requires loading models to GPU. "
            "In production, use the job queue for generation."
        ),
    }


@router.get("/tabdit/info")
async def get_tabdit_info():
    """Get information about the TabDiT synthesizer."""
    from .synthesizers import TabDiTSynthesizer

    return TabDiTSynthesizer.get_info()
