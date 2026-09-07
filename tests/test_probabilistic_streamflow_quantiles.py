"""
Unit tests for Conformal Streamflow 7-Quantile Distribution (Phase 18).
"""

import pytest
from ml.probabilistic.conformal_hydrology import ConformalHydrologyEngine

def test_streamflow_7_quantiles_non_crossing():
    res = ConformalHydrologyEngine.predict_conformal_quantiles(
        station_id="CWC_MUNDALI",
        current_stage_m=26.15,
        peak_predicted_m=26.80,
        danger_threshold_m=26.30,
        warning_threshold_m=25.40
    )

    for i in range(len(res.horizons_hours)):
        # p05 <= p10 <= p25 <= p50 <= p75 <= p90 <= p95
        assert res.p05[i] <= res.p10[i]
        assert res.p10[i] <= res.p25[i]
        assert res.p25[i] <= res.p50[i]
        assert res.p50[i] <= res.p75[i]
        assert res.p75[i] <= res.p90[i]
        assert res.p90[i] <= res.p95[i]
