"""
Unit tests for Quality Control (QC) integration on IMD AWS observations.
"""

import pytest
from datetime import datetime, timezone
from services.ingestion.live_adapters import IMDLiveAdapter

def test_qc_flags_physical_limits():
    adapter = IMDLiveAdapter()
    now = datetime.now(timezone.utc)

    # Valid observation with rainfall
    valid_raw = {
        "CALL_SIGN": "42971",
        "STATION": "BHUBANESWAR",
        "Latitude": "20.296",
        "Longitude": "85.824",
        "DATE": now.strftime("%Y-%m-%d"),
        "TIME": now.strftime("%H:%M:%S"),
        "CURR_TEMP": "28.5",
        "RH": "90.0",
        "MSLP": "1004.0",
        "RAIN_1H": "12.0"
    }
    obs_valid = adapter.normalize_record(valid_raw, now, "RUN-01", "HASH-01")
    assert obs_valid.quality_state == "GOOD"

    # Extreme impossible temperature (e.g. 85 degC)
    extreme_raw = {
        "CALL_SIGN": "42971",
        "STATION": "BHUBANESWAR",
        "Latitude": "20.296",
        "Longitude": "85.824",
        "DATE": now.strftime("%Y-%m-%d"),
        "TIME": now.strftime("%H:%M:%S"),
        "CURR_TEMP": "85.0",  # Implausible
        "RH": "90.0",
        "MSLP": "1004.0",
        "RAIN_1H": "12.0"
    }
    obs_extreme = adapter.normalize_record(extreme_raw, now, "RUN-02", "HASH-02")
    assert obs_extreme.quality_state == "SUSPECT"
