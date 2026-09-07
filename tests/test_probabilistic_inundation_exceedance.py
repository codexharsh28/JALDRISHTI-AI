"""
Unit tests for Probabilistic Inundation Depth Exceedance Surfaces (Phase 18).
"""

import pytest
from ml.probabilistic.uncertainty_decomposer import UncertaintyDecomposer

def test_inundation_depth_exceedance_probabilities():
    res = UncertaintyDecomposer.compute_inundation_exceedance(
        peak_river_stage_m=27.40,
        danger_threshold_m=26.30,
        lead_time_hours=18.0
    )

    assert 0.0 <= res.prob_exceed_0_5m_pct <= 100.0
    assert 0.0 <= res.prob_exceed_1_0m_pct <= 100.0
    assert 0.0 <= res.prob_exceed_2_0m_pct <= 100.0
    # Higher water depth has strictly lower or equal probability of exceedance
    assert res.prob_exceed_0_5m_pct >= res.prob_exceed_1_0m_pct >= res.prob_exceed_2_0m_pct
    assert res.inundation_extent_sqkm_p90 >= res.inundation_extent_sqkm_p50
