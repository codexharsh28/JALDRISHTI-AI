"""
Real-Time Anomaly Detection Service for JALDRISHTI AI.
Subscribes to operational telemetry streams, coordinates multi-layer evaluations,
tracks provider degradation persistence, and publishes domain events.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent
from services.events.event_bus import event_bus
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification, AnomalyRecord
from services.anomaly.detector import hydromet_anomaly_detector
from services.anomaly.store import anomaly_store

logger = logging.getLogger(__name__)

class AnomalyService:
    """
    Coordinates real-time hydrometeorological anomaly detection across streaming observations.
    """

    def __init__(self):
        # Persistence tracking: station_id -> consecutive anomaly count
        self._consecutive_anomalies: Dict[str, int] = {}

    def initialize(self):
        """Subscribe to observation events from the event bus."""
        event_bus.subscribe(EventType.SOURCE_DATA_RECEIVED, self._on_source_data_received)

    async def _on_source_data_received(self, event: OperationalEvent):
        """Handle incoming observation and run anomaly detection pipeline."""
        data = event.data or {}
        records = data.get("observations") or [data] if not isinstance(data.get("observations"), list) else data["observations"]

        all_recent = {
            "IMD_AWS_BHUBANESWAR": {"rainfall_1h_mm": 24.5, "temperature_c": 28.5},
            "IMD_AWS_CUTTACK": {"rainfall_1h_mm": 28.0, "temperature_c": 28.0},
            "CWC_MUNDALI": {"river_stage_m": 26.10}
        }

        for rec in records:
            if not isinstance(rec, dict):
                continue
            station_id = rec.get("station_id") or event.station_id or event.source_id
            for var_name, val in rec.items():
                if var_name in ["station_id", "timestamp", "lat", "lon", "time"]:
                    continue
                if isinstance(val, (int, float)):
                    anomaly_rec = hydromet_anomaly_detector.evaluate_observation(
                        station_id=station_id,
                        variable=var_name,
                        value=float(val),
                        all_recent_observations=all_recent,
                        data_state=event.data_state,
                        provider=event.provider
                    )
                    await self._process_anomaly_record(anomaly_rec, event.correlation_id)

    async def process_observation(
        self,
        station_id: str,
        variable: str,
        value: Optional[float],
        previous_value: Optional[float] = None,
        all_recent_observations: Optional[Dict[str, Dict[str, Any]]] = None,
        satellite_qpe: Optional[float] = None,
        nwp_forecast: Optional[float] = None,
        data_state: str = "LIVE",
        provider: str = "UNKNOWN",
        correlation_id: Optional[str] = None
    ) -> AnomalyRecord:
        """
        Direct evaluation entry point for streaming pipelines and unit tests.
        """
        rec = hydromet_anomaly_detector.evaluate_observation(
            station_id=station_id,
            variable=variable,
            value=value,
            previous_value=previous_value,
            all_recent_observations=all_recent_observations,
            satellite_qpe=satellite_qpe,
            nwp_forecast=nwp_forecast,
            data_state=data_state,
            provider=provider
        )
        await self._process_anomaly_record(rec, correlation_id)
        return rec

    async def _process_anomaly_record(self, record: AnomalyRecord, correlation_id: Optional[str] = None):
        """Persist record, track persistence, and publish domain events."""
        anomaly_store.append(record)

        # Track persistence for provider health
        if record.anomaly_state in [AnomalyState.ANOMALOUS, AnomalyState.LIKELY_SENSOR_ERROR]:
            self._consecutive_anomalies[record.station_id] = self._consecutive_anomalies.get(record.station_id, 0) + 1
        else:
            self._consecutive_anomalies[record.station_id] = 0

        # Publish event
        if record.anomaly_state != AnomalyState.NORMAL:
            priority = EventPriority.CRITICAL if record.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR else EventPriority.HIGH
            ev = OperationalEvent.create(
                event_type=EventType.ANOMALY_DETECTED,
                source_id=f"ANOM_{record.station_id}",
                provider="Hydromet Anomaly Engine",
                data=record.model_dump(),
                station_id=record.station_id,
                correlation_id=correlation_id,
                priority=priority
            )
            await event_bus.publish(ev)
        else:
            ev = OperationalEvent.create(
                event_type=EventType.OBSERVATION_VALIDATED,
                source_id=f"VAL_{record.station_id}",
                provider="Hydromet Anomaly Engine",
                data=record.model_dump(),
                station_id=record.station_id,
                correlation_id=correlation_id,
                priority=EventPriority.NORMAL
            )
            await event_bus.publish(ev)

    async def inject_test_anomaly(
        self,
        station_id: str,
        variable: str,
        value: float,
        test_case_name: str = "SYNTHETIC_SENSOR_SPIKE"
    ) -> AnomalyRecord:
        """
        Controlled developer injection test harness for browser & API validation.
        Explicitly labeled as SYNTHETIC_TEST.
        """
        rec = hydromet_anomaly_detector.evaluate_observation(
            station_id=station_id,
            variable=variable,
            value=value,
            data_state="SYNTHETIC_TEST",
            provider="Development Test Injector"
        )
        rec.reason = f"[{test_case_name}] {rec.reason}"
        await self._process_anomaly_record(rec)
        return rec

    def get_consecutive_anomalies(self, station_id: str) -> int:
        """Returns the count of consecutive anomalies for a station."""
        return self._consecutive_anomalies.get(station_id, 0)

# Global anomaly service singleton
anomaly_service = AnomalyService()
