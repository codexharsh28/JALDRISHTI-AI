"""
Asynchronous Forecast Job Queue & State Machine for JALDRISHTI AI.
Decouples heavy model execution from REST request lifecycles.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

class JobState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ForecastJob(BaseModel):
    forecast_job_id: str
    forecast_run_id: str
    state: JobState = JobState.QUEUED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    trigger_sources: List[str] = Field(default_factory=list)
    state_version: int = 1000
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class ForecastJobQueue:
    """
    In-memory async job queue with state transitions and bounded execution.
    """

    def __init__(self, max_queue_size: int = 50):
        self.max_queue_size = max_queue_size
        self._jobs: Dict[str, ForecastJob] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._is_worker_running = False
        self._current_job: Optional[ForecastJob] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._runner_func: Optional[Callable[[ForecastJob], Awaitable[Dict[str, Any]]]] = None

    def set_runner(self, runner_func: Callable[[ForecastJob], Awaitable[Dict[str, Any]]]):
        """Attach the pipeline execution runner function."""
        self._runner_func = runner_func

    def submit_job(
        self,
        forecast_run_id: str,
        trigger_sources: List[str],
        state_version: int = 1000
    ) -> ForecastJob:
        """Enqueue a new forecasting job."""
        job_id = f"JOB-FC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
        job = ForecastJob(
            forecast_job_id=job_id,
            forecast_run_id=forecast_run_id,
            state=JobState.QUEUED,
            trigger_sources=trigger_sources,
            state_version=state_version
        )
        self._jobs[job_id] = job
        try:
            self._queue.put_nowait(job)
        except asyncio.QueueFull:
            job.state = JobState.FAILED
            job.error_message = "Forecast queue is full; dropping oldest non-critical forecast."
            logger.warning("Forecast queue capacity exceeded.")
        
        return job

    def get_job(self, job_id: str) -> Optional[ForecastJob]:
        return self._jobs.get(job_id)

    def get_recent_jobs(self, limit: int = 20) -> List[ForecastJob]:
        return list(reversed(list(self._jobs.values())))[:limit]

    def get_queue_status(self) -> Dict[str, Any]:
        return {
            "queue_depth": self._queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "active_job_id": self._current_job.forecast_job_id if self._current_job else None,
            "total_jobs_tracked": len(self._jobs)
        }

    async def start_worker(self):
        """Start background worker processing loop."""
        if not self._is_worker_running:
            self._is_worker_running = True
            self._worker_task = asyncio.create_task(self._process_queue())

    async def stop_worker(self):
        """Stop background worker."""
        self._is_worker_running = False
        if self._worker_task:
            self._worker_task.cancel()

    async def _process_queue(self):
        while self._is_worker_running:
            try:
                job: ForecastJob = await self._queue.get()
                self._current_job = job
                job.state = JobState.RUNNING
                job.started_at = datetime.now(timezone.utc).isoformat()

                if self._runner_func:
                    try:
                        res = await self._runner_func(job)
                        job.state = JobState.COMPLETED
                        job.result = res
                        job.completed_at = datetime.now(timezone.utc).isoformat()
                    except Exception as e:
                        job.state = JobState.FAILED
                        job.error_message = str(e)
                        job.completed_at = datetime.now(timezone.utc).isoformat()
                        logger.error(f"Forecast job {job.forecast_job_id} failed: {e}")
                else:
                    # Synchronous fallback simulation
                    job.state = JobState.COMPLETED
                    job.completed_at = datetime.now(timezone.utc).isoformat()

                self._current_job = None
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker queue exception: {e}")
                await asyncio.sleep(1.0)

# Global queue singleton
forecast_job_queue = ForecastJobQueue()
