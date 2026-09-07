"""
Unit tests for Level 1 Temporal Jump, Rate-of-Change & Sensor Freeze / Flatline.
"""

import pytest
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification
from services.anomaly.detector import HydrometAnomalyDetector
from services.anomaly.baselines import StationBaselineTracker

def test_temporal_jump_river_stage():
    detector = HydrometAnomalyDetector()
    # Flash rise of 8.0 meters in 1 hour exceeds 4.5m/hr max jump
    rec = detector.evaluate_observation(
        station_id="CWC_MUNDALI",
        variable="river_stage_m",
        value=28.0,
        previous_value=20.0
    )
    assert "LEVEL_1_TEMPORAL_JUMP" in rec.layers_triggered
    assert rec.anomaly_state in [AnomalyState.ANOMALOUS, AnomalyState.LIKELY_SENSOR_ERROR]
    assert rec.classification in [AnomalyClassification.TEMPORAL_JUMP, AnomalyClassification.LIKELY_SENSOR_ERROR, AnomalyClassification.POSSIBLE_ANOMALY]

def test_temporal_jump_temperature_step():
    detector = HydrometAnomalyDetector()
    # 25°C jump in 1 hour (e.g. 25°C -> 52°C) exceeds 15°C/hr jump limit
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="temperature_c",
        value=52.0,
        previous_value=25.0
    )
    assert "LEVEL_1_TEMPORAL_JUMP" in rec.layers_triggered
    assert rec.anomaly_score >= 0.7

def test_sensor_freeze_flatline():
    tracker = StationBaselineTracker()
    tracker.reset()
    
    # Simulate 6 consecutive identical stage values
    for _ in range(6):
        tracker.record_observation("CWC_MUNDALI", "river_stage_m", 24.50)

    count = tracker.get_flatline_count("CWC_MUNDALI", "river_stage_m")
    assert count >= 6

def test_normal_continuity():
    detector = HydrometAnomalyDetector()
    # Normal stage variation: 24.5m -> 24.8m in 1h
    rec = detector.evaluate_observation(
        station_id="CWC_MUNDALI",
        variable="river_stage_m",
        value=24.8,
        previous_value=24.5
    )
    assert "LEVEL_1_TEMPORAL_JUMP" not in rec.layers_triggered
    assert rec.anomaly_state == AnomalyState.NORMAL
