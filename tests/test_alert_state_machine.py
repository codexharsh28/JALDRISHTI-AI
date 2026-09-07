"""
Unit tests for Alert Lifecycle State Machine Transitions & Rejection Rules (Phase 16).
"""

import pytest
from services.alerts.alert_types import AlertLifecycleState, OperatorAction, UserRole
from services.alerts.alert_engine import AlertEngine, VALID_TRANSITIONS

def test_valid_state_transitions():
    engine = AlertEngine()
    
    # NORMAL -> PENDING_HUMAN_REVIEW is valid
    assert engine.validate_transition(AlertLifecycleState.NORMAL, AlertLifecycleState.PENDING_HUMAN_REVIEW) is True
    # PENDING_HUMAN_REVIEW -> ACKNOWLEDGED is valid
    assert engine.validate_transition(AlertLifecycleState.PENDING_HUMAN_REVIEW, AlertLifecycleState.ACKNOWLEDGED) is True
    # ACKNOWLEDGED -> ESCALATED is valid
    assert engine.validate_transition(AlertLifecycleState.ACKNOWLEDGED, AlertLifecycleState.ESCALATED) is True
    # PENDING_HUMAN_REVIEW -> DOWNGRADED is valid
    assert engine.validate_transition(AlertLifecycleState.PENDING_HUMAN_REVIEW, AlertLifecycleState.DOWNGRADED) is True

def test_invalid_state_transitions_rejected():
    engine = AlertEngine()

    # CANCELLED cannot jump to ESCALATED
    assert engine.validate_transition(AlertLifecycleState.CANCELLED, AlertLifecycleState.ESCALATED) is False
    # EXPIRED cannot jump directly to ESCALATED
    assert engine.validate_transition(AlertLifecycleState.EXPIRED, AlertLifecycleState.ESCALATED) is False

def test_execute_review_action_invalid_transition_raises_error():
    engine = AlertEngine()
    incident = engine.execute_review_action(
        alert_id="ALT-TEST-01",
        action=OperatorAction.DISMISS,
        operator_role=UserRole.OPERATOR
    )
    assert incident.status == AlertLifecycleState.DISMISSED

    # Trying to ESCALATE directly from DISMISSED must raise ValueError
    with pytest.raises(ValueError, match="Invalid transition"):
        engine.execute_review_action(
            alert_id="ALT-TEST-01",
            action=OperatorAction.ESCALATE,
            operator_role=UserRole.OPERATOR
        )
