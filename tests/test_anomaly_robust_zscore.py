"""
Unit tests for Level 2 Robust Z-Score (Median Absolute Deviation) & Sensor Baselines.
"""

import pytest
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification
from services.anomaly.detector import HydrometAnomalyDetector
from services.anomaly.baselines import StationBaselineTracker

def test_robust_zscore_calculation():
    tracker = StationBaselineTracker()
    tracker.reset()
    
    # Ingest 15 normal rainfall readings around 10 mm
    sample_values = [10.0, 10.2, 9.8, 10.5, 9.9, 10.1, 10.4, 9.7, 10.0, 10.3, 9.9, 10.1, 10.2, 9.8, 10.0]
    for v in sample_values:
        tracker.record_observation("STATION_TEST", "rainfall_1h_mm", v)

    stats = tracker.get_baseline_stats("STATION_TEST", "rainfall_1h_mm")
    assert 9.9 <= stats["median"] <= 10.2
    assert stats["mad"] > 0.0
    assert stats["mad"] < 1.0

def test_robust_zscore_outlier_detection():
    detector = HydrometAnomalyDetector()
    
    # Train detector baseline on steady temperature ~28°C
    for _ in range(20):
        detector.evaluate_observation(
            station_id="STATION_Z",
            variable="temperature_c",
            value=28.0
        )

    # Sudden uncorroborated surge to 45°C
    rec = detector.evaluate_observation(
        station_id="STATION_Z",
        variable="temperature_c",
        value=45.0
    )
    assert "LEVEL_2_ROBUST_ZSCORE" in rec.layers_triggered
    assert rec.anomaly_score >= 0.5
