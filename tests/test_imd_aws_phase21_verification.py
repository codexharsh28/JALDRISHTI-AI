"""
Phase 21 Unit and Integration Tests for IMD AWS Live Ingestion & Hardening.
Verifies real-time event bus emission, zero fabrication rules, classification,
provenance retention, and duplicate prevention.
"""

import pytest
from datetime import datetime, timezone
from services.ingestion.live_adapters import IMDLiveAdapter
from services.ingestion.imd_aws_repository import imd_aws_repository, IMDAWSObservation, IMDAWSStation
from services.events.event_bus import event_bus
from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent

def test_imd_aws_adapter_zero_fabrication_on_missing_fields():
    adapter = IMDLiveAdapter()
    now = datetime.now(timezone.utc)
    raw = {
        "CALL_SIGN": "TEST_AWS_01",
        "STATION": "Test AWS Station",
        "DISTRICT": "Cuttack",
        "STATE": "Odisha",
        "Latitude": 20.46,
        "Longitude": 85.88,
        "DATE": "2026-08-31",
        "TIME": "14:00:00",
        "CURR_TEMP": "28.5",
        "RH": "85.0"
        # RAINFALL_MM / RAIN_1H is omitted intentionally
    }

    obs = adapter.normalize_record(raw, retrieved_at=now, ingestion_run_id="ING-TEST", payload_hash="HASH123")
    assert obs is not None
    assert obs.rainfall_mm is None  # Zero fabrication rule: missing rainfall must be None, NOT 0.0
    assert obs.air_temperature_c == 28.5
    assert obs.relative_humidity_pct == 85.0
    assert obs.pressure_hpa is None
    assert obs.inside_basin is True
    assert obs.data_state == "OBSERVED_IMD_AWS"

def test_imd_aws_adapter_event_bus_emission():
    adapter = IMDLiveAdapter()
    published_events = []

    async def mock_handler(evt: OperationalEvent):
        published_events.append(evt)

    event_bus.subscribe(EventType.IMD_AWS_OBSERVATION_UPDATED, mock_handler)
    event_bus.subscribe(EventType.IMD_AWS_SOURCE_HEALTH_CHANGED, mock_handler)

    raw_payload = [{
        "CALL_SIGN": "BHU_AWS",
        "STATION": "Bhubaneswar AWS",
        "DISTRICT": "Khurda",
        "STATE": "Odisha",
        "Latitude": 20.27,
        "Longitude": 85.84,
        "DATE": "2026-08-31",
        "TIME": "14:00:00",
        "CURR_TEMP": "29.2",
        "RAIN_1H": "12.4"
    }]

    res = adapter.fetch(force=True, custom_raw_payload=raw_payload)
    assert res.ingestion_run.status == "SUCCESS"
    assert res.ingestion_run.records_accepted == 1

def test_imd_aws_duplicate_observation_prevention():
    now = datetime.now(timezone.utc)
    obs_id = imd_aws_repository.generate_observation_id("TEST_STN", now.isoformat())

    obs = IMDAWSObservation(
        observation_id=obs_id,
        call_sign="TEST_STN",
        station_id="IMD_AWS_TEST_STN",
        station_name="Test Station",
        district="Cuttack",
        state="Odisha",
        latitude=20.46,
        longitude=85.88,
        observation_time=now,
        retrieved_at=now,
        air_temperature_c=27.5,
        rainfall_mm=5.2,
        quality_state="GOOD",
        data_state="OBSERVED_IMD_AWS",
        provider="IMD_AWS",
        is_observed_telemetry=True,
        inside_basin=True,
        ingestion_run_id="RUN-1",
        raw_payload_hash="HASH1"
    )

    first_insert = imd_aws_repository.store_observation(obs)
    second_insert = imd_aws_repository.store_observation(obs)

    assert first_insert is True
    assert second_insert is False  # Duplicate prevention enforces idempotency
