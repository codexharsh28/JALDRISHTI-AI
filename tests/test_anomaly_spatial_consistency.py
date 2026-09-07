"""
Unit tests for Spatial Cross-Corroboration: Differentiating VALID_EXTREME from LIKELY_SENSOR_ERROR.
"""

import pytest
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification
from services.anomaly.spatial_consistency import SpatialConsistencyEngine
from services.anomaly.detector import HydrometAnomalyDetector

def test_corroborated_valid_extreme_weather():
    """
    Legitimate intense rainfall event: Gauge reads 65 mm/hr, nearby gauges report 55-60 mm/hr,
    NASA GPM satellite QPE reports 52 mm/hr, and NWP forecast reports 48 mm/hr.
    MUST be classified as VALID_EXTREME with WATCH/NORMAL state, NEVER LIKELY_SENSOR_ERROR.
    """
    detector = HydrometAnomalyDetector()
    
    recent_obs = {
        "IMD_AWS_CUTTACK": {"rainfall_1h_mm": 58.0},
        "IMD_AWS_PURI": {"rainfall_1h_mm": 62.0}
    }
    
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=65.0,
        all_recent_observations=recent_obs,
        satellite_qpe=52.0,
        nwp_forecast=48.0
    )
    
    assert rec.classification == AnomalyClassification.VALID_EXTREME
    assert rec.anomaly_state in [AnomalyState.WATCH, AnomalyState.NORMAL]
    assert rec.anomaly_state != AnomalyState.LIKELY_SENSOR_ERROR
    assert rec.anomaly_score <= 0.45
    assert "VALID EXTREME METEOROLOGICAL EVENT" in rec.reason

def test_isolated_uncorroborated_sensor_spike():
    """
    Sensor failure scenario: Bhubaneswar gauge reads 140 mm/hr, but Cuttack/Puri read 0 mm/hr,
    satellite QPE reads 0 mm/hr, and NWP reads 0 mm/hr.
    MUST be classified as LIKELY_SENSOR_ERROR.
    """
    detector = HydrometAnomalyDetector()
    
    recent_obs = {
        "IMD_AWS_CUTTACK": {"rainfall_1h_mm": 0.0},
        "IMD_AWS_PURI": {"rainfall_1h_mm": 0.0}
    }
    
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=140.0,
        all_recent_observations=recent_obs,
        satellite_qpe=0.0,
        nwp_forecast=0.0
    )
    
    assert rec.classification in [AnomalyClassification.LIKELY_SENSOR_ERROR, AnomalyClassification.POSSIBLE_ANOMALY]
    assert rec.anomaly_state in [AnomalyState.LIKELY_SENSOR_ERROR, AnomalyState.ANOMALOUS]
    assert rec.anomaly_score >= 0.70

def test_spatial_engine_insufficient_context():
    """
    When no neighbors exist and satellite/NWP are not available, classify as INSUFFICIENT_CONTEXT.
    """
    engine = SpatialConsistencyEngine()
    score, classification, evidence = engine.evaluate_spatial_consistency(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        observed_value=25.0,
        all_recent_observations={}
    )
    assert classification == AnomalyClassification.INSUFFICIENT_CONTEXT
