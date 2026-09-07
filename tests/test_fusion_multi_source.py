"""
Unit tests for Multi-Source River Stage and Discharge Fusion (Phase 17).
"""

import pytest
from services.fusion.stage_discharge_fusion import StageDischargeFusionEngine
from services.models import ConfidenceLevel

def test_multi_source_stage_fusion_nominal():
    observations = [
        {"source_id": "CWC_TELEMETRY", "stage_m": 26.40, "latency_hours": 0.2, "is_anomalous": False},
        {"source_id": "CWC_MANUAL_GAUGE", "stage_m": 26.45, "latency_hours": 0.5, "is_anomalous": False},
        {"source_id": "WRD_BARRAGE_LOG", "stage_m": 26.38, "latency_hours": 0.4, "is_anomalous": False},
        {"source_id": "SATELLITE_ALTIMETRY", "stage_m": 26.50, "latency_hours": 2.0, "is_anomalous": False}
    ]

    fused_stage, unc, weights, conf = StageDischargeFusionEngine.fuse_stage_observations(observations)
    
    assert 26.38 <= fused_stage <= 26.45
    assert unc < 0.10
    assert conf == ConfidenceLevel.HIGH
    assert weights["CWC_TELEMETRY"] > weights["SATELLITE_ALTIMETRY"]

def test_multi_source_discharge_fusion():
    discharge_obs = [
        {"source_id": "HIRAKUD_OUTFLOW", "discharge_cumec": 14200.0, "reliability_pct": 95.0},
        {"source_id": "MUNDALI_DISCHARGE", "discharge_cumec": 18500.0, "reliability_pct": 92.0}
    ]

    fused_q, unc_q, weights = StageDischargeFusionEngine.fuse_discharge_observations(discharge_obs)
    assert 14000.0 <= fused_q <= 19000.0
    assert unc_q > 0.0
    assert len(weights) == 2
