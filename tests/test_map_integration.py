"""
Geospatial Map Integration Tests for JALDRISHTI AI.
Tests that all map data layers, Phase 4 rainfall outputs, station coordinates,
inundation polygons, and alert zones are correctly served by the backend APIs.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_map_basin_and_subbasins_endpoints():
    res = client.get("/api/v1/basins/pilot-mahanadi-delta")
    assert res.status_code == 200
    data = res.json()
    assert data["basin"]["id"] == "pilot-mahanadi-delta"
    assert len(data["subbasins"]) == 3
    assert data["stations_count"] >= 10

def test_map_stations_layer_coordinates():
    res = client.get("/api/v1/stations")
    assert res.status_code == 200
    stations = res.json()
    assert len(stations) >= 10
    for stn in stations:
        assert "lat" in stn
        assert "lon" in stn
        assert 19.0 <= stn["lat"] <= 22.0
        assert 84.0 <= stn["lon"] <= 88.0

def test_map_phase4_rainfall_nowcast_consumption():
    res = client.get("/api/v1/rainfall/nowcast")
    assert res.status_code == 200
    nowcast = res.json()
    assert "forecast_run_id" in nowcast
    assert "current_fused_rainfall_mm_hr" in nowcast
    assert "frames" in nowcast
    assert len(nowcast["frames"]) >= 5

def test_map_inundation_layer_payload():
    res = client.get("/api/v1/inundation/forecast?lead_time_hours=12")
    assert res.status_code == 200
    inund = res.json()
    assert "inundated_area_sqkm" in inund
    assert "depth_class_0_30cm_sqkm" in inund
    assert "flood_polygons_geojson" in inund

def test_map_alerts_layer_payload():
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)
    for alert in alerts:
        assert "severity" in alert
        assert "location_name" in alert
        assert "probability" in alert

def test_map_data_health_strip():
    res = client.get("/api/v1/data-health")
    assert res.status_code == 200
    health = res.json()
    assert "sources" in health
    assert len(health["sources"]) >= 6
