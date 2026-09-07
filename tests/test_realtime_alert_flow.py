"""
Unit tests for Alert Lifecycle State Machine and Human Review Safety Gate.
"""

import pytest
from services.alerts.alert_engine import AlertEngine
from services.models import AlertSeverity, ConfidenceLevel
from datetime import datetime, timezone

def test_alert_lifecycle_state_transitions():
    engine = AlertEngine()
    
    # 1. Evaluate RED alert condition
    alert = engine.evaluate_alert(
        fused_rain_mm_hr=45.0,
        rain_24h_mm=160.0,
        river_stage_m=27.20,
        warning_stage_m=25.40,
        danger_stage_m=26.30,
        flood_prob=0.92,
        inundated_area_sqkm=220.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=12.0,
        forecast_run_id="FR-TEST-ALERT",
        base_time=datetime.now(timezone.utc)
    )
    assert alert.severity == AlertSeverity.RED
    assert alert.requires_human_review is True

    # 2. State Transition to PENDING_HUMAN_REVIEW
    trans1 = engine.transition_state(alert.alert_id, "PENDING_HUMAN_REVIEW")
    assert trans1["state"] == "PENDING_HUMAN_REVIEW"

    # 3. State Transition to ACKNOWLEDGED
    trans2 = engine.transition_state(alert.alert_id, "ACKNOWLEDGED", operator_id="Disaster Commander")
    assert trans2["state"] == "ACKNOWLEDGED"
    assert alert.alert_id in engine.acknowledged_alerts
