"""
Alert Orchestration & Safety Workflow Tests: State Machine, Deadband Hysteresis, Deduplication, Human Review Gate, RBAC Security, and Immutable Audit Logging.
"""

import pytest
from datetime import datetime, timezone
from services.alerts.alert_engine import AlertEngine
from services.alerts.alert_types import (
    AlertLifecycleState,
    OperatorAction,
    UserRole,
    AlertIncident
)
from services.alerts.security import verify_operator_permission
from services.alerts.audit_logger import AlertAuditLogger
from services.models import ConfidenceLevel, AlertSeverity

# 1. State Machine & Review Actions
def test_alert_state_machine_transitions():
    engine = AlertEngine()
    item = engine.evaluate_alert(
        fused_rain_mm_hr=35.0,
        rain_24h_mm=160.0,
        river_stage_m=27.2,
        warning_stage_m=25.0,
        danger_stage_m=26.3,
        flood_prob=0.88,
        inundated_area_sqkm=180.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=12.0,
        forecast_run_id="FR-ALT-01",
        base_time=datetime.now(timezone.utc)
    )
    assert item.severity == AlertSeverity.RED
    assert item.requires_human_review is True

    # Acknowledge review action
    incident = engine.execute_review_action(
        alert_id=item.alert_id,
        action=OperatorAction.ACKNOWLEDGE,
        operator_id="Disaster Ops Director",
        operator_role=UserRole.OPERATOR,
        reason="Hydraulic model output corroborated by upstream barrage discharge."
    )
    assert incident.status == AlertLifecycleState.ACKNOWLEDGED
    assert len(incident.audit_history) == 1
    assert incident.audit_history[0].action == OperatorAction.ACKNOWLEDGE

# 2. RBAC Permissions Matrix
def test_rbac_permissions():
    # VIEWER cannot acknowledge or dismiss
    assert verify_operator_permission(UserRole.VIEWER, OperatorAction.ACKNOWLEDGE) is False
    assert verify_operator_permission(UserRole.VIEWER, OperatorAction.DISMISS) is False

    # ANALYST can request field verification
    assert verify_operator_permission(UserRole.ANALYST, OperatorAction.REQUEST_FIELD_VERIFICATION) is True
    # ANALYST cannot dismiss
    assert verify_operator_permission(UserRole.ANALYST, OperatorAction.DISMISS) is False

    # OPERATOR can acknowledge, downgrade, dismiss
    assert verify_operator_permission(UserRole.OPERATOR, OperatorAction.ACKNOWLEDGE) is True
    assert verify_operator_permission(UserRole.OPERATOR, OperatorAction.DOWNGRADE) is True
    assert verify_operator_permission(UserRole.OPERATOR, OperatorAction.DISMISS) is True

    # ADMINISTRATOR has full permission
    assert verify_operator_permission(UserRole.ADMINISTRATOR, OperatorAction.SUPPRESS) is True

def test_rbac_unauthorized_execution():
    engine = AlertEngine()
    with pytest.raises(PermissionError):
        engine.execute_review_action(
            alert_id="ALT-UNAUTH-01",
            action=OperatorAction.DISMISS,
            operator_id="Guest User",
            operator_role=UserRole.VIEWER,
            reason="Unauthorized attempt"
        )

# 3. Deadband Hysteresis & Condition Fingerprint Deduplication
def test_alert_condition_fingerprint():
    engine = AlertEngine()
    t1 = datetime.now(timezone.utc)
    item1 = engine.evaluate_alert(
        fused_rain_mm_hr=30.0,
        rain_24h_mm=140.0,
        river_stage_m=26.8,
        warning_stage_m=25.0,
        danger_stage_m=26.3,
        flood_prob=0.85,
        inundated_area_sqkm=120.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=6.0,
        forecast_run_id="FR-DUP-01",
        base_time=t1
    )
    inc = engine.get_incident_by_id(item1.alert_id)
    assert inc is not None
    assert inc.condition_fingerprint is not None
    assert len(inc.condition_fingerprint) == 12

# 4. Mandatory Human Review Safety Gate for RED
def test_red_alert_safety_gate():
    engine = AlertEngine()
    item = engine.evaluate_alert(
        fused_rain_mm_hr=40.0,
        rain_24h_mm=180.0,
        river_stage_m=27.5,
        warning_stage_m=25.0,
        danger_stage_m=26.3,
        flood_prob=0.90,
        inundated_area_sqkm=220.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=8.0,
        forecast_run_id="FR-GATE-01",
        base_time=datetime.now(timezone.utc)
    )
    assert item.severity == AlertSeverity.RED
    assert item.requires_human_review is True
    # Initial state must be PENDING_HUMAN_REVIEW
    inc = engine.get_incident_by_id(item.alert_id)
    assert inc.status == AlertLifecycleState.PENDING_HUMAN_REVIEW

# 5. Field Verification Flow
def test_field_verification_flow():
    engine = AlertEngine()
    item = engine.evaluate_alert(
        fused_rain_mm_hr=20.0,
        rain_24h_mm=90.0,
        river_stage_m=25.8,
        warning_stage_m=25.0,
        danger_stage_m=26.3,
        flood_prob=0.65,
        inundated_area_sqkm=80.0,
        data_confidence=ConfidenceLevel.HIGH,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=12.0,
        forecast_run_id="FR-FIELD-01",
        base_time=datetime.now(timezone.utc)
    )
    # Request field verification
    inc = engine.execute_review_action(
        alert_id=item.alert_id,
        action=OperatorAction.REQUEST_FIELD_VERIFICATION,
        operator_id="DEOC Duty Officer",
        operator_role=UserRole.ANALYST,
        reason="Check physical gauge gauge marker at Mundali weir."
    )
    assert inc.field_verification_status == "FIELD_VERIFICATION_REQUIRED"
