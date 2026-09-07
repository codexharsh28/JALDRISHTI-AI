"""
Automated Tests for Probabilistic Quantile Hydrograph Integrity and Exceedance Math.
"""

from ml.streamflow.xgboost_forecast import XGBoostStreamflowNowcaster

def test_quantile_monotonicity():
    model = XGBoostStreamflowNowcaster()
    features = [45.0, 140.0, 0.85, 26.15, 25.9, 0.08, 18500.0]
    res = model.predict_multi_horizon(features)

    for p10, p50, p90 in zip(res["stage_p10"], res["stage_p50"], res["stage_p90"]):
        assert p10 <= p50, f"P10 ({p10}) must be <= P50 ({p50})"
        assert p50 <= p90, f"P50 ({p50}) must be <= P90 ({p90})"

def test_uncertainty_interval_expansion_with_lead_time():
    model = XGBoostStreamflowNowcaster()
    features = [45.0, 140.0, 0.85, 26.15, 25.9, 0.08, 18500.0]
    res = model.predict_multi_horizon(features)

    width_1h = res["stage_p90"][0] - res["stage_p10"][0]
    width_72h = res["stage_p90"][-1] - res["stage_p10"][-1]

    # Uncertainty must expand with forecast horizon
    assert width_72h > width_1h
