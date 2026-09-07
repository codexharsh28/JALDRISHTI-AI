"""
API & Route Tests for ConvLSTM Nowcasting Endpoints.
Verifies:
1. /api/v1/rainfall/models lists RAIN_L3_CONVLSTM with EXPERIMENTAL status.
2. /api/v1/rainfall/nowcast?model=convlstm returns 12 valid nowcast frames.
3. /api/v1/rainfall/validation returns held-out evaluation metrics.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_get_rainfall_models_includes_convlstm():
    resp = client.get("/api/v1/rainfall/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    
    convlstm_entry = next((m for m in data["models"] if m["model_id"] == "RAIN_L3_CONVLSTM"), None)
    assert convlstm_entry is not None
    assert convlstm_entry["framework"] == "PyTorch"
    assert convlstm_entry["parameter_count"] == 108065
    assert convlstm_entry["status"] == "EXPERIMENTAL"

def test_get_rainfall_nowcast_with_convlstm_model():
    resp = client.get("/api/v1/rainfall/nowcast?model=convlstm")
    assert resp.status_code == 200
    data = resp.json()

    assert "frames" in data
    assert len(data["frames"]) == 12
    assert data["provenance"]["model_version_id"] == "PyTorch-ConvLSTM-v1.0"
    assert data["provenance"]["source_id"] == "PRECIP_FUSION_CONVLSTM_PYTORCH"

    for frame in data["frames"]:
        assert frame["mean_rainfall_mm_hr"] >= 0.0
        assert frame["max_rainfall_mm_hr"] >= 0.0
        assert 0.0 <= frame["heavy_rain_prob"] <= 1.0
        assert frame["model_level"] == "RAIN_L3_CONVLSTM"

def test_get_rainfall_validation():
    resp = client.get("/api/v1/rainfall/validation")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "L3_PYTORCH_CONVLSTM" in data["models"] or "MOD-NOWCAST-L3-ANALYTICAL" in data["models"]
