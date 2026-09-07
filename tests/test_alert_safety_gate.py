"""
Unit tests for Mandatory RED Safety Gate & Human Review Enforcement (Phase 16).
"""

import pytest
from datetime import datetime, timezone
from services.alerts.alert_engine import AlertEngine
from services.models import ConfidenceLevel, AlertSeverity
from services.alerts.alert_types import AlertLifecycleState, OperatorAction, UserRole

def test_red_alert_requires_human_review_and_pending_state():
    engine = AlertEngine()
    item = engine.evaluate_alert(
        fused_rain_mm_hr=60.0,
        rain_24h_mm=220.0,
        river_stage_m=28.10,
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.92,
        inundated_area_sqkm=350.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=6.0,
        forecast_run_id="FR-RED-SAFE-01",
        base_time=datetime.now(timezone.utc)
    )

    assert item.severity == AlertSeverity.RED
    assert item.requires_human_review is True
    
    incident = engine.get_incident_by_id(item.alert_id)
    assert incident is not None
    assert incident.status == AlertLifecycleState.PENDING_HUMAN_REVIEW

def test_red_alert_operator_acknowledgement():
    engine = AlertEngine()
    item = engine.evaluate_alert(
        fused_rain_mm_hr=60.0,
        rain_24h_mm=220.0,
        river_stage_m=28.10,
        warning_stage_m=25.0,
        danger_stage_m=26.30,
        flood_prob=0.92,
        inundated_area_sqkm=350.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=6.0,
        forecast_run_id="FR-RED-SAFE-02",
        base_time=datetime.now(timezone.utc)
    )

    incident = engine.execute_review_action(
        alert_id=item.alert_id,
        action=OperatorAction.ACKNOWLEDGE,
        operator_id="Duty Commander 101",
        operator_role=UserRole.OPERATOR,
        reason="Field gauge level verified at Mundali"
    )

    assert incident.status == AlertLifecycleState.ACKNOWLEDGED
    assert incident.requires_human_review is False
    assert len(incident.audit_history) == 1
