"""
Unit tests for IMD AWS Observation & Station Data Schemas.
"""

import pytest
from datetime import datetime, timezone
from services.ingestion.imd_aws_repository import IMDAWSStation, IMDAWSObservation

def test_imd_aws_station_schema_valid():
    stn = IMDAWSStation(
        call_sign="42971",
        station_id="IMD_AWS_42971",
        station_name="Bhubaneswar AWS",
        district="Khordha",
        state="Odisha",
        latitude=20.296,
        longitude=85.824,
        inside_basin=True,
        distance_to_basin_km=0.0,
        subbasin_id="sub-central-cuttack"
    )
    assert stn.call_sign == "42971"
    assert stn.inside_basin is True
    assert stn.status == "ACTIVE"

def test_imd_aws_observation_schema_valid():
    obs = IMDAWSObservation(
        observation_id="OBS-1234567890",
        call_sign="42971",
        station_id="IMD_AWS_42971",
        station_name="Bhubaneswar AWS",
        district="Khordha",
        state="Odisha",
        latitude=20.296,
        longitude=85.824,
        observation_time=datetime(2026, 8, 27, 10, 30, tzinfo=timezone.utc),
        air_temperature_c=28.4,
        dew_point_c=25.2,
        relative_humidity_pct=92.0,
        pressure_hpa=1004.5,
        wind_direction_deg=180.0,
        wind_speed_mps=3.5,
        rainfall_mm=None,  # Explicitly absent
        quality_state="GOOD",
        data_state="OBSERVED_IMD_AWS",
        provider="IMD_AWS",
        is_observed_telemetry=True,
        ingestion_run_id="ING-IMD-20260827-01",
        raw_payload_hash="sha256_mock_hash"
    )
    assert obs.data_state == "OBSERVED_IMD_AWS"
    assert obs.is_observed_telemetry is True
    assert obs.rainfall_mm is None
    assert obs.air_temperature_c == 28.4
