"""
Anomaly Detection Tests: Physical Limits, Continuity, Robust Z-score, EWMA, Spatial Cross-Corroboration, Streaming & Alert Safety.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification, AnomalyDomain
from services.anomaly.detector import HydrometAnomalyDetector
from services.anomaly.baselines import StationBaselineTracker
from services.anomaly.spatial_consistency import SpatialConsistencyEngine
from services.anomaly.service import AnomalyService
from services.anomaly.store import AnomalyStore
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel

# 1. Physical Limits
def test_anomaly_physical_limits_rainfall_negative():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="TEST_STATION",
        variable="rainfall_1h_mm",
        value=-5.0
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
    assert rec.classification == AnomalyClassification.OUT_OF_BOUNDS

def test_anomaly_physical_limits_extreme_rain():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="TEST_STATION",
        variable="rainfall_1h_mm",
        value=450.0
    )
    assert rec.anomaly_state == AnomalyState.LIKELY_SENSOR_ERROR
    assert rec.classification == AnomalyClassification.OUT_OF_BOUNDS

# 2. Temporal Jump & Flatline
def test_anomaly_temporal_jump_stage():
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="CWC_MUNDALI",
        variable="river_stage_m",
        value=25.5,
        previous_value=20.0
    )
    assert rec.anomaly_state in [AnomalyState.ANOMALOUS, AnomalyState.LIKELY_SENSOR_ERROR]
    assert rec.classification in [AnomalyClassification.TEMPORAL_JUMP, AnomalyClassification.STATISTICAL_OUTLIER]

# 3. Robust Z-score & Baseline
def test_anomaly_robust_zscore():
    tracker = StationBaselineTracker()
    for val in [10.0, 10.5, 11.0, 9.8, 10.2, 10.1, 10.4, 9.9, 10.0]:
        tracker.record_observation("STATION_A", "rainfall_1h_mm", val)
    
    stats = tracker.get_baseline_stats("STATION_A", "rainfall_1h_mm")
    assert stats["median"] > 0
    assert stats["mad"] > 0

# 4. EWMA Volatility
def test_anomaly_ewma_tracking():
    tracker = StationBaselineTracker()
    for val in [10.0, 12.0, 14.0, 16.0, 18.0]:
        tracker.record_observation("STATION_A", "temperature_c", val)
    stats = tracker.get_baseline_stats("STATION_A", "temperature_c")
    assert stats["ewma_mean"] > 10.0

# 5. Spatial Cross-Corroboration: Valid Extreme vs Sensor Error
def test_spatial_consistency_valid_extreme():
    engine = SpatialConsistencyEngine()
    score, classification, evidence = engine.evaluate_spatial_consistency(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        observed_value=65.0,
        all_recent_observations={
            "IMD_AWS_CUTTACK": {"rainfall_1h_mm": 58.0},
            "IMD_AWS_PURI": {"rainfall_1h_mm": 62.0}
        },
        satellite_qpe=55.0,
        nwp_forecast=50.0
    )
    assert classification == AnomalyClassification.VALID_EXTREME

def test_spatial_consistency_isolated_spike_sensor_error():
    engine = SpatialConsistencyEngine()
    score, classification, evidence = engine.evaluate_spatial_consistency(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        observed_value=120.0,
        all_recent_observations={
            "IMD_AWS_CUTTACK": {"rainfall_1h_mm": 2.0},
            "IMD_AWS_PURI": {"rainfall_1h_mm": 1.5}
        },
        satellite_qpe=0.0,
        nwp_forecast=1.0
    )
    assert classification in [AnomalyClassification.LIKELY_SENSOR_ERROR, AnomalyClassification.POSSIBLE_ANOMALY]

# 6. Streaming Anomaly Service
def test_anomaly_service_flow():
    svc = AnomalyService()
    svc.initialize()
    rec = asyncio.run(svc.process_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=12.0
    ))
    assert rec.anomaly_state == AnomalyState.NORMAL

# 7. Alert Safety Invariant: Sensor Anomaly Never Creates RED Alert
def test_anomaly_safety_invariant():
    alert_engine = AlertEngine()
    item = alert_engine.evaluate_alert(
        fused_rain_mm_hr=45.0,
        rain_24h_mm=210.0,
        river_stage_m=28.5,
        warning_stage_m=25.0,
        danger_stage_m=26.3,
        flood_prob=0.92,
        inundated_area_sqkm=250.0,
        data_confidence=ConfidenceLevel.DATA_DEGRADED,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=6.0,
        forecast_run_id="FR-ANOM-TEST",
        base_time=datetime.now(timezone.utc)
    )
    assert item.severity.value != "RED"
    assert item.severity.value == "ORANGE"
    assert item.requires_human_review is True
