"""
Unit tests for IMD AWS Observation Freshness Evaluation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from services.ingestion.live_adapters import IMDLiveAdapter
from services.ingestion.live_interfaces import SourceState

def test_freshness_categories():
    adapter = IMDLiveAdapter()
    now = datetime.now(timezone.utc)

    # 1. Fresh observation (30 mins old)
    raw_fresh = [{
        "CALL_SIGN": "42971",
        "STATION": "BHUBANESWAR",
        "DATE": (now - timedelta(minutes=30)).strftime("%Y-%m-%d"),
        "TIME": (now - timedelta(minutes=30)).strftime("%H:%M:%S"),
        "Latitude": "20.296",
        "Longitude": "85.824",
        "CURR_TEMP": "28.0"
    }]

    result_fresh = adapter.fetch(custom_raw_payload=raw_fresh)
    assert result_fresh.source_state == SourceState.AVAILABLE
    assert len(result_fresh.observations) == 1

    # 2. Empty payload
    result_empty = adapter.fetch(custom_raw_payload=[])
    assert result_empty.source_state == SourceState.UNAVAILABLE
