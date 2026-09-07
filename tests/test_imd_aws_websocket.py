"""
Integration tests for IMD AWS REST endpoints and diagnostics.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_get_imd_aws_status_endpoint():
    res = client.get("/api/v1/live/imd-aws/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "endpoint" in data
    assert "state" in data
    assert "freshness_state" in data
    assert "station_count" in data

def test_get_imd_aws_stations_endpoint():
    res = client.get("/api/v1/live/imd-aws/stations")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

def test_trigger_imd_aws_refresh_endpoint():
    res = client.post("/api/v1/live/imd-aws/refresh?force=true")
    assert res.status_code == 200
    data = res.json()
    assert "ingestion_run_id" in data or "status" in data
