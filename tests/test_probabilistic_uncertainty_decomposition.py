"""
Unit tests for Aleatoric vs Epistemic Uncertainty Decomposition (Phase 18).
"""

import pytest
from ml.probabilistic.uncertainty_decomposer import UncertaintyDecomposer

def test_aleatoric_and_epistemic_sum_to_100():
    res = UncertaintyDecomposer.decompose_uncertainty(
        station_id="CWC_MUNDALI",
        data_confidence="HIGH"
    )

    assert len(res.horizons) == 8
    for h in res.horizons:
        # Sum of percentages equals 100%
        assert abs((h.aleatoric_pct + h.epistemic_pct) - 100.0) < 0.2
        assert h.total_variance == round(h.aleatoric_variance + h.epistemic_variance, 4)

def test_degraded_data_increases_epistemic_fraction():
    res_high = UncertaintyDecomposer.decompose_uncertainty(station_id="CWC_MUNDALI", data_confidence="HIGH")
    res_deg = UncertaintyDecomposer.decompose_uncertainty(station_id="CWC_MUNDALI", data_confidence="DATA_DEGRADED")

    # Epistemic variance must be higher under degraded data
    assert res_deg.mean_epistemic_pct > res_high.mean_epistemic_pct
