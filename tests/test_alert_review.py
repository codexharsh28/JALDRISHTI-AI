"""
Unit tests for Operator Review Workflows & Field Verification (Phase 16).
"""

import pytest
from services.alerts.alert_engine import AlertEngine
from services.alerts.alert_types import AlertLifecycleState, OperatorAction, UserRole

def test_alert_escalation_workflow():
    engine = AlertEngine()
    inc = engine.execute_review_action(
        alert_id="ALT-REV-01",
        action=OperatorAction.ESCALATE,
        operator_id="Chief Commander",
        operator_role=UserRole.OPERATOR,
        reason="Embankment seepage reported by local SDMA"
    )
    assert inc.status == AlertLifecycleState.ESCALATED
    assert len(inc.audit_history) == 1
    assert inc.audit_history[0].action == OperatorAction.ESCALATE

def test_alert_downgrade_workflow():
    engine = AlertEngine()
    inc = engine.execute_review_action(
        alert_id="ALT-REV-02",
        action=OperatorAction.DOWNGRADE,
        operator_id="Duty Hydrologist",
        operator_role=UserRole.OPERATOR,
        reason="Upstream barrage gates opened, level cresting"
    )
    assert inc.status == AlertLifecycleState.DOWNGRADED
    assert inc.severity in ["ORANGE", "YELLOW"]

def test_alert_field_verification_request_and_submit():
    engine = AlertEngine()
    # 1. Analyst requests field verification
    inc = engine.execute_review_action(
        alert_id="ALT-REV-03",
        action=OperatorAction.REQUEST_FIELD_VERIFICATION,
        operator_id="Field Analyst 05",
        operator_role=UserRole.ANALYST,
        reason="Inspect physical staff gauge reading",
        field_notes="Dispatched team to Mundali weir"
    )
    assert inc.field_verification_status == "FIELD_VERIFICATION_REQUIRED"
    assert inc.field_verification_notes == "Dispatched team to Mundali weir"

    # 2. Operator submits verified field gauge data
    inc_sub = engine.execute_review_action(
        alert_id="ALT-REV-03",
        action=OperatorAction.SUBMIT_FIELD_VERIFICATION,
        operator_id="Field Officer 12",
        operator_role=UserRole.OPERATOR,
        reason="Staff gauge reads 26.15m (below danger mark)",
        field_notes="Verified by ODRAF team on site"
    )
    assert inc_sub.field_verification_status == "FIELD_VERIFICATION_RECEIVED"
    assert "Verified by ODRAF" in inc_sub.field_verification_notes
