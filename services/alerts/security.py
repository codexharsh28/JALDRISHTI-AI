"""
Role-Based Access Control (RBAC) Security Verification for Alert Decisions (Phase 16).
Ensures only authorized disaster management operators can acknowledge, escalate, or dismiss alerts.
"""

from typing import Dict, Any, Optional
import logging
from services.alerts.alert_types import UserRole, OperatorAction

logger = logging.getLogger(__name__)

# Action permissions matrix
ALLOWED_PERMISSIONS = {
    UserRole.VIEWER: [],
    UserRole.ANALYST: [
        OperatorAction.REQUEST_FIELD_VERIFICATION
    ],
    UserRole.OPERATOR: [
        OperatorAction.ACKNOWLEDGE,
        OperatorAction.ESCALATE,
        OperatorAction.DOWNGRADE,
        OperatorAction.DISMISS,
        OperatorAction.REQUEST_FIELD_VERIFICATION,
        OperatorAction.SUBMIT_FIELD_VERIFICATION
    ],
    UserRole.ADMIN: [
        OperatorAction.ACKNOWLEDGE,
        OperatorAction.ESCALATE,
        OperatorAction.DOWNGRADE,
        OperatorAction.DISMISS,
        OperatorAction.SUPPRESS,
        OperatorAction.REQUEST_FIELD_VERIFICATION,
        OperatorAction.SUBMIT_FIELD_VERIFICATION
    ],
    UserRole.ADMINISTRATOR: [
        OperatorAction.ACKNOWLEDGE,
        OperatorAction.ESCALATE,
        OperatorAction.DOWNGRADE,
        OperatorAction.DISMISS,
        OperatorAction.SUPPRESS,
        OperatorAction.REQUEST_FIELD_VERIFICATION,
        OperatorAction.SUBMIT_FIELD_VERIFICATION
    ]
}

def verify_operator_permission(role: UserRole, action: OperatorAction) -> bool:
    """Verifies whether the given role is authorized to execute the action."""
    allowed = ALLOWED_PERMISSIONS.get(role, [])
    return action in allowed
