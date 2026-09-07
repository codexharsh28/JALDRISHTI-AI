"""
Unit tests for Alert Safety Invariant: Sensor anomalies must NEVER directly create RED emergency alerts.
"""

import pytest
from datetime import datetime, timezone
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel, AlertSeverity
from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification
from services.anomaly.detector import HydrometAnomalyDetector

def test_sensor_anomaly_never_creates_red_alert():
    """
    Critical Invariant: Even if an uncorroborated sensor reports immense rain (>200mm/hr)
    or extreme stage, if data confidence is degraded by the anomaly engine, AlertEngine
    MUST cap the severity below RED (e.g. ORANGE/YELLOW) and require human review.
    """
    alert_engine = AlertEngine()
    
    # 1. Uncorroborated sensor failure triggering data degradation
    alert_item = alert_engine.evaluate_alert(
        fused_rain_mm_hr=120.0,
        rain_24h_mm=450.0,
        river_stage_m=29.0,
        warning_stage_m=25.0,
        danger_stage_m=26.3,
        flood_prob=0.98,
        inundated_area_sqkm=350.0,
        data_confidence=ConfidenceLevel.DATA_DEGRADED, # Restricted due to sensor anomaly
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=3.0,
        forecast_run_id="FR-SAFETY-TEST-01",
        base_time=datetime.now(timezone.utc)
    )

    # Invariant: Alert severity MUST NOT be RED
    assert alert_item.severity != AlertSeverity.RED
    assert alert_item.severity == AlertSeverity.ORANGE
    assert alert_item.requires_human_review is True
    assert alert_item.recommended_action is not None

def test_anomaly_score_is_not_labeled_probability():
    """
    Score Calibration Invariant: Anomaly score must be labeled as uncalibrated score 0-1,
    never presented as a true statistical probability unless calibrated.
    """
    detector = HydrometAnomalyDetector()
    rec = detector.evaluate_observation(
        station_id="IMD_AWS_BHUBANESWAR",
        variable="rainfall_1h_mm",
        value=110.0
    )
    assert hasattr(rec, "anomaly_score")
    assert 0.0 <= rec.anomaly_score <= 1.0
    assert not hasattr(rec, "probability") # Not called probability
