"""
Alert Decision Support Types, Roles, and Lifecycle Schemas for JALDRISHTI AI (Phase 16).
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class AlertLifecycleState(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    CANDIDATE = "CANDIDATE"
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ESCALATED = "ESCALATED"
    DOWNGRADED = "DOWNGRADED"
    DISMISSED = "DISMISSED"
    SUPPRESSED = "SUPPRESSED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class OperatorAction(str, Enum):
    ACKNOWLEDGE = "ACKNOWLEDGE"
    ESCALATE = "ESCALATE"
    DOWNGRADE = "DOWNGRADE"
    DISMISS = "DISMISS"
    SUPPRESS = "SUPPRESS"
    REQUEST_FIELD_VERIFICATION = "REQUEST_FIELD_VERIFICATION"
    SUBMIT_FIELD_VERIFICATION = "SUBMIT_FIELD_VERIFICATION"

class UserRole(str, Enum):
    VIEWER = "VIEWER"
    ANALYST = "ANALYST"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"
    ADMINISTRATOR = "ADMINISTRATOR"

class AlertAuditRecord(BaseModel):
    audit_id: str = Field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:6]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    operator_id: str
    operator_role: UserRole
    action: OperatorAction
    previous_state: AlertLifecycleState
    new_state: AlertLifecycleState
    reason: str
    evidence_snapshot_hash: Optional[str] = None

class AlertIncident(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:4]}")
    alert_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity: str # "GREEN", "YELLOW", "ORANGE", "RED"
    status: AlertLifecycleState = AlertLifecycleState.NORMAL
    hazard: str = "RIVERINE_FLOODING"
    title: str
    location_name: str
    basin_id: str = "pilot-mahanadi-delta"
    condition_fingerprint: str
    forecast_run_id: str
    inundation_run_id: Optional[str] = None
    impact_run_id: Optional[str] = None
    risk_score: float = 0.0
    impact_score: float = 0.0
    data_confidence: str = "HIGH"
    model_confidence: str = "HIGH"
    flood_probability: float = 0.0
    lead_time_hours: float = 12.0
    threshold_crossing_time: Optional[str] = None
    why_alert_created: str
    requires_human_review: bool = False
    field_verification_status: str = "NOT_REQUESTED" # "NOT_REQUESTED", "FIELD_VERIFICATION_REQUIRED", "FIELD_VERIFICATION_RECEIVED"
    field_verification_notes: Optional[str] = None
    audit_history: List[AlertAuditRecord] = Field(default_factory=list)
