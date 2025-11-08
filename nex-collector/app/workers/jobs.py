"""Background worker jobs."""
import os
from redis import Redis
from rq import Queue
from .worker import process_teacher_run, process_aggregate_job


redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
queue = Queue("nex_queue", connection=redis)


def enqueue_teacher_run_job(run_id: str):
    """Enqueue a teacher run job."""
    queue.enqueue(process_teacher_run, run_id, job_timeout="5m")


def enqueue_aggregate_job(job_id: str, payload: dict):
    """Enqueue an aggregation job."""
    queue.enqueue(process_aggregate_job, job_id, payload, job_timeout="10m")
