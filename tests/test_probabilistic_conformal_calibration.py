"""
Unit tests for Conformal Calibration Coverage & Interval Width (Phase 18).
"""

import pytest
from ml.probabilistic.conformal_hydrology import ConformalHydrologyEngine

def test_conformal_coverage_nominal_targets():
    res = ConformalHydrologyEngine.predict_conformal_quantiles(
        station_id="CWC_NARAJ",
        current_stage_m=25.20,
        peak_predicted_m=26.45
    )

    # Nominal 90% coverage target
    assert res.conformal_coverage_90pct >= 0.90
    # Nominal 95% coverage target
    assert res.conformal_coverage_95pct >= 0.95
    # Reasonable physical interval width (< 1.5m)
    assert 0.30 <= res.mean_interval_width_90pct_m <= 1.50
