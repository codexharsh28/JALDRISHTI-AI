"""
Unit tests for IMD AWS Payload Normalization.
Tests field extraction, unit conversions, wind direction cardinal parsing, and rainfall non-fabrication.
"""

import pytest
from datetime import datetime, timezone
from services.ingestion.live_adapters import IMDLiveAdapter

def test_normalization_complete_payload():
    adapter = IMDLiveAdapter()
    raw = {
        "CALL_SIGN": "42970",
        "STATION": "CUTTACK",
        "DISTRICT": "Cuttack",
        "STATE": "Odisha",
        "DATE": "2026-08-27",
        "TIME": "11:30:00",
        "CURR_TEMP": "27.5",
        "DEW_POINT_TEMP": "24.8",
        "RH": "88.0",
        "MSLP": "1005.2",
        "WIND_DIRECTION": "SW",
        "WIND_SPEED": "4.2",
        "MIN_TEMP": "25.0",
        "MAX_TEMP": "31.5",
        "Latitude": "20.462",
        "Longitude": "85.882",
        "WEATHER_CODE": "RA",
        "NEBULOSITY": "7.0",
        "Feel Like": "32.0",
        "RAIN_1H": "14.5"
    }

    obs = adapter.normalize_record(
        raw=raw,
        retrieved_at=datetime.now(timezone.utc),
        ingestion_run_id="ING-RUN-01",
        payload_hash="HASH01"
    )

    assert obs is not None
    assert obs.call_sign == "42970"
    assert obs.station_name == "CUTTACK"
    assert obs.air_temperature_c == 27.5
    assert obs.wind_direction_deg == 225.0  # SW mapped to 225 deg
    assert obs.rainfall_mm == 14.5
    assert obs.inside_basin is True

def test_normalization_absent_rainfall_never_fabricated():
    adapter = IMDLiveAdapter()
    raw_no_rain = {
        "CALL_SIGN": "42972",
        "STATION": "PARADIP",
        "DATE": "2026-08-27",
        "TIME": "11:30:00",
        "CURR_TEMP": "29.0",
        "Latitude": "20.264",
        "Longitude": "86.671"
    }

    obs = adapter.normalize_record(
        raw=raw_no_rain,
        retrieved_at=datetime.now(timezone.utc),
        ingestion_run_id="ING-RUN-02",
        payload_hash="HASH02"
    )

    assert obs is not None
    # Crucial scientific check: rainfall must be None, NOT 0.0 or synthetic value
    assert obs.rainfall_mm is None

def test_normalization_invalid_coordinates_rejected():
    adapter = IMDLiveAdapter()
    raw_invalid = {
        "CALL_SIGN": "99999",
        "STATION": "INVALID_STN",
        "Latitude": "999.0",  # Invalid latitude
        "Longitude": "85.88"
    }

    obs = adapter.normalize_record(
        raw=raw_invalid,
        retrieved_at=datetime.now(timezone.utc),
        ingestion_run_id="ING-RUN-03",
        payload_hash="HASH03"
    )
    assert obs is None
