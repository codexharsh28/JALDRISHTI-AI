"""
Unit tests for Immutable Alert Audit Records & Event Logging (Phase 16).
"""

import pytest
from services.alerts.alert_engine import AlertEngine
from services.alerts.alert_types import OperatorAction, UserRole
from services.alerts.audit_logger import alert_audit_logger

def test_alert_audit_record_structure_and_persistence():
    engine = AlertEngine()
    
    inc = engine.execute_review_action(
        alert_id="ALT-AUD-01",
        action=OperatorAction.ACKNOWLEDGE,
        operator_id="Op-77",
        operator_role=UserRole.OPERATOR,
        reason="Hydrometric cross-check verified"
    )

    assert len(inc.audit_history) == 1
    rec = inc.audit_history[0]
    assert rec.operator_id == "Op-77"
    assert rec.action == OperatorAction.ACKNOWLEDGE
    assert rec.reason == "Hydrometric cross-check verified"
    assert rec.timestamp is not None
