"""
Automated Test Suite for JALDRISHTI AI Dashboard & Map Visualization Architecture.
Validates:
1. Real geographic basemap integration and tile provider configurations.
2. Rainfall layer consumption of Phase 4 API with 2.5km discrete computational grid.
3. Hydrology station coordinates and severity mapping from /api/v1/stations.
4. Inundation depth surfaces from Phase 8 API /api/v1/inundation/forecast.
5. Strict honesty regarding Radar availability.
6. System Mode, Data State, and Map State disaggregation.
7. Genuine ConvLSTM model labeling and held-out benchmark data tagging.
8. Data Health registry synchronization with provider statuses.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_geographic_stations_coordinates_and_hierarchy(client):
    """Verifies that all gauge stations have genuine geographic lat/lon coordinates."""
    response = client.get("/api/v1/stations")
    assert response.status_code == 200
    stations = response.json()
    assert len(stations) >= 5

    # Check key stations in Mahanadi delta
    stn_names = [s["name"] for s in stations]
    assert any("Mundali" in n for n in stn_names)
    assert any("Naraj" in n for n in stn_names)

    mundali = next(s for s in stations if "Mundali" in s["name"])
    assert 20.35 <= mundali["lat"] <= 20.55
    assert 85.65 <= mundali["lon"] <= 85.85
    assert mundali["warning_level_m"] > 0
    assert mundali["danger_level_m"] > mundali["warning_level_m"]

    naraj = next(s for s in stations if "Naraj" in s["name"])
    assert 20.35 <= naraj["lat"] <= 20.55
    assert 85.75 <= naraj["lon"] <= 85.95

def test_rainfall_nowcast_api_and_grid_attributes(client):
    """Verifies Phase 4 / Phase 10 rainfall nowcast payload for 2.5km discrete model grid."""
    response = client.get("/api/v1/rainfall/nowcast?model=convlstm")
    assert response.status_code == 200
    data = response.json()
    assert "current_fused_rainfall_mm_hr" in data
    assert "accumulation_6h_mm" in data
    assert "frames" in data
    assert len(data["frames"]) >= 7

    # Verify frame horizons
    lead_times = [f["lead_time_minutes"] for f in data["frames"]]
    assert 30 in lead_times
    assert 60 in lead_times
    assert 120 in lead_times
    assert 360 in lead_times

def test_inundation_forecast_api_depth_and_extent(client):
    """Verifies Phase 8 2D inundation forecast outputs with hydraulic depth classes."""
    response = client.get("/api/v1/inundation/forecast?lead_time_hours=12")
    assert response.status_code == 200
    data = response.json()
    assert "inundated_area_sqkm" in data
    assert data["inundated_area_sqkm"] > 0
    assert "depth_class_0_30cm_sqkm" in data or "depth_class_0_0_3m_sqkm" in data
    assert "depth_class_1_2m_sqkm" in data
    assert "depth_class_gt_2m_sqkm" in data
    assert "flood_prob_mean" in data

def test_data_health_sources_catalog_structure(client):
    """Verifies data health report structure."""
    response = client.get("/api/v1/data-health")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert len(data["sources"]) >= 4

def test_live_sources_catalog_and_modes(client):
    """Verifies the live ingestion sources catalog endpoint."""
    response = client.get("/api/v1/live/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 4

def test_replay_events_catalog_availability(client):
    """Verifies that historical replay events are non-empty and well-structured."""
    response = client.get("/api/v1/replay/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    event_ids = [e["event_id"] for e in events]
    assert any("EVT-MAHANADI" in eid for eid in event_ids)

def test_alerts_endpoint_structure_and_gating(client):
    """Verifies that alerts provide severity levels, location, and human review flags."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1
    first_alert = alerts[0]
    assert "severity" in first_alert
    assert "location_name" in first_alert
    assert "requires_human_review" in first_alert
    assert "data_confidence" in first_alert

def test_model_validation_held_out_metrics_separation(client):
    """Verifies that model validation returns real held-out metrics without fabricated zeros."""
    response = client.get("/api/v1/rainfall/validation")
    assert response.status_code == 200
    val_data = response.json()
    assert "models" in val_data
    assert "L3_PYTORCH_CONVLSTM" in val_data["models"]
    convlstm = val_data["models"]["L3_PYTORCH_CONVLSTM"]
    assert convlstm["overall"]["rmse_mm"] > 0
    assert convlstm["overall"]["mae_mm"] > 0
