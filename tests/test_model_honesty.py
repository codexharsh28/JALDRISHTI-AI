"""
Automated Model Honesty & Scientific Integrity Verification Tests.
Ensures that all model docstrings, class names, API endpoints, and model catalog entries
adhere to strict scientific honesty standards (no neural architecture names on analytical formula models).
"""

import pytest
import inspect
import json
from pathlib import Path
from fastapi.testclient import TestClient

from apps.api.main import app
from ml.rainfall.nowcast_models import RainfallNowcastSuite
from ml.streamflow.lstm_forecast import AnalyticalHydrographSurrogate
from ml.streamflow.tft_model import NWPGuidedAnalyticalSurrogate
from ml.streamflow.graph_model import RiverRoutingAnalyticalModel
from ml.streamflow.xgboost_forecast import XGBoostStreamflowNowcaster
from ml.inundation.models import AnalyticalSpatialSurrogate
from services.models import ModelStatus

client = TestClient(app)

# -----------------------------------------------------------------------------
# Test 1: Python import os Regression Guard in main.py
# -----------------------------------------------------------------------------
def test_import_os_present_in_main_api():
    main_py_path = Path("apps/api/main.py")
    assert main_py_path.exists()
    content = main_py_path.read_text(encoding="utf-8")
    assert "import os" in content, "apps/api/main.py MUST import os to avoid runtime crashes on /api/v1/rainfall/validation"

# -----------------------------------------------------------------------------
# Test 2: Rainfall L3 Model Honesty
# -----------------------------------------------------------------------------
def test_rainfall_l3_model_honesty():
    suite = RainfallNowcastSuite()
    meta = suite.metadata()
    assert meta["model_id"] == "MOD-NOWCAST-L3-ANALYTICAL"
    assert "Analytical" in meta["model_name"]
    assert meta["status"] == "CANDIDATE"

    # Verify predict output uses honest model_level
    frames = suite.predict(fused_grid_or_rate=30.0, features={}, base_time=pytest.importorskip("datetime").datetime.now())
    for f in frames:
        assert f.model_level == "L3_ANALYTICAL_SURROGATE"
        assert "CONVLSTM" not in f.model_level

# -----------------------------------------------------------------------------
# Test 3: Streamflow Analytical Surrogate Honesty
# -----------------------------------------------------------------------------
def test_streamflow_analytical_surrogates_honesty():
    # L2: Analytical Hydrograph Surrogate
    l2 = AnalyticalHydrographSurrogate()
    assert l2.model_id == "STREAMFLOW_L2_ANALYTICAL_HYDROGRAPH"
    l2_res = l2.predict_sequence([], [])
    assert l2_res["uncertainty_method"] == "ANALYTICAL_PARAMETRIC_SPREAD"

    # L3: NWP-Guided Analytical Surrogate
    l3 = NWPGuidedAnalyticalSurrogate()
    assert l3.model_id == "STREAMFLOW_L3_NWP_ANALYTICAL"
    l3_res = l3.predict({}, [], [])
    assert l3_res["uncertainty_method"] == "ANALYTICAL_PARAMETRIC_SPREAD"

    # L4: River Routing Analytical Model
    l4 = RiverRoutingAnalyticalModel()
    assert l4.model_id == "STREAMFLOW_L4_RIVER_ROUTING_ANALYTICAL"
    l4_res = l4.predict_node("CWC_MUNDALI", {}, {})
    assert l4_res["uncertainty_method"] == "ANALYTICAL_TOPOLOGICAL_SPREAD"

# -----------------------------------------------------------------------------
# Test 4: XGBoost Streamflow Uses Real Fitted Estimators
# -----------------------------------------------------------------------------
def test_xgboost_streamflow_uses_fitted_estimators():
    xgb = XGBoostStreamflowNowcaster()
    assert hasattr(xgb, "models_p50")
    assert len(xgb.models_p50) > 0
    # Predict with specific feature vector
    res = xgb.predict_multi_horizon([25.0, 120.0, 0.8, 25.5, 25.2, 0.05, 12000.0])
    assert len(res["stage_p50"]) == len(xgb.horizons_hours)
    # Check that p10 <= p50 <= p90
    for p10, p50, p90 in zip(res["stage_p10"], res["stage_p50"], res["stage_p90"]):
        assert p10 <= p50 <= p90

# -----------------------------------------------------------------------------
# Test 5: Inundation Spatial Surrogate Honesty
# -----------------------------------------------------------------------------
def test_inundation_spatial_surrogate_honesty():
    spatial = AnalyticalSpatialSurrogate()
    assert spatial.model_name == "AnalyticalSpatialSurrogate"
    assert spatial.model_status == ModelStatus.CANDIDATE
    doc = inspect.getdoc(AnalyticalSpatialSurrogate)
    assert "Analytical 2D Spatial Inundation Surrogate" in doc

# -----------------------------------------------------------------------------
# Test 6: Model Catalog Status Reconciliation
# -----------------------------------------------------------------------------
def test_model_catalog_reconciliation():
    catalog_path = Path("model_registry/model_catalog.json")
    assert catalog_path.exists()
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    for m in catalog["models"]:
        # No unvalidated model should claim "DEPLOYED"
        assert m["status"] in ["VALIDATED", "CANDIDATE", "BASELINE", "EXPERIMENTAL"]
        if "L3-ANALYTICAL" in m["model_id"] or "INUNDATION" in m["model_id"]:
            assert m["status"] == "CANDIDATE"

# -----------------------------------------------------------------------------
# Test 7: API Endpoints Return Honest Labels
# -----------------------------------------------------------------------------
def test_api_models_endpoint_returns_honest_labels():
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    for m in models:
        # None of the unvalidated models should be "ACTIVE_PRODUCTION" except genuine tested ones
        if "RAINFALL_NOWCAST" in m.get("category", "") and "L3" in m.get("model_id", ""):
            assert m["status"] == "CANDIDATE"
            assert "Analytical" in m["name"]
        if "STREAMFLOW" in m.get("category", "") and "ANALYTICAL" in m.get("model_id", ""):
            assert m["status"] == "CANDIDATE"

def test_api_hydrology_models_endpoint_honest_labels():
    res = client.get("/api/v1/hydrology/models")
    assert res.status_code == 200
    models = res.json()
    model_names = [m["name"] for m in models]
    assert "Analytical Hydrograph Surrogate" in model_names
    assert "NWP-Guided Analytical Surrogate" in model_names
    assert "River Routing Analytical Model" in model_names

def test_api_rainfall_models_endpoint_honest_labels():
    res = client.get("/api/v1/rainfall/models")
    assert res.status_code == 200
    data = res.json()
    l3_model = [m for m in data["models"] if m["level"] == "L3"][0]
    assert l3_model["name"] == "Analytical Storm Decay Surrogate"
    assert l3_model["status"] == "CANDIDATE"

# -----------------------------------------------------------------------------
# Test 8: API Replay Step Control Flow
# -----------------------------------------------------------------------------
def test_api_replay_step_pause_and_control():
    res = client.post("/api/v1/replay/step?action=pause")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["action"] == "pause"
    assert "state" in data
