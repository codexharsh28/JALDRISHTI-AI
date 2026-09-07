"""
Unit tests for Stochastic Ensemble Precipitation Nowcasting (Phase 18).
"""

import pytest
from datetime import datetime, timezone
from ml.probabilistic.ensemble_nowcaster import EnsembleNowcaster

def test_stochastic_ensemble_generation_and_member_count():
    nowcaster = EnsembleNowcaster(ensemble_size=20)
    base_t = datetime(2026, 8, 27, 14, 0, 0, tzinfo=timezone.utc)
    
    res = nowcaster.generate_ensemble_nowcast(
        base_rate_mm_hr=32.0,
        base_time=base_t,
        forecast_run_id="FR-TEST-ENS-01"
    )

    assert res.ensemble_size == 20
    assert len(res.members) == 20
    assert len(res.horizons_hours) == 8
    assert len(res.mean_trajectory_mm_hr) == 8
    assert len(res.p10_trajectory_mm_hr) == 8
    assert len(res.p90_trajectory_mm_hr) == 8

def test_ensemble_quantile_monotonicity():
    nowcaster = EnsembleNowcaster(ensemble_size=20)
    base_t = datetime(2026, 8, 27, 14, 0, 0, tzinfo=timezone.utc)
    
    res = nowcaster.generate_ensemble_nowcast(
        base_rate_mm_hr=25.0,
        base_time=base_t
    )

    for i in range(len(res.horizons_hours)):
        # p10 <= p50 <= p90 must strictly hold
        assert res.p10_trajectory_mm_hr[i] <= res.p50_trajectory_mm_hr[i] + 1e-4
        assert res.p50_trajectory_mm_hr[i] <= res.p90_trajectory_mm_hr[i] + 1e-4
