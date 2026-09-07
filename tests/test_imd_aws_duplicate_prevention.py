"""
Unit tests for duplicate prevention and deterministic observation identity.
"""

import pytest
import uuid
from datetime import datetime, timezone
from services.ingestion.imd_aws_repository import imd_aws_repository, IMDAWSObservation

def test_duplicate_observation_rejected():
    test_id = uuid.uuid4().hex[:8]
    obs_time = datetime.now(timezone.utc)
    obs_id = f"OBS-TEST-{test_id}"

    obs = IMDAWSObservation(
        observation_id=obs_id,
        call_sign=f"TST_{test_id[:4]}",
        station_id=f"IMD_AWS_TST_{test_id[:4]}",
        station_name="Test AWS",
        district="Khordha",
        state="Odisha",
        latitude=20.296,
        longitude=85.824,
        observation_time=obs_time,
        retrieved_at=datetime.now(timezone.utc),
        air_temperature_c=28.4,
        dew_point_c=25.2,
        relative_humidity_pct=92.0,
        pressure_hpa=1004.5,
        wind_direction_deg=180.0,
        wind_speed_mps=3.5,
        rainfall_mm=12.0,
        quality_state="GOOD",
        data_state="OBSERVED_IMD_AWS",
        provider="IMD_AWS",
        is_observed_telemetry=True,
        ingestion_run_id=f"ING-RUN-{test_id}",
        raw_payload_hash=f"HASH-{test_id}"
    )

    # First insert -> True (new)
    first_res = imd_aws_repository.store_observation(obs)
    assert first_res is True

    # Second insert with identical ID -> False (ignored, duplicate prevented)
    second_res = imd_aws_repository.store_observation(obs)
    assert second_res is False
