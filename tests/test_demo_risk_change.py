"""
Material Risk Delta & Causal Explainer Integration Tests during Demo.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.demo.demo_orchestrator import demo_orchestrator

client = TestClient(app)

def test_risk_delta_evolves_with_scenario():
    # Start at T0
    client.post("/api/v1/demo/start")
    res_t0 = client.get("/api/v1/risk/current")
    assert res_t0.status_code == 200
    data_t0 = res_t0.json()
    assert data_t0["risk_score"] == 14.2
    assert data_t0["risk_change"] == 0.0

    # Step to T2 (Heavy Rain)
    client.post("/api/v1/demo/step?direction=forward")
    client.post("/api/v1/demo/step?direction=forward")
    res_t2 = client.get("/api/v1/risk/current")
    assert res_t2.status_code == 200
    data_t2 = res_t2.json()
    assert data_t2["risk_score"] == 36.5
    assert data_t2["risk_change"] == 14.5
    assert data_t2["is_material_change"] is True
    assert len(data_t2["contributors"]) > 0
