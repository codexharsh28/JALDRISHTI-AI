"""
Unit tests for Level 3 Online EWMA Dynamic Volatility Bands.
"""

import pytest
from services.anomaly.anomaly_types import AnomalyState
from services.anomaly.baselines import StationBaselineTracker
from services.anomaly.detector import HydrometAnomalyDetector

def test_ewma_tracking_and_variance():
    tracker = StationBaselineTracker(alpha_ewma=0.2)
    tracker.reset()

    # Step transition from 20 -> 40
    for val in [20.0, 20.0, 20.0, 25.0, 30.0, 35.0, 40.0]:
        tracker.record_observation("STN_EWMA", "river_stage_m", val)

    stats = tracker.get_baseline_stats("STN_EWMA", "river_stage_m")
    assert stats["ewma_mean"] > 25.0
    assert stats["ewma_std"] > 0.5

def test_ewma_volatility_band_deviation():
    detector = HydrometAnomalyDetector()
    
    # Establish tight baseline
    for _ in range(15):
        detector.evaluate_observation(
            station_id="STN_EWMA_DEV",
            variable="surface_pressure_hpa",
            value=1008.0
        )

    # Sharp pressure drop (cyclonic surge)
    rec = detector.evaluate_observation(
        station_id="STN_EWMA_DEV",
        variable="surface_pressure_hpa",
        value=965.0
    )
    assert "LEVEL_3_EWMA_DEVIATION" in rec.layers_triggered
    assert rec.anomaly_state in [AnomalyState.ANOMALOUS, AnomalyState.WATCH, AnomalyState.LIKELY_SENSOR_ERROR]
