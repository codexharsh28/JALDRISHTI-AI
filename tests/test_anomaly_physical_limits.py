"""
Unit tests for Level 0 Physical Limits & Missingness anomaly screening.
"""

import pytest
import math
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification
from services.anomaly.detector import HydrometAnomalyDetector
from services.anomaly.baselines import PHYSICAL_BOUNDS

def test_rainfall_negative_value():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=-12.5
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
    assert rec.classification == AnomalyClassification.OUT_OF_BOUNDS
    assert "LEVEL_0_PHYSICAL_BOUNDS" in rec.layers_triggered
    assert rec.anomaly_score == 1.0

def test_rainfall_unphysical_extreme():
    detector = HydrometAnomalyDetector()
    # 450 mm/hr exceeds 300 mm/hr physical cloudburst threshold
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=450.0
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
    assert rec.classification == AnomalyClassification.OUT_OF_BOUNDS
    assert "LEVEL_0_PHYSICAL_BOUNDS" in rec.layers_triggered

def test_river_stage_negative():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="CWC_MUNDALI",
        variable="river_stage_m",
        value=-1.0
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
    assert rec.classification == AnomalyClassification.OUT_OF_BOUNDS

def test_river_stage_unphysical_high():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="CWC_MUNDALI",
        variable="river_stage_m",
        value=85.0 # Max physical limit is 60m
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
    assert rec.classification == AnomalyClassification.OUT_OF_BOUNDS

def test_temperature_limits():
    detector = HydrometAnomalyDetector()
    # Too hot: 68°C exceeds 55°C limit
    rec_hot = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="temperature_c",
        value=68.0
    )
    assert rec_hot.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
    assert rec_hot.classification == AnomalyClassification.OUT_OF_BOUNDS

    # Too cold for Odisha: -15°C violates -5°C limit
    rec_cold = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="temperature_c",
        value=-15.0
    )
    assert rec_cold.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR

def test_humidity_limits():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="relative_humidity_pct",
        value=115.0 # Exceeds 100%
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR

def test_pressure_limits():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="surface_pressure_hpa",
        value=600.0 # Unphysical low
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR

def test_wind_speed_limits():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="wind_speed_kmh",
        value=420.0 # Exceeds 350 km/h limit
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR

def test_missing_observation():
    detector = HydrometAnomalyDetector()
    rec_none = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=None
    )
    assert rec_none.anomaly_state == AnomalyState.ANOMALOUS
    assert rec_none.classification == AnomalyClassification.LIKELY_SENSOR_ERROR
    assert "LEVEL_0_MISSING" in rec_none.layers_triggered

    rec_nan = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=float("nan")
    )
    assert rec_nan.anomaly_state == AnomalyState.ANOMALOUS
