"""
Event Dispatcher & Central Routing Gateway for JALDRISHTI AI.
Bridges domain services, forecasting engines, and WebSocket clients through standard event publication.
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timezone
import logging

from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent, generate_event_id
from services.events.event_bus import event_bus

logger = logging.getLogger(__name__)

class EventDispatcher:
    """
    Convenience facade for emitting typed domain events across JALDRISHTI AI.
    """

    def __init__(self, bus=event_bus):
        self.bus = bus
        self._ws_broadcaster: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None

    def set_websocket_broadcaster(self, broadcaster: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Attach the WebSocket broadcasting hook."""
        self._ws_broadcaster = broadcaster
        self.bus.subscribe_all(self._on_event_for_websocket)

    async def _on_event_for_websocket(self, event: OperationalEvent):
        """Format and transmit operational event over WebSocket."""
        if self._ws_broadcaster:
            payload = {
                "type": event.event_type.value,
                "event_id": event.event_id,
                "event_version": event.event_version,
                "timestamp": event.created_at,
                "occurred_at": event.occurred_at,
                "state_version": event.state_version,
                "mode": event.mode,
                "data_state": event.data_state,
                "source_id": event.source_id,
                "provider": event.provider,
                "run_id": event.forecast_run_id or event.ingestion_run_id,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "priority": event.priority.value,
                "payload_ref": event.payload_ref,
                "payload": event.data
            }
            try:
                await self._ws_broadcaster(payload)
            except Exception as e:
                logger.error(f"Failed to broadcast event {event.event_id} over WebSocket: {e}")

    async def publish_source_received(
        self,
        source_id: str,
        provider: str,
        observations: Any,
        ingestion_run_id: str,
        data_state: str = "LIVE",
        mode: str = "LIVE",
        correlation_id: Optional[str] = None
    ) -> OperationalEvent:
        event = OperationalEvent.create(
            event_type=EventType.SOURCE_DATA_RECEIVED,
            source_id=source_id,
            provider=provider,
            data={"records_count": len(observations) if isinstance(observations, list) else 1, "ingestion_run_id": ingestion_run_id},
            ingestion_run_id=ingestion_run_id,
            mode=mode,
            data_state=data_state,
            correlation_id=correlation_id,
            priority=EventPriority.NORMAL
        )
        await self.bus.publish(event)
        return event

    async def publish_forecast_completed(
        self,
        forecast_run_id: str,
        models_executed: list,
        source_snapshot_hash: str,
        state_version: int,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> OperationalEvent:
        event = OperationalEvent.create(
            event_type=EventType.FORECAST_COMPLETED,
            source_id="FORECAST_COALESCER",
            provider="JALDRISHTI Forecasting Core",
            data={
                "forecast_run_id": forecast_run_id,
                "models_executed": models_executed,
                "source_snapshot_hash": source_snapshot_hash
            },
            forecast_run_id=forecast_run_id,
            state_version=state_version,
            correlation_id=correlation_id,
            causation_id=causation_id,
            priority=EventPriority.HIGH
        )
        await self.bus.publish(event)
        return event

    async def publish_hydrology_updated(
        self,
        station_id: str,
        stage_m: float,
        discharge_cumec: float,
        forecast_run_id: str,
        input_source: str,
        state_version: int,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> OperationalEvent:
        event = OperationalEvent.create(
            event_type=EventType.HYDROLOGY_UPDATED,
            source_id=f"HYDRO_{station_id}",
            provider="XGBoost Quantile Streamflow Model",
            data={
                "station_id": station_id,
                "predicted_stage_m": stage_m,
                "predicted_discharge_cumec": discharge_cumec,
                "input_hydrology_source": input_source
            },
            forecast_run_id=forecast_run_id,
            state_version=state_version,
            station_id=station_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            priority=EventPriority.HIGH
        )
        await self.bus.publish(event)
        return event

    async def publish_inundation_updated(
        self,
        inundated_area_sqkm: float,
        flood_prob_mean: float,
        forecast_run_id: str,
        inundation_run_id: str,
        state_version: int,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> OperationalEvent:
        event = OperationalEvent.create(
            event_type=EventType.INUNDATION_UPDATED,
            source_id="INUNDATION_SURROGATE",
            provider="Spatial Hydraulic Surrogate",
            data={
                "inundated_area_sqkm": inundated_area_sqkm,
                "flood_prob_mean": flood_prob_mean
            },
            forecast_run_id=forecast_run_id,
            inundation_run_id=inundation_run_id,
            state_version=state_version,
            correlation_id=correlation_id,
            causation_id=causation_id,
            priority=EventPriority.HIGH
        )
        await self.bus.publish(event)
        return event

    async def publish_alert_state_changed(
        self,
        alert_id: str,
        severity: str,
        requires_human_review: bool,
        location_name: str,
        forecast_run_id: str,
        state_version: int,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> OperationalEvent:
        event_type = EventType.HUMAN_REVIEW_REQUIRED if requires_human_review else EventType.ALERT_STATE_CHANGED
        priority = EventPriority.CRITICAL if severity in ["RED", "DANGER"] or requires_human_review else EventPriority.HIGH
        
        event = OperationalEvent.create(
            event_type=event_type,
            source_id="ALERT_SAFETY_GATE",
            provider="JALDRISHTI Early Warning Engine",
            data={
                "alert_id": alert_id,
                "severity": severity,
                "requires_human_review": requires_human_review,
                "location_name": location_name
            },
            forecast_run_id=forecast_run_id,
            state_version=state_version,
            severity=severity,
            correlation_id=correlation_id,
            causation_id=causation_id,
            priority=priority
        )
        await self.bus.publish(event)
        return event

# Global dispatcher singleton
event_dispatcher = EventDispatcher()
