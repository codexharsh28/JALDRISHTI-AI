"""
Unit tests for Monotonic Lead Time Uncertainty Widening (Phase 18).
"""

import pytest
from ml.probabilistic.conformal_hydrology import ConformalHydrologyEngine

def test_interval_width_widens_with_horizon():
    res = ConformalHydrologyEngine.predict_conformal_quantiles(
        station_id="CWC_MUNDALI",
        current_stage_m=26.15,
        horizons_hours=[3, 12, 24, 48, 72]
    )

    widths = [res.p90[i] - res.p10[i] for i in range(len(res.horizons_hours))]
    # +72h width must be strictly greater than +3h width
    assert widths[-1] > widths[0] * 1.8
