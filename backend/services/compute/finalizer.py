"""Background service to poll and finalize remote runs."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from .adapter import ComputeAdapter, JobState
from ..object_store import ObjectStoreClient, ObjectStorePaths

logger = logging.getLogger(__name__)


class RunFinalizer:
    """
    Background service to poll and finalize remote ML runs.
    
    Responsibilities:
    - Poll status of active runs with remote_job_id
    - Update run status in database
    - Fetch and store logs on completion
    - Read metrics from output manifest
    - Auto-create temporal DerivedAsset on success
    - Log interaction events
    """
    
    def __init__(
        self,
        compute_adapter: ComputeAdapter,
        object_store: ObjectStoreClient,
        async_session_factory
    ):
        """
        Initialize the finalizer.
        
        Args:
            compute_adapter: Adapter for checking job status
            object_store: Client for storing logs/reading outputs
            async_session_factory: Factory for async database sessions
        """
        self.compute = compute_adapter
        self.storage = object_store
        self.session_factory = async_session_factory
        self.poll_interval = settings.finalizer_poll_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background polling loop."""
        if self._running:
            logger.warning("Finalizer already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Run finalizer started (poll interval: {self.poll_interval}s)")
    
    async def stop(self):
        """Stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Run finalizer stopped")
    
    async def _poll_loop(self):
        """Main polling loop."""
        while self._running:
            try:
                await self._poll_active_runs()
            except Exception as e:
                logger.error(f"Finalizer poll error: {e}", exc_info=True)
            
            await asyncio.sleep(self.poll_interval)
    
    async def _poll_active_runs(self):
        """Check status of all active runs with remote jobs."""
        async with self.session_factory() as session:
            # Import here to avoid circular imports
            from db.models import ml_run
            
            # First, submit any queued runs that haven't been submitted yet
            await self._submit_queued_runs(session)
            
            # Then check runs that are already submitted
            stmt = select(ml_run).where(
                and_(
                    ml_run.c.status.in_(['queued', 'running', 'scheduled']),
                    ml_run.c.remote_job_id.isnot(None),
                    ml_run.c.compute_target != 'local'
                )
            )
            result = await session.execute(stmt)
            runs = result.fetchall()
            
            if runs:
                logger.debug(f"Checking {len(runs)} active runs")
            
            for run in runs:
                try:
                    await self._check_run(session, run)
                except Exception as e:
                    logger.error(f"Error checking run {run.id}: {e}", exc_info=True)
            
            await session.commit()
    
    async def _submit_queued_runs(self, session: AsyncSession):
        """Submit queued runs that haven't been submitted to remote compute yet."""
        from db.models import ml_run
        from .adapter import JobSubmission
        
        # Find queued runs without remote_job_id that need remote execution
        stmt = select(ml_run).where(
            and_(
                ml_run.c.status == 'queued',
                ml_run.c.remote_job_id.is_(None),
                ml_run.c.compute_target != 'local'
            )
        )
        result = await session.execute(stmt)
        queued_runs = result.fetchall()
        
        if not queued_runs:
            return
        
        logger.info(f"Submitting {len(queued_runs)} queued runs to remote compute")
        
        for run in queued_runs:
            try:
                # Build job submission
                recipe_name = run.recipe_id.replace('recipe_', '').replace('_base', '')
                params = dict(run.parameters) if run.parameters else {}
                
                job = JobSubmission(
                    run_id=run.id,
                    image=f"nex/{recipe_name}:v1",  # Convention: nex/forecasting:v1
                    command=["python", "run.py"],
                    env={
                        "RUN_ID": run.id,
                        "INPUT_URI": f"datasets/{run.recipe_id}/latest",
                        "OUTPUT_URI": f"runs/{run.id}",
                        "PARAMS_JSON": str(params),
                        "S3_ENDPOINT": settings.s3_endpoint or "http://minio:9000",
                        "S3_ACCESS_KEY": settings.s3_access_key or "minioadmin",
                        "S3_SECRET_KEY": settings.s3_secret_key or "minioadmin",
                        "S3_BUCKET": settings.s3_bucket or "nex-data"
                    },
                    input_uri=f"datasets/{run.recipe_id}/latest",
                    output_uri=f"runs/{run.id}",
                    timeout_seconds=3600
                )
                
                # Submit to compute adapter
                remote_job_id = await self.compute.submit(job)
                
                # Update run with remote job ID
                await session.execute(
                    ml_run.update().where(ml_run.c.id == run.id).values(
                        remote_job_id=remote_job_id,
                        status='scheduled'
                    )
                )
                
                logger.info(f"Submitted run {run.id} -> remote job {remote_job_id}")
                
                await self._log_interaction(
                    session, 'RUN_SUBMITTED',
                    refs={'run_id': run.id, 'remote_job_id': remote_job_id},
                    chat_session_id=run.chat_session_id
                )
                
            except Exception as e:
                logger.error(f"Failed to submit run {run.id}: {e}", exc_info=True)
                # Mark as failed
                await session.execute(
                    ml_run.update().where(ml_run.c.id == run.id).values(
                        status='failed',
                        failure_reason=str(e),
                        failure_type='infra'
                    )
                )
        
        await session.commit()
    
    async def _check_run(self, session: AsyncSession, run):
        """Check and update a single run."""
        from db.models import ml_run
        
        status = await self.compute.get_status(run.remote_job_id)
        logger.debug(f"Run {run.id} status: {status.state}")
        
        if status.state == JobState.RUNNING and run.status != 'running':
            # Update to running
            await session.execute(
                ml_run.update().where(ml_run.c.id == run.id).values(
                    status='running',
                    started_at=status.started_at or datetime.utcnow()
                )
            )
            await self._log_interaction(
                session, 'RUN_STARTED', 
                refs={'run_id': run.id},
                chat_session_id=run.chat_session_id
            )
        
        elif status.state == JobState.SUCCEEDED:
            await self._finalize_success(session, run)
        
        elif status.state == JobState.FAILED:
            await self._finalize_failure(session, run, status.reason)
        
        elif status.state == JobState.CANCELLED:
            await self._finalize_cancelled(session, run)
    
    async def _finalize_success(self, session: AsyncSession, run):
        """Finalize a successful run."""
        from db.models import ml_run, ml_derived_assets
        
        logger.info(f"Finalizing successful run {run.id}")
        
        # Fetch and store logs
        logs_uri = None
        try:
            logs = await self.compute.get_logs(run.remote_job_id)
            logs_key = ObjectStorePaths.run_logs(run.id)
            logs_uri = self.storage.put_text(logs_key, logs)
        except Exception as e:
            logger.warning(f"Failed to fetch logs for {run.id}: {e}")
        
        # Read metrics from output
        metrics = {}
        try:
            metrics_key = ObjectStorePaths.run_metrics(run.id)
            if self.storage.exists(metrics_key):
                metrics = self.storage.get_json(metrics_key)
        except Exception as e:
            logger.warning(f"Failed to read metrics for {run.id}: {e}")
        
        # Read manifest
        manifest_uri = None
        try:
            manifest_key = ObjectStorePaths.run_manifest(run.id)
            if self.storage.exists(manifest_key):
                manifest_uri = self.storage.get_uri(manifest_key)
        except Exception as e:
            logger.warning(f"Failed to read manifest for {run.id}: {e}")
        
        # Update run record
        await session.execute(
            ml_run.update().where(ml_run.c.id == run.id).values(
                status='succeeded',
                finished_at=datetime.utcnow(),
                logs_uri=logs_uri,
                output_manifest_uri=manifest_uri,
                metrics_json=metrics
            )
        )
        
        # Log completion event
        await self._log_interaction(
            session, 'RUN_COMPLETED',
            refs={'run_id': run.id},
            chat_session_id=run.chat_session_id,
            metadata={'metrics': metrics}
        )
        
        # Auto-create temporal derived asset
        await self._create_temporal_asset(session, run, metrics)
    
    async def _finalize_failure(self, session: AsyncSession, run, reason: Optional[str]):
        """Finalize a failed run."""
        from db.models import ml_run
        
        logger.info(f"Finalizing failed run {run.id}: {reason}")
        
        # Fetch logs
        logs_uri = None
        try:
            logs = await self.compute.get_logs(run.remote_job_id)
            logs_key = ObjectStorePaths.run_logs(run.id)
            logs_uri = self.storage.put_text(logs_key, logs)
        except Exception as e:
            logger.warning(f"Failed to fetch logs for {run.id}: {e}")
        
        # Update run record
        await session.execute(
            ml_run.update().where(ml_run.c.id == run.id).values(
                status='failed',
                finished_at=datetime.utcnow(),
                logs_uri=logs_uri,
                status_reason=reason or "Job failed"
            )
        )
        
        # Log failure event
        await self._log_interaction(
            session, 'RUN_FAILED',
            refs={'run_id': run.id},
            chat_session_id=run.chat_session_id,
            metadata={'reason': reason}
        )
    
    async def _finalize_cancelled(self, session: AsyncSession, run):
        """Finalize a cancelled run."""
        from db.models import ml_run
        
        logger.info(f"Finalizing cancelled run {run.id}")
        
        await session.execute(
            ml_run.update().where(ml_run.c.id == run.id).values(
                status='failed',
                finished_at=datetime.utcnow(),
                status_reason="Cancelled"
            )
        )
    
    async def _create_temporal_asset(self, session: AsyncSession, run, metrics: dict):
        """Auto-create a temporal derived asset from successful run."""
        from db.models import ml_derived_assets
        
        asset_id = str(uuid4())
        ttl_expires = datetime.utcnow() + timedelta(days=settings.derived_asset_ttl_days)
        
        # Create asset manifest
        asset_manifest = ObjectStorePaths.create_asset_manifest(
            asset_id=asset_id,
            source_run_id=run.id,
            asset_type='temporal',
            artifacts=[
                {'name': 'outputs', 'source': run.output_manifest_uri or f"runs/{run.id}/outputs"}
            ]
        )
        
        manifest_key = ObjectStorePaths.asset_manifest(asset_id)
        manifest_uri = self.storage.put_json(manifest_key, asset_manifest)
        storage_uri = self.storage.get_uri(ObjectStorePaths.asset_root(asset_id))
        
        # Insert asset record
        await session.execute(
            ml_derived_assets.insert().values(
                id=asset_id,
                source_run_id=run.id,
                name=f"Results from run {run.id[:8]}",
                asset_type='temporal',
                storage_uri=storage_uri,
                manifest_uri=manifest_uri,
                ttl_expires_at=ttl_expires,
                metrics_json=metrics,
                created_by=run.created_by,
                approval_state='draft'
            )
        )
        
        logger.info(f"Created temporal asset {asset_id} for run {run.id} (expires {ttl_expires})")
        
        # Log asset creation
        await self._log_interaction(
            session, 'ASSET_CREATED',
            refs={'run_id': run.id, 'asset_id': asset_id},
            chat_session_id=run.chat_session_id,
            metadata={'asset_type': 'temporal', 'ttl_days': settings.derived_asset_ttl_days}
        )
    
    async def _log_interaction(
        self, 
        session: AsyncSession, 
        event_type: str,
        refs: dict = None,
        chat_session_id: str = None,
        message: str = None,
        metadata: dict = None
    ):
        """Log an interaction event."""
        from db.models import interaction_logs
        
        await session.execute(
            interaction_logs.insert().values(
                id=str(uuid4()),
                chat_session_id=chat_session_id,
                actor='system',
                event_type=event_type,
                message=message,
                refs=refs or {},
                metadata=metadata or {}
            )
        )
