"""
Unit tests for Continuous Ranked Probability Score (CRPS) Evaluation (Phase 18).
"""

import pytest
from ml.probabilistic.conformal_hydrology import ConformalHydrologyEngine

def test_crps_score_positive_and_bounded():
    res = ConformalHydrologyEngine.predict_conformal_quantiles(
        station_id="CWC_MUNDALI",
        current_stage_m=26.15,
        peak_predicted_m=26.80
    )

    # CRPS should be positive and under 0.25m for a well-calibrated ensemble
    assert res.crps_score > 0.0
    assert res.crps_score <= 0.25
