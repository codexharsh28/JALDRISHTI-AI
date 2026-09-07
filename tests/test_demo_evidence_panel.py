"""
Verification Evidence & API Readiness Tests.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_demo_api_endpoints_functional():
    res_status = client.get("/api/v1/demo/status")
    assert res_status.status_code == 200

    res_timeline = client.get("/api/v1/demo/timeline")
    assert res_timeline.status_code == 200
    data = res_timeline.json()
    assert data["stages_count"] == 14
    assert len(data["timeline"]) == 14

    res_start = client.post("/api/v1/demo/start")
    assert res_start.status_code == 200
    assert res_start.json()["is_active"] is True

    res_speed = client.post("/api/v1/demo/speed?speed=2.0")
    assert res_speed.status_code == 200
    assert res_speed.json()["playback_speed"] == 2.0

    res_reset = client.post("/api/v1/demo/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["is_active"] is False
