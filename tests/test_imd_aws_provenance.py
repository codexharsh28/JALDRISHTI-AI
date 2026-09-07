"""
Unit tests for IMD AWS Provenance & Hash Auditing.
"""

import pytest
from datetime import datetime, timezone
from services.ingestion.live_adapters import IMDLiveAdapter

def test_observation_provenance_and_hash():
    adapter = IMDLiveAdapter()
    now = datetime.now(timezone.utc)
    raw = [{
        "CALL_SIGN": "42970",
        "STATION": "CUTTACK",
        "Latitude": "20.462",
        "Longitude": "85.882",
        "CURR_TEMP": "27.5"
    }]

    result = adapter.fetch(custom_raw_payload=raw)
    assert result.raw_payload_checksum != "ERROR"
    assert len(result.observations) == 1
    obs = result.observations[0]
    assert obs["data_state"] == "OBSERVED_IMD_AWS"
    assert obs["is_observed_telemetry"] is True
    assert obs["provider"] == "IMD_AWS"
    assert obs["raw_payload_hash"] == result.raw_payload_checksum
