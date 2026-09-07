"""
Unit tests for Role-Based Access Control & Action Permissions (Phase 16).
"""

import pytest
from services.alerts.alert_engine import AlertEngine
from services.alerts.alert_types import OperatorAction, UserRole
from services.alerts.security import verify_operator_permission

def test_viewer_permission_restricted():
    assert verify_operator_permission(UserRole.VIEWER, OperatorAction.ACKNOWLEDGE) is False
    assert verify_operator_permission(UserRole.VIEWER, OperatorAction.ESCALATE) is False
    assert verify_operator_permission(UserRole.VIEWER, OperatorAction.DISMISS) is False

def test_analyst_permission_limited_to_field_verification():
    assert verify_operator_permission(UserRole.ANALYST, OperatorAction.REQUEST_FIELD_VERIFICATION) is True
    assert verify_operator_permission(UserRole.ANALYST, OperatorAction.ESCALATE) is False
    assert verify_operator_permission(UserRole.ANALYST, OperatorAction.ACKNOWLEDGE) is False

def test_operator_permission_full_review():
    assert verify_operator_permission(UserRole.OPERATOR, OperatorAction.ACKNOWLEDGE) is True
    assert verify_operator_permission(UserRole.OPERATOR, OperatorAction.ESCALATE) is True
    assert verify_operator_permission(UserRole.OPERATOR, OperatorAction.DOWNGRADE) is True
    assert verify_operator_permission(UserRole.OPERATOR, OperatorAction.DISMISS) is True

def test_admin_permission_includes_suppress():
    assert verify_operator_permission(UserRole.ADMIN, OperatorAction.SUPPRESS) is True
    assert verify_operator_permission(UserRole.ADMINISTRATOR, OperatorAction.SUPPRESS) is True

def test_unauthorized_role_raises_permission_error():
    engine = AlertEngine()
    with pytest.raises(PermissionError, match="not authorized"):
        engine.execute_review_action(
            alert_id="ALT-PERM-01",
            action=OperatorAction.ESCALATE,
            operator_role=UserRole.VIEWER
        )
