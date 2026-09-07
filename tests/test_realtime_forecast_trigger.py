"""
Unit tests for Coalesced Forecast Trigger Engine & Work Queue.
"""

import pytest
import asyncio
from services.forecasting.trigger_engine import ForecastTriggerEngine
from services.forecasting.job_queue import ForecastJobQueue, JobState

@pytest.mark.anyio
async def test_forecast_trigger_coalescing_and_debouncing():
    """Verifies that multiple incoming source updates coalesce into a single job."""
    engine = ForecastTriggerEngine(debounce_seconds=0.1, min_interval_seconds=0.2)
    
    job1 = await engine.trigger_coalesced_run(force=True)
    assert job1 is not None
    assert job1.state == JobState.QUEUED
    assert "FR-LIVE" in job1.forecast_run_id

    # Immediate second call without force should be throttled
    job2 = await engine.trigger_coalesced_run(force=False)
    assert job2 is None

@pytest.mark.anyio
async def test_forecast_job_queue_execution():
    """Verifies background queue execution state transitions."""
    queue = ForecastJobQueue()

    async def mock_runner(job):
        await asyncio.sleep(0.05)
        return {"metrics": "ok"}

    queue.set_runner(mock_runner)
    await queue.start_worker()

    job = queue.submit_job(forecast_run_id="RUN-Q-TEST", trigger_sources=["IMD_AWS"])
    assert job.state in [JobState.QUEUED, JobState.RUNNING]

    await asyncio.sleep(0.15)
    assert job.state == JobState.COMPLETED
    assert job.completed_at is not None

    await queue.stop_worker()
