"""
Coalesced Forecast Trigger Engine for JALDRISHTI AI.
Aggregates incoming multi-source observation events across a debounce window
and enqueues single, non-overlapping forecast execution runs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncio
import logging
import uuid

from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent
from services.events.event_bus import event_bus
from services.forecasting.job_queue import forecast_job_queue, ForecastJob
from services.forecasting.runner import run_forecast_pipeline

logger = logging.getLogger(__name__)

class ForecastTriggerEngine:
    """
    Coalesces rapid observation arrivals into debounced forecast execution runs.
    """

    def __init__(
        self,
        debounce_seconds: float = 2.0,
        min_interval_seconds: float = 5.0
    ):
        self.debounce_seconds = debounce_seconds
        self.min_interval_seconds = min_interval_seconds
        
        self._pending_sources: List[str] = []
        self._debounce_task: Optional[asyncio.Task] = None
        self._last_trigger_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        
        # Attach runner to queue
        forecast_job_queue.set_runner(run_forecast_pipeline)

    def initialize(self):
        """Subscribe to incoming source observation events."""
        event_bus.subscribe(EventType.SOURCE_DATA_RECEIVED, self._on_source_data_received)

    async def _on_source_data_received(self, event: OperationalEvent):
        """Debounce incoming source update."""
        async with self._lock:
            self._pending_sources.append(event.source_id)
            if self._debounce_task and not self._debounce_task.done():
                self._debounce_task.cancel()
            self._debounce_task = asyncio.create_task(self._debounce_window())

    async def _debounce_window(self):
        """Wait for debounce quiet period then trigger coalesced forecast."""
        try:
            await asyncio.sleep(self.debounce_seconds)
            await self.trigger_coalesced_run()
        except asyncio.CancelledError:
            pass

    async def trigger_coalesced_run(self, force: bool = False) -> Optional[ForecastJob]:
        """Submit a single coalesced forecast job."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            if not force and self._last_trigger_time:
                elapsed = (now - self._last_trigger_time).total_seconds()
                if elapsed < self.min_interval_seconds:
                    logger.info(f"Trigger throttled: {elapsed:.2f}s < min {self.min_interval_seconds}s")
                    return None

            sources = list(set(self._pending_sources))
            self._pending_sources = []
            self._last_trigger_time = now

            run_id = f"FR-LIVE-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

            # Emit FORECAST_TRIGGERED event
            trigger_ev = OperationalEvent.create(
                event_type=EventType.FORECAST_TRIGGERED,
                source_id="FORECAST_TRIGGER_ENGINE",
                provider="Coalesced Forecast Trigger",
                data={"trigger_sources": sources, "coalesced_count": len(sources)},
                forecast_run_id=run_id,
                priority=EventPriority.HIGH
            )
            await event_bus.publish(trigger_ev)

            # Submit job to async execution queue
            job = forecast_job_queue.submit_job(
                forecast_run_id=run_id,
                trigger_sources=sources
            )
            return job

# Global trigger engine singleton
forecast_trigger_engine = ForecastTriggerEngine()
