"""
Inundation Evolution & Impact Expansion Tests during Demo Scenario.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.demo.demo_orchestrator import demo_orchestrator

client = TestClient(app)

def test_inundation_growth_during_surge():
    demo_orchestrator.start_demo()
    # Advance to Stage 7 (Inundation Expansion)
    for _ in range(7):
        demo_orchestrator.step_forward()

    res = client.get("/api/v1/inundation/forecast?lead_time_hours=12")
    assert res.status_code == 200
    data = res.json()
    assert data["inundated_area_sqkm"] > 100.0

    res_imp = client.get("/api/v1/impacts")
    assert res_imp.status_code == 200
    data_imp = res_imp.json()
    assert data_imp["population_exposed"] > 20000
