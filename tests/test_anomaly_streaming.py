"""
Unit tests for Real-Time Streaming Ingestion, Event Bus Lifecycle & Anomaly Persistence.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from services.events.event_types import EventType
from services.events.event_schema import OperationalEvent
from services.events.event_bus import event_bus
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification
from services.anomaly.service import AnomalyService, anomaly_service
from services.anomaly.store import anomaly_store

def test_streaming_observation_lifecycle():
    async def _test():
        anomaly_service.initialize()

        # Process normal observation
        rec_normal = await anomaly_service.process_observation(
            station_id="IMD_AWS_BHUBANESWAR",
            variable="rainfall_1h_mm",
            value=15.0
        )
        assert rec_normal.anomaly_state == AnomalyState.NORMAL

        # Process out-of-bounds observation
        rec_out = await anomaly_service.process_observation(
            station_id="IMD_AWS_CUTTACK",
            variable="rainfall_1h_mm",
            value=-20.0
        )
        assert rec_out.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
        assert rec_out.classification == AnomalyClassification.OUT_OF_BOUNDS

        # Check persistence count
        assert anomaly_service.get_consecutive_anomalies("IMD_AWS_CUTTACK") >= 1

    asyncio.run(_test())

def test_event_bus_subscription_trigger():
    async def _test():
        published_events = []
        
        async def capture_event(ev: OperationalEvent):
            published_events.append(ev)

        event_bus.subscribe(EventType.ANOMALY_DETECTED, capture_event)
        event_bus.subscribe(EventType.OBSERVATION_VALIDATED, capture_event)

        # Ingest synthetic spike
        rec = await anomaly_service.inject_test_anomaly(
            station_id="IMD_AWS_BHUBANESWAR",
            variable="rainfall_1h_mm",
            value=280.0,
            test_case_name="SYNTHETIC_TEST_SPIKE"
        )
        
        # Yield control to let async event bus handlers complete
        await asyncio.sleep(0.05)

        assert rec.data_state == "SYNTHETIC_TEST"
        assert len(published_events) >= 1
        assert any(e.event_type == EventType.ANOMALY_DETECTED for e in published_events)

    asyncio.run(_test())

def test_store_query_and_summary():
    async def _test():
        anomaly_store.clear()

        rec1 = await anomaly_service.process_observation("STN_A", "rainfall_1h_mm", 10.0)
        rec2 = await anomaly_service.process_observation("STN_B", "rainfall_1h_mm", -5.0)

        summary = anomaly_store.get_summary()
        assert summary["total_recent_anomalies"] >= 2
        assert summary["counts_by_state"]["NORMAL"] >= 1
        assert summary["counts_by_state"]["LIKELY_SENSOR_ERROR"] >= 1

    asyncio.run(_test())
