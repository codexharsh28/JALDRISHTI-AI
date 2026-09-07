"""
Regression tests verifying all major navigation view endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_overview_dashboard_endpoints():
    res = client.get("/api/v1/forecast-runs")
    assert res.status_code == 200
    state_res = client.get("/api/v1/live/current-state")
    assert state_res.status_code == 200

def test_data_health_endpoints():
    res = client.get("/api/v1/live/health")
    assert res.status_code == 200
    imd_res = client.get("/api/v1/live/imd-aws/status")
    assert imd_res.status_code == 200

def test_rainfall_nowcast_endpoints():
    res = client.get("/api/v1/rainfall/nowcast")
    assert res.status_code == 200

def test_river_forecast_endpoints():
    res = client.get("/api/v1/hydrology/forecast")
    assert res.status_code == 200

def test_inundation_endpoints():
    res = client.get("/api/v1/inundation/current")
    assert res.status_code == 200

def test_impact_endpoints():
    res = client.get("/api/v1/impacts")
    assert res.status_code == 200

def test_risk_endpoints():
    res = client.get("/api/v1/risk/current")
    assert res.status_code == 200

def test_alerts_endpoints():
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200

def test_stations_endpoints():
    res = client.get("/api/v1/stations")
    assert res.status_code == 200
