"""
Integration tests for Phase 18 Probabilistic REST API Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_probabilistic_rainfall_ensemble_endpoint():
    res = client.get("/api/v1/probabilistic/rainfall/ensemble?base_rate_mm_hr=28.0&ensemble_size=20")
    assert res.status_code == 200
    data = res.json()
    assert data["ensemble_size"] == 20
    assert len(data["members"]) == 20
    assert len(data["mean_trajectory_mm_hr"]) == 8

def test_probabilistic_streamflow_quantiles_endpoint():
    res = client.get("/api/v1/probabilistic/streamflow/quantiles?station_id=CWC_MUNDALI&current_stage_m=26.15")
    assert res.status_code == 200
    data = res.json()
    assert "p05" in data
    assert "p50" in data
    assert "p95" in data
    assert data["conformal_coverage_90pct"] >= 0.90

def test_probabilistic_inundation_exceedance_endpoint():
    res = client.get("/api/v1/probabilistic/inundation/exceedance?peak_stage_m=27.10&danger_threshold_m=26.30")
    assert res.status_code == 200
    data = res.json()
    assert "prob_exceed_0_5m_pct" in data
    assert data["prob_exceed_0_5m_pct"] > 0

def test_probabilistic_uncertainty_decomposition_endpoint():
    res = client.get("/api/v1/probabilistic/uncertainty/decomposition?station_id=CWC_MUNDALI&data_confidence=HIGH")
    assert res.status_code == 200
    data = res.json()
    assert "mean_aleatoric_pct" in data
    assert "mean_epistemic_pct" in data
    assert len(data["horizons"]) > 0
