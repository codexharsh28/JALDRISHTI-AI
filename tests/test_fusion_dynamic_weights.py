"""
Unit tests for Dynamic Reliability Weighting with Latency & Anomaly Penalties (Phase 17).
"""

import pytest
from services.fusion.stage_discharge_fusion import StageDischargeFusionEngine
from services.models import ConfidenceLevel

def test_stale_source_latency_penalty_reduces_weight():
    # Source A is fresh (0.1h), Source B is delayed (8.0h)
    fresh_obs = [
        {"source_id": "CWC_TELEMETRY", "stage_m": 26.50, "latency_hours": 0.1, "is_anomalous": False},
        {"source_id": "CWC_MANUAL_GAUGE", "stage_m": 26.20, "latency_hours": 8.0, "is_anomalous": False}
    ]

    _, _, weights, _ = StageDischargeFusionEngine.fuse_stage_observations(fresh_obs)
    # Fresh telemetry must have substantially higher weight than 8h stale gauge
    assert weights["CWC_TELEMETRY"] > weights["CWC_MANUAL_GAUGE"] * 3.0

def test_anomalous_source_penalty_reduces_weight():
    obs = [
        {"source_id": "CWC_TELEMETRY", "stage_m": 26.40, "latency_hours": 0.2, "is_anomalous": False},
        {"source_id": "WRD_BARRAGE_LOG", "stage_m": 28.90, "latency_hours": 0.2, "is_anomalous": True}
    ]

    fused_stage, _, weights, _ = StageDischargeFusionEngine.fuse_stage_observations(obs)
    # Fused value should be dominated by the non-anomalous telemetry reading
    assert fused_stage < 27.0
    assert weights["CWC_TELEMETRY"] > weights["WRD_BARRAGE_LOG"]
