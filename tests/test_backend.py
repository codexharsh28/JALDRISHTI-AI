"""
Unit and Integration Tests for JALDRISHTI AI Backend.
Tests Quality Control, Adapters, Multi-Source Fusion, ML Nowcast, Streamflow,
Inundation, Alerts, Degradation Safety Gate, and FastAPI endpoints.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.main import app
from services.models import QualityFlag, SourceStatus, AlertSeverity, ConfidenceLevel
from services.preprocessing.qc import QualityControlEngine
from services.fusion.precipitation import PrecipitationFusionEngine
from ml.rainfall.nowcast_models import RainfallNowcastSuite
from ml.streamflow.discharge_models import HydrologyForecastSuite
from ml.inundation.hydraulic_surrogate import HydraulicSurrogateModel
from services.alerts.alert_engine import AlertEngine
from services.replay.replay_engine import ReplayEngine

client = TestClient(app)

def test_health_and_ready():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

    res_ready = client.get("/api/v1/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["ready"] is True

def test_basin_and_stations():
    res = client.get("/api/v1/basins")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res_stn = client.get("/api/v1/stations")
    assert res_stn.status_code == 200
    assert len(res_stn.json()) == 12

def test_quality_control_deterministic():
    # Negative rainfall should be flagged as BAD
    bad_record = {
        "lat": 20.44, "lon": 85.74, "timestamp": datetime.now(timezone.utc),
        "rainfall_1h_mm": -10.5
    }
    flag, anomalies = QualityControlEngine.check_observation(bad_record)
    assert flag == QualityFlag.BAD
    assert "rainfall_1h_mm" in anomalies

    # Normal valid observation
    good_record = {
        "lat": 20.44, "lon": 85.74, "timestamp": datetime.now(timezone.utc),
        "rainfall_1h_mm": 24.5, "temperature_c": 27.0
    }
    flag_good, _ = QualityControlEngine.check_observation(good_record)
    assert flag_good == QualityFlag.GOOD

def test_precipitation_fusion_weights():
    fusion = PrecipitationFusionEngine.fuse(
        radar_precip_mm_hr=30.0,
        gauge_mean_precip_mm_hr=25.0,
        insat_precip_mm_hr=20.0,
        imerg_precip_mm_hr=22.0,
        nwp_precip_mm_hr=18.0
    )
    assert "fused_rainfall_mm_hr" in fusion
    assert fusion["fused_rainfall_mm_hr"] > 0
    assert "source_weights" in fusion

def test_rainfall_nowcast_api():
    res = client.get("/api/v1/rainfall/nowcast")
    assert res.status_code == 200
    data = res.json()
    assert len(data["frames"]) >= 5
    assert data["provenance"]["is_simulation"] is True

def test_hydrology_hydrograph_api():
    res = client.get("/api/v1/hydrology/forecast?station_id=STN-01")
    assert res.status_code == 200
    data = res.json()
    assert len(data["hydrograph"]) > 0
    assert "peak_predicted_level_m" in data

def test_inundation_and_impact_api():
    res_inund = client.get("/api/v1/inundation/forecast?lead_time_hours=12")
    assert res_inund.status_code == 200
    assert res_inund.json()["inundated_area_sqkm"] > 0

    res_impact = client.get("/api/v1/impacts")
    assert res_impact.status_code == 200
    assert "population_exposed" in res_impact.json()

def test_alert_human_review_requirement():
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) >= 1
    # Check that high severity alert requires human review
    if alerts[0]["severity"] == "RED":
        assert alerts[0]["requires_human_review"] is True

def test_sensor_degradation_confidence_drop():
    # Simulate radar failure
    outage_res = client.post("/api/v1/data-health/simulate-outage?source_id=DOPPLER_RADAR_PARADIP&is_offline=true")
    assert outage_res.status_code == 200
    
    # Check that alert reflects degraded confidence and constrains RED escalation
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert alerts[0]["data_confidence"] == "DATA_DEGRADED"
    
    # Restore radar
    restore_res = client.post("/api/v1/data-health/simulate-outage?source_id=DOPPLER_RADAR_PARADIP&is_offline=false")
    assert restore_res.status_code == 200

def test_metrics_observability_endpoint():
    res = client.get("/api/v1/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "ingestion_latency_ms" in data
    assert "model_inference_latency_ms" in data
    assert "active_forecast_run_id" in data

def test_alert_acknowledgement_workflow():
    alerts = client.get("/api/v1/alerts").json()
    alert_id = alerts[0]["alert_id"]
    ack_res = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", json="District Collector - Cuttack")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "SUCCESS"

def test_replay_determinism():
    engine = ReplayEngine()
    s0 = engine.get_current_state()
    assert s0.step_index == 0
    s1 = engine.step_forward()
    assert s1.step_index == 1
    assert s1.stage_name == "RAINFALL_INCREASE"
    engine.reset()
    s_reset = engine.get_current_state()
    assert s_reset.step_index == 0
