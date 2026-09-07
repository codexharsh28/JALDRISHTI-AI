"""
Integration tests for Realtime Endpoints and Latency Monitoring.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_realtime_status_endpoint(client):
    res = client.get("/api/v1/realtime/status")
    assert res.status_code == 200
    data = res.json()
    assert "system_mode" in data
    assert "state_version" in data
    assert "event_bus" in data
    assert "queue" in data

def test_realtime_state_delta_endpoint(client):
    res = client.get("/api/v1/realtime/state?since_version=999")
    assert res.status_code == 200
    data = res.json()
    assert "snapshot" in data
    assert data["is_delta"] is True
    assert "delta_events" in data

def test_realtime_latency_endpoint(client):
    res = client.get("/api/v1/realtime/latency")
    assert res.status_code == 200
    data = res.json()
    assert "total_end_to_end_latency_ms" in data
    assert data["total_end_to_end_latency_ms"] <= 1000.0  # Must be under 1 second budget

def test_realtime_queue_status_endpoint(client):
    res = client.get("/api/v1/realtime/queue-status")
    assert res.status_code == 200
    data = res.json()
    assert "queue_depth" in data
    assert "recent_jobs" in data
