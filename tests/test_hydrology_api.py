"""
Automated Tests for Hydrology REST APIs (/api/v1/hydrology/*).
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_hydrology_stations_endpoint():
    res = client.get("/api/v1/hydrology/stations")
    assert res.status_code == 200
    stns = res.json()
    assert len(stns) >= 5
    mundali = next(s for s in stns if s["station_id"] == "CWC_MUNDALI")
    assert mundali["data_readiness"] == "VERIFIED_AVAILABLE"
    assert mundali["warning_level_m"] == 26.30
    assert mundali["danger_level_m"] == 26.85

def test_hydrology_forecast_endpoint_xgb_default():
    res = client.get("/api/v1/hydrology/forecast?station_id=CWC_MUNDALI&model=L1_XGBOOST")
    assert res.status_code == 200
    data = res.json()
    assert data["station_id"] == "CWC_MUNDALI"
    assert data["model_id"] == "STREAMFLOW_L1_XGBOOST"
    assert len(data["stage_p50"]) == 7
    assert len(data["discharge_p50"]) == 7
    assert "warning_probability" in data
    assert "danger_probability" in data
    assert data["uncertainty_method"] == "QUANTILE_GRADIENT_BOOSTING"

def test_hydrology_models_catalog():
    res = client.get("/api/v1/hydrology/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) == 5
    assert any(m["status"] == "BEST_VALIDATED_MODEL" for m in models)

def test_hydrology_validation_report_endpoint():
    res = client.get("/api/v1/hydrology/validation")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert "L1_XGBOOST" in data["models"] or "L1_XGBoost" in data["models"]
