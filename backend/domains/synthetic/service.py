"""Synthetic data generation service."""
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from decimal import Decimal

import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import synthetic_jobs, synthetic_datasets, synthetic_quality_reports
from .models import (
    SyntheticGenerateRequest, JobStatus, SynthesizerType,
    JobStatusResponse, SyntheticDatasetResponse, QualityReportResponse, QualityColumnScore
)
from .synthesizers import GaussianCopulaSynthesizer, CTGANSynthesizer, TVAESynthesizer
from .evaluator import SyntheticDataEvaluator

logger = logging.getLogger(__name__)


class SyntheticDataService:
    """Service for synthetic data generation."""
    
    # Map synthesizer types to classes
    SYNTHESIZERS = {
        SynthesizerType.GAUSSIAN_COPULA: GaussianCopulaSynthesizer,
        SynthesizerType.CTGAN: CTGANSynthesizer,
        SynthesizerType.TVAE: TVAESynthesizer,
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evaluator = SyntheticDataEvaluator()
    
    async def create_job(
        self,
        request: SyntheticGenerateRequest,
        created_by: str = "user",
    ) -> UUID:
        """Create a new synthetic generation job.
        
        Args:
            request: Generation request
            created_by: User creating the job
            
        Returns:
            Job ID
        """
        job_id = uuid4()
        
        # Build config based on synthesizer type
        config = {}
        if request.synthesizer == SynthesizerType.GAUSSIAN_COPULA and request.copula_config:
            config = request.copula_config.model_dump()
        elif request.synthesizer == SynthesizerType.CTGAN and request.ctgan_config:
            config = request.ctgan_config.model_dump()
        elif request.synthesizer == SynthesizerType.TVAE and request.tvae_config:
            config = request.tvae_config.model_dump()
        
        # Privacy config
        privacy_config = request.privacy.model_dump() if request.privacy else {}
        
        # Column configs
        column_configs = {}
        if request.columns:
            column_configs = {
                col: cfg.model_dump() for col, cfg in request.columns.items()
            }
        
        # Insert job record
        await self.session.execute(
            synthetic_jobs.insert().values(
                id=job_id,
                source_dataset_id=request.source.dataset_id,
                source_table_ref=request.source.table_ref,
                source_connection_id=request.source.connection_id,
                synthesizer_type=request.synthesizer.value,
                config=config,
                privacy_config=privacy_config,
                column_configs=column_configs,
                num_rows_requested=request.num_rows,
                random_seed=request.random_seed,
                status=JobStatus.PENDING.value,
                created_by=created_by,
            )
        )
        await self.session.commit()
        
        logger.info(f"Created synthetic job {job_id} for {request.num_rows} rows with {request.synthesizer.value}")
        
        return job_id
    
    async def run_job(
        self,
        job_id: UUID,
        source_data: pd.DataFrame,
        output_name: Optional[str] = None,
    ) -> UUID:
        """Run a synthetic generation job.
        
        This is the main entry point for generation. It:
        1. Updates job status to running
        2. Initializes and fits the synthesizer
        3. Generates synthetic data
        4. Evaluates quality
        5. Stores results
        6. Updates job status
        
        Args:
            job_id: Job ID
            source_data: Source data to synthesize
            output_name: Optional name for output dataset
            
        Returns:
            Synthetic dataset ID
        """
        # Get job details
        result = await self.session.execute(
            select(synthetic_jobs).where(synthetic_jobs.c.id == job_id)
        )
        job = result.fetchone()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Update status to running
        await self._update_job_status(job_id, JobStatus.RUNNING, "Starting synthesis...")
        
        try:
            start_time = time.time()
            
            # Get synthesizer class
            synth_type = SynthesizerType(job.synthesizer_type)
            synth_class = self.SYNTHESIZERS[synth_type]
            
            # Initialize synthesizer with config
            config = job.config or {}
            synthesizer = synth_class(config=config)
            
            # Prepare metadata from column configs
            metadata = {}
            if job.column_configs:
                for col, col_cfg in job.column_configs.items():
                    if col_cfg.get('sdtype'):
                        metadata[col] = {'sdtype': col_cfg['sdtype']}
            
            # Fit synthesizer
            await self._update_job_status(job_id, JobStatus.RUNNING, "Fitting model...", progress=10)
            synthesizer.fit(source_data, metadata=metadata if metadata else None)
            
            # Generate synthetic data
            await self._update_job_status(job_id, JobStatus.RUNNING, "Generating synthetic data...", progress=50)
            result = synthesizer.sample(job.num_rows_requested)
            synthetic_df = result.synthetic_data
            
            # Evaluate quality
            await self._update_job_status(job_id, JobStatus.RUNNING, "Evaluating quality...", progress=80)
            quality_report = self.evaluator.evaluate(source_data, synthetic_df)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Store synthetic dataset
            dataset_id = uuid4()
            dataset_name = output_name or f"synthetic_{job.synthesizer_type}_{job_id.hex[:8]}"
            
            # Get column info
            columns_info = [
                {"name": col, "dtype": str(synthetic_df[col].dtype)}
                for col in synthetic_df.columns
            ]
            
            await self.session.execute(
                synthetic_datasets.insert().values(
                    id=dataset_id,
                    job_id=job_id,
                    name=dataset_name,
                    num_rows=len(synthetic_df),
                    num_columns=len(synthetic_df.columns),
                    columns=columns_info,
                )
            )
            
            # Store quality report
            report_id = uuid4()
            await self.session.execute(
                synthetic_quality_reports.insert().values(
                    id=report_id,
                    synthetic_dataset_id=dataset_id,
                    job_id=job_id,
                    overall_score=Decimal(str(quality_report.overall_score)),
                    statistical_fidelity_score=Decimal(str(quality_report.statistical_fidelity_score)),
                    correlation_score=Decimal(str(quality_report.correlation_score)),
                    column_scores=[
                        {
                            "column_name": cs.column_name,
                            "dtype": cs.dtype,
                            "ks_statistic": cs.ks_statistic,
                            "p_value": cs.p_value,
                            "score": cs.score,
                            "rating": cs.rating,
                        }
                        for cs in quality_report.column_scores
                    ],
                    correlation_metrics=quality_report.correlation_metrics,
                    recommendations=quality_report.recommendations,
                    warnings=quality_report.warnings,
                )
            )
            
            # Update job as completed
            await self.session.execute(
                update(synthetic_jobs)
                .where(synthetic_jobs.c.id == job_id)
                .values(
                    status=JobStatus.COMPLETED.value,
                    progress=100,
                    status_message="Synthesis completed successfully",
                    num_rows_generated=len(synthetic_df),
                    synthetic_dataset_id=dataset_id,
                    quality_report_id=report_id,
                    completed_at=datetime.utcnow(),
                    duration_seconds=Decimal(str(round(duration, 2))),
                )
            )
            await self.session.commit()
            
            logger.info(f"Job {job_id} completed: {len(synthetic_df)} rows in {duration:.2f}s, quality={quality_report.overall_score:.2f}")
            
            # Return the synthetic data (caller can save to storage)
            return dataset_id, synthetic_df
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self._update_job_status(
                job_id, 
                JobStatus.FAILED, 
                f"Synthesis failed: {str(e)}",
                error_message=str(e)
            )
            raise
    
    async def _update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        message: str,
        progress: int = None,
        error_message: str = None,
    ) -> None:
        """Update job status."""
        values = {
            "status": status.value,
            "status_message": message,
        }
        
        if progress is not None:
            values["progress"] = progress
        
        if status == JobStatus.RUNNING and progress == 10:
            values["started_at"] = datetime.utcnow()
        
        if error_message:
            values["error_message"] = error_message
        
        await self.session.execute(
            update(synthetic_jobs)
            .where(synthetic_jobs.c.id == job_id)
            .values(**values)
        )
        await self.session.commit()
    
    async def get_job_status(self, job_id: UUID) -> Optional[JobStatusResponse]:
        """Get job status."""
        result = await self.session.execute(
            select(synthetic_jobs).where(synthetic_jobs.c.id == job_id)
        )
        job = result.fetchone()
        
        if not job:
            return None
        
        # Get quality score if completed
        quality_score = None
        if job.quality_report_id:
            report_result = await self.session.execute(
                select(synthetic_quality_reports.c.overall_score)
                .where(synthetic_quality_reports.c.id == job.quality_report_id)
            )
            score_row = report_result.fetchone()
            if score_row:
                quality_score = float(score_row.overall_score)
        
        return JobStatusResponse(
            job_id=job.id,
            status=JobStatus(job.status),
            progress=job.progress or 0,
            status_message=job.status_message,
            source_type="dataset" if job.source_dataset_id else "table",
            synthesizer_type=job.synthesizer_type,
            num_rows_requested=job.num_rows_requested,
            synthetic_dataset_id=job.synthetic_dataset_id,
            num_rows_generated=job.num_rows_generated,
            quality_score=quality_score,
            started_at=job.started_at,
            completed_at=job.completed_at,
            duration_seconds=float(job.duration_seconds) if job.duration_seconds else None,
            error_message=job.error_message,
            created_at=job.created_at,
        )
    
    async def get_dataset(self, dataset_id: UUID) -> Optional[SyntheticDatasetResponse]:
        """Get synthetic dataset info."""
        result = await self.session.execute(
            select(synthetic_datasets).where(synthetic_datasets.c.id == dataset_id)
        )
        ds = result.fetchone()
        
        if not ds:
            return None
        
        # Get quality score
        quality_score = None
        report_result = await self.session.execute(
            select(synthetic_quality_reports.c.overall_score)
            .where(synthetic_quality_reports.c.synthetic_dataset_id == dataset_id)
        )
        score_row = report_result.fetchone()
        if score_row:
            quality_score = float(score_row.overall_score)
        
        return SyntheticDatasetResponse(
            id=ds.id,
            job_id=ds.job_id,
            name=ds.name,
            description=ds.description,
            storage_uri=ds.storage_uri,
            storage_format=ds.storage_format,
            num_rows=ds.num_rows,
            num_columns=ds.num_columns,
            file_size_bytes=ds.file_size_bytes,
            columns=ds.columns,
            quality_score=quality_score,
            created_at=ds.created_at,
        )
    
    async def get_quality_report(self, dataset_id: UUID) -> Optional[QualityReportResponse]:
        """Get quality report for a synthetic dataset."""
        result = await self.session.execute(
            select(synthetic_quality_reports)
            .where(synthetic_quality_reports.c.synthetic_dataset_id == dataset_id)
        )
        report = result.fetchone()
        
        if not report:
            return None
        
        return QualityReportResponse(
            report_id=report.id,
            synthetic_dataset_id=report.synthetic_dataset_id,
            job_id=report.job_id,
            overall_score=float(report.overall_score) if report.overall_score else 0,
            statistical_fidelity_score=float(report.statistical_fidelity_score) if report.statistical_fidelity_score else 0,
            correlation_score=float(report.correlation_score) if report.correlation_score else 0,
            column_scores=[
                QualityColumnScore(**cs) for cs in (report.column_scores or [])
            ],
            privacy_score=float(report.privacy_score) if report.privacy_score else None,
            privacy_metrics=report.privacy_metrics,
            recommendations=report.recommendations or [],
            warnings=report.warnings or [],
            created_at=report.created_at,
        )
    
    async def list_datasets(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[SyntheticDatasetResponse], int]:
        """List synthetic datasets."""
        from sqlalchemy import func
        
        # Get datasets
        result = await self.session.execute(
            select(synthetic_datasets)
            .order_by(synthetic_datasets.c.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.fetchall()
        
        # Get total count
        count_result = await self.session.execute(
            select(func.count(synthetic_datasets.c.id))
        )
        total = count_result.scalar() or 0
        
        datasets = []
        for ds in rows:
            # Get quality score for each
            quality_score = None
            report_result = await self.session.execute(
                select(synthetic_quality_reports.c.overall_score)
                .where(synthetic_quality_reports.c.synthetic_dataset_id == ds.id)
            )
            score_row = report_result.fetchone()
            if score_row:
                quality_score = float(score_row.overall_score)
            
            datasets.append(SyntheticDatasetResponse(
                id=ds.id,
                job_id=ds.job_id,
                name=ds.name,
                description=ds.description,
                storage_uri=ds.storage_uri,
                storage_format=ds.storage_format,
                num_rows=ds.num_rows,
                num_columns=ds.num_columns,
                file_size_bytes=ds.file_size_bytes,
                columns=ds.columns,
                quality_score=quality_score,
                created_at=ds.created_at,
            ))
        
        return datasets, total
    
    @classmethod
    def get_synthesizer_info(cls) -> List[Dict[str, Any]]:
        """Get information about available synthesizers."""
        return [
            cls.SYNTHESIZERS[SynthesizerType.GAUSSIAN_COPULA].get_info(),
            cls.SYNTHESIZERS[SynthesizerType.CTGAN].get_info(),
            cls.SYNTHESIZERS[SynthesizerType.TVAE].get_info(),
        ]
