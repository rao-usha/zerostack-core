"""Run scheduler service for scheduled ML runs.

Provides:
- Cron-style scheduling
- APScheduler integration
- Timezone support
- Reuse engine integration
"""
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pytz
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings
from services.notifications import get_notification_service

logger = logging.getLogger(__name__)

# Try to import APScheduler, fall back to simple async scheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler not installed, using simple scheduler")


@dataclass
class ScheduleInfo:
    """Information about a schedule."""
    id: str
    name: str
    recipe_id: str
    dataset_id: Optional[str]
    cron_expression: str
    timezone: str
    is_active: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    last_run_id: Optional[str]
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'recipe_id': self.recipe_id,
            'dataset_id': self.dataset_id,
            'cron_expression': self.cron_expression,
            'timezone': self.timezone,
            'is_active': self.is_active,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_id': self.last_run_id
        }


class RunScheduler:
    """Service for scheduling ML runs."""
    
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
        self._scheduler = None
        self._is_running = False
        self._scheduled_jobs: Dict[str, str] = {}  # schedule_id -> job_id
    
    async def start(self):
        """Start the scheduler."""
        if self._is_running:
            return
        
        if HAS_APSCHEDULER:
            self._scheduler = AsyncIOScheduler(
                jobstores={'default': MemoryJobStore()},
                timezone=pytz.UTC
            )
            self._scheduler.start()
            logger.info("APScheduler started")
        
        # Load active schedules
        await self._load_schedules()
        self._is_running = True
        logger.info("Run scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        if self._scheduler and HAS_APSCHEDULER:
            self._scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("Run scheduler stopped")
    
    async def _load_schedules(self):
        """Load all active schedules and register them."""
        query = "SELECT * FROM run_schedules WHERE is_active = true"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            schedules = [dict(row._mapping) for row in result]
        
        for schedule in schedules:
            await self._register_schedule(schedule)
        
        logger.info(f"Loaded {len(schedules)} active schedules")
    
    async def _register_schedule(self, schedule: dict):
        """Register a schedule with the scheduler."""
        schedule_id = str(schedule['id'])
        cron_expr = schedule['cron_expression']
        timezone = schedule.get('timezone', 'UTC')
        
        if HAS_APSCHEDULER and self._scheduler:
            try:
                # Parse cron expression (minute hour day month day_of_week)
                parts = cron_expr.split()
                if len(parts) == 5:
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4],
                        timezone=pytz.timezone(timezone)
                    )
                    
                    job = self._scheduler.add_job(
                        self._execute_schedule,
                        trigger,
                        args=[schedule_id],
                        id=f"schedule_{schedule_id}",
                        replace_existing=True
                    )
                    
                    self._scheduled_jobs[schedule_id] = job.id
                    
                    # Update next_run_at
                    next_run = job.next_run_time
                    if next_run:
                        await self._update_next_run(schedule_id, next_run)
                    
                    logger.info(f"Registered schedule {schedule_id}: {schedule['name']}")
                else:
                    logger.error(f"Invalid cron expression for schedule {schedule_id}: {cron_expr}")
            except Exception as e:
                logger.error(f"Failed to register schedule {schedule_id}: {e}")
        else:
            # Simple scheduler - just calculate next run time
            next_run = self._calculate_next_run(cron_expr, timezone)
            if next_run:
                await self._update_next_run(schedule_id, next_run)
    
    async def _execute_schedule(self, schedule_id: str):
        """Execute a scheduled run."""
        logger.info(f"Executing schedule {schedule_id}")
        
        # Get schedule details
        query = "SELECT * FROM run_schedules WHERE id = :id"
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'id': schedule_id}).fetchone()
        
        if not result:
            logger.error(f"Schedule {schedule_id} not found")
            return
        
        schedule = dict(result._mapping)
        
        # Check reuse engine first (if enabled)
        if schedule.get('use_reuse_engine', True):
            from services.reuse_engine import get_reuse_engine, ReuseAction
            
            reuse_engine = get_reuse_engine()
            decision = reuse_engine.evaluate_reuse(
                recipe_id=schedule['recipe_id'],
                dataset_version_id=schedule.get('dataset_id'),
                parameters=schedule.get('parameters', {})
            )
            
            if decision.action == ReuseAction.REUSE_REQUIRED:
                logger.info(f"Schedule {schedule_id}: Reusing existing run {decision.best_match.run_id}")
                await self._record_reused_run(schedule_id, decision.best_match.run_id)
                return
        
        # Create new run
        run_id = await self._create_run(schedule)
        
        if run_id:
            await self._record_run(schedule_id, run_id)
            logger.info(f"Schedule {schedule_id}: Created run {run_id}")
            
            # Send notifications if configured
            if schedule.get('notify_on_success'):
                await self._send_notification(schedule, 'success', run_id)
        else:
            if schedule.get('notify_on_failure'):
                await self._send_notification(schedule, 'failure', None)
    
    async def _create_run(self, schedule: dict) -> Optional[str]:
        """Create a run from a schedule."""
        from uuid import uuid4
        
        run_id = f"run_{uuid4().hex[:12]}"
        
        query = """
            INSERT INTO ml_run (
                id, recipe_id, recipe_version_id, run_type, status, 
                created_at
            )
            VALUES (
                :id, :recipe_id, 'latest', 'scheduled', 'queued',
                NOW()
            )
            RETURNING id
        """
        
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(query), {
                    'id': run_id,
                    'recipe_id': schedule['recipe_id']
                })
                return str(result.fetchone()[0])
        except Exception as e:
            logger.error(f"Failed to create run: {e}")
            return None
    
    async def _record_run(self, schedule_id: str, run_id: str):
        """Record a run execution for a schedule."""
        query = """
            UPDATE run_schedules 
            SET last_run_id = :run_id, 
                last_run_at = NOW(),
                updated_at = NOW()
            WHERE id = :schedule_id
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'schedule_id': schedule_id,
                'run_id': run_id
            })
    
    async def _record_reused_run(self, schedule_id: str, reused_run_id: str):
        """Record that a schedule reused an existing run."""
        query = """
            UPDATE run_schedules 
            SET last_run_id = :run_id, 
                last_run_at = NOW(),
                updated_at = NOW()
            WHERE id = :schedule_id
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'schedule_id': schedule_id,
                'run_id': reused_run_id
            })
    
    async def _update_next_run(self, schedule_id: str, next_run: datetime):
        """Update the next_run_at for a schedule."""
        query = """
            UPDATE run_schedules 
            SET next_run_at = :next_run
            WHERE id = :schedule_id
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'schedule_id': schedule_id,
                'next_run': next_run
            })
    
    async def _send_notification(self, schedule: dict, status: str, run_id: Optional[str], error_message: str = None):
        """Send notifications for schedule execution."""
        # Check if notification is enabled for this status
        notify_on_success = schedule.get('notify_on_success', False)
        notify_on_failure = schedule.get('notify_on_failure', True)

        if status == 'success' and not notify_on_success:
            logger.debug(f"Skipping success notification for schedule {schedule['id']}")
            return
        if status == 'failure' and not notify_on_failure:
            logger.debug(f"Skipping failure notification for schedule {schedule['id']}")
            return

        channels = schedule.get('notification_channels', [])
        if not channels:
            logger.debug(f"No notification channels configured for schedule {schedule['id']}")
            return

        try:
            notification_service = get_notification_service()
            results = await notification_service.send_schedule_notification(
                schedule_name=schedule.get('name', 'Unknown Schedule'),
                status=status,
                run_id=run_id,
                error_message=error_message,
                channels=channels
            )

            success_count = sum(1 for r in results if r.success)
            logger.info(f"Sent {success_count}/{len(results)} notifications for schedule {schedule['id']}: {status}")

        except Exception as e:
            logger.error(f"Failed to send notifications for schedule {schedule['id']}: {e}")
    
    def _calculate_next_run(self, cron_expr: str, timezone: str = 'UTC') -> Optional[datetime]:
        """Calculate the next run time for a cron expression."""
        try:
            from croniter import croniter
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            cron = croniter(cron_expr, now)
            return cron.get_next(datetime)
        except ImportError:
            logger.warning("croniter not installed, cannot calculate next run time")
            return None
        except Exception as e:
            logger.error(f"Failed to calculate next run: {e}")
            return None
    
    # ========================================
    # Public API
    # ========================================
    
    async def create_schedule(
        self,
        name: str,
        recipe_id: str,
        cron_expression: str,
        dataset_id: str = None,
        parameters: dict = None,
        timezone: str = 'UTC',
        use_reuse_engine: bool = True,
        notify_on_failure: bool = True,
        notify_on_success: bool = False,
        notification_channels: List[str] = None
    ) -> str:
        """Create a new schedule."""
        query = """
            INSERT INTO run_schedules (
                name, recipe_id, dataset_id, parameters, cron_expression,
                timezone, use_reuse_engine, notify_on_failure, notify_on_success,
                notification_channels
            )
            VALUES (
                :name, :recipe_id, :dataset_id, :parameters, :cron,
                :timezone, :use_reuse, :notify_fail, :notify_success,
                :channels
            )
            RETURNING id
        """
        
        import json
        
        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'name': name,
                'recipe_id': recipe_id,
                'dataset_id': dataset_id,
                'parameters': json.dumps(parameters or {}),
                'cron': cron_expression,
                'timezone': timezone,
                'use_reuse': use_reuse_engine,
                'notify_fail': notify_on_failure,
                'notify_success': notify_on_success,
                'channels': json.dumps(notification_channels or [])
            })
            schedule_id = str(result.fetchone()[0])
        
        # Register with scheduler
        schedule = {
            'id': schedule_id,
            'name': name,
            'recipe_id': recipe_id,
            'cron_expression': cron_expression,
            'timezone': timezone
        }
        await self._register_schedule(schedule)
        
        logger.info(f"Created schedule {schedule_id}: {name}")
        return schedule_id
    
    async def pause_schedule(self, schedule_id: str):
        """Pause a schedule."""
        query = "UPDATE run_schedules SET is_active = false WHERE id = :id"
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {'id': schedule_id})
        
        # Remove from scheduler
        if schedule_id in self._scheduled_jobs and self._scheduler:
            self._scheduler.remove_job(self._scheduled_jobs[schedule_id])
            del self._scheduled_jobs[schedule_id]
        
        logger.info(f"Paused schedule {schedule_id}")
    
    async def resume_schedule(self, schedule_id: str):
        """Resume a paused schedule."""
        query = "UPDATE run_schedules SET is_active = true WHERE id = :id RETURNING *"
        
        with self.engine.begin() as conn:
            result = conn.execute(text(query), {'id': schedule_id}).fetchone()
        
        if result:
            await self._register_schedule(dict(result._mapping))
            logger.info(f"Resumed schedule {schedule_id}")
    
    async def trigger_now(self, schedule_id: str) -> Optional[str]:
        """Manually trigger a schedule now."""
        logger.info(f"Manually triggering schedule {schedule_id}")
        await self._execute_schedule(schedule_id)
        
        # Return the last run ID
        query = "SELECT last_run_id FROM run_schedules WHERE id = :id"
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'id': schedule_id}).fetchone()
            return result[0] if result else None
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduleInfo]:
        """Get schedule information."""
        query = "SELECT * FROM run_schedules WHERE id = :id"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'id': schedule_id}).fetchone()
        
        if not result:
            return None
        
        s = dict(result._mapping)
        return ScheduleInfo(
            id=str(s['id']),
            name=s['name'],
            recipe_id=s['recipe_id'],
            dataset_id=s.get('dataset_id'),
            cron_expression=s['cron_expression'],
            timezone=s.get('timezone', 'UTC'),
            is_active=s['is_active'],
            next_run_at=s.get('next_run_at'),
            last_run_at=s.get('last_run_at'),
            last_run_id=s.get('last_run_id')
        )
    
    def list_schedules(self, is_active: bool = None) -> List[ScheduleInfo]:
        """List all schedules."""
        query = "SELECT * FROM run_schedules"
        params = {}
        
        if is_active is not None:
            query += " WHERE is_active = :is_active"
            params['is_active'] = is_active
        
        query += " ORDER BY created_at DESC"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            schedules = []
            for row in result:
                s = dict(row._mapping)
                schedules.append(ScheduleInfo(
                    id=str(s['id']),
                    name=s['name'],
                    recipe_id=s['recipe_id'],
                    dataset_id=s.get('dataset_id'),
                    cron_expression=s['cron_expression'],
                    timezone=s.get('timezone', 'UTC'),
                    is_active=s['is_active'],
                    next_run_at=s.get('next_run_at'),
                    last_run_at=s.get('last_run_at'),
                    last_run_id=s.get('last_run_id')
                ))
        
        return schedules


# Singleton instance
_scheduler_instance: Optional[RunScheduler] = None


def get_scheduler() -> RunScheduler:
    """Get singleton scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = RunScheduler()
    return _scheduler_instance
