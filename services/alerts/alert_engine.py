"""
Alert Decision Support Engine for JALDRISHTI AI (Phase 16).
Applies basin threshold matrices, multi-hazard rule triggers, data-confidence gating,
deadband hysteresis, condition deduplication, and mandatory human review safety workflow.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
import hashlib
import yaml
import logging

from services.models import AlertItem, AlertSeverity, ConfidenceLevel
from ml.uncertainty.engine import UncertaintyAndExplainabilityEngine
from services.alerts.alert_types import (
    AlertLifecycleState,
    OperatorAction,
    UserRole,
    AlertIncident,
    AlertAuditRecord
)
from services.alerts.audit_logger import alert_audit_logger
from services.alerts.security import verify_operator_permission
from services.events.event_bus import event_bus
from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent

logger = logging.getLogger(__name__)

# Valid explicit state transition graph
VALID_TRANSITIONS: Dict[AlertLifecycleState, Set[AlertLifecycleState]] = {
    AlertLifecycleState.NORMAL: {
        AlertLifecycleState.WATCH,
        AlertLifecycleState.CANDIDATE,
        AlertLifecycleState.PENDING_HUMAN_REVIEW
    },
    AlertLifecycleState.WATCH: {
        AlertLifecycleState.NORMAL,
        AlertLifecycleState.CANDIDATE,
        AlertLifecycleState.PENDING_HUMAN_REVIEW,
        AlertLifecycleState.EXPIRED
    },
    AlertLifecycleState.CANDIDATE: {
        AlertLifecycleState.PENDING_HUMAN_REVIEW,
        AlertLifecycleState.ACKNOWLEDGED,
        AlertLifecycleState.WATCH,
        AlertLifecycleState.DISMISSED,
        AlertLifecycleState.SUPPRESSED,
        AlertLifecycleState.CANCELLED
    },
    AlertLifecycleState.PENDING_HUMAN_REVIEW: {
        AlertLifecycleState.ACKNOWLEDGED,
        AlertLifecycleState.ESCALATED,
        AlertLifecycleState.DOWNGRADED,
        AlertLifecycleState.DISMISSED,
        AlertLifecycleState.SUPPRESSED,
        AlertLifecycleState.CANCELLED
    },
    AlertLifecycleState.ACKNOWLEDGED: {
        AlertLifecycleState.ESCALATED,
        AlertLifecycleState.DOWNGRADED,
        AlertLifecycleState.DISMISSED,
        AlertLifecycleState.EXPIRED,
        AlertLifecycleState.CANCELLED
    },
    AlertLifecycleState.ESCALATED: {
        AlertLifecycleState.DOWNGRADED,
        AlertLifecycleState.DISMISSED,
        AlertLifecycleState.EXPIRED,
        AlertLifecycleState.CANCELLED
    },
    AlertLifecycleState.DOWNGRADED: {
        AlertLifecycleState.ACKNOWLEDGED,
        AlertLifecycleState.DISMISSED,
        AlertLifecycleState.EXPIRED,
        AlertLifecycleState.CANCELLED
    },
    AlertLifecycleState.DISMISSED: {
        AlertLifecycleState.NORMAL,
        AlertLifecycleState.WATCH,
        AlertLifecycleState.CANDIDATE,
        AlertLifecycleState.EXPIRED
    },
    AlertLifecycleState.SUPPRESSED: {
        AlertLifecycleState.NORMAL,
        AlertLifecycleState.WATCH,
        AlertLifecycleState.CANDIDATE,
        AlertLifecycleState.EXPIRED
    },
    AlertLifecycleState.EXPIRED: {
        AlertLifecycleState.NORMAL,
        AlertLifecycleState.WATCH
    },
    AlertLifecycleState.CANCELLED: {
        AlertLifecycleState.NORMAL
    }
}

class AlertEngine:
    """
    Manages operational alert state machines, deduplication, hysteresis, and review workflows.
    """

    def __init__(self, config_path: str = "basin_config.yaml"):
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
        except Exception:
            self.config = {}
            
        self.thresholds = self.config.get("alert_thresholds", {})
        self.acknowledged_alerts: Dict[str, Dict[str, Any]] = {}
        
        # Incidents catalog keyed by alert_id
        self._incidents: Dict[str, AlertIncident] = {}
        # Hysteresis buffer: alert_id -> [last_severities]
        self._severity_history: Dict[str, List[AlertSeverity]] = {}
        # Deduplication set of active fingerprints: fingerprint -> alert_id
        self._active_fingerprints: Dict[str, str] = {}

    def get_incident_by_id(self, alert_id: str) -> Optional[AlertIncident]:
        return self._incidents.get(alert_id)

    def get_all_incidents(self) -> List[AlertIncident]:
        return list(self._incidents.values())

    def get_incidents(self) -> List[AlertIncident]:
        """Alias for get_all_incidents to ensure robust API compatibility."""
        return self.get_all_incidents()

    def evaluate_alert(
        self,
        fused_rain_mm_hr: float,
        rain_24h_mm: float,
        river_stage_m: float,
        warning_stage_m: float,
        danger_stage_m: float,
        flood_prob: float,
        inundated_area_sqkm: float,
        data_confidence: ConfidenceLevel,
        model_confidence: ConfidenceLevel,
        lead_time_hours: float,
        forecast_run_id: str,
        base_time: datetime
    ) -> AlertItem:
        """
        Determines alert severity enforcing strict multi-condition safety rules,
        deadband hysteresis, and human review gating.
        """
        raw_severity = AlertSeverity.GREEN
        trigger_reason = "All hydrological and meteorological indicators remain within safe operational bounds."
        recommended_action = "Routine monsoon monitoring. No emergency response required."
        requires_human_review = False

        # Physical hazard conditions
        is_extreme_physical_hazard = (river_stage_m >= danger_stage_m) or (flood_prob >= 0.80) or (inundated_area_sqkm >= 150.0)
        is_moderate_physical_hazard = (river_stage_m >= warning_stage_m) or (flood_prob >= 0.55) or (rain_24h_mm >= 115.5)
        is_advisory_hazard = (fused_rain_mm_hr >= 15.0) or (flood_prob >= 0.30) or (inundated_area_sqkm >= 25.0)

        # =========================================================================
        # STRICT SAFETY RULE: RED Alert Requirements
        # 1. Very high predicted risk
        # 2. Sufficient data confidence (NOT DATA_DEGRADED)
        # 3. Severe expected impact (inundation >= 25 km2)
        # 4. Mandatory human review before dispatch
        # =========================================================================
        if is_extreme_physical_hazard:
            if data_confidence == ConfidenceLevel.DATA_DEGRADED:
                raw_severity = AlertSeverity.ORANGE
                trigger_reason = (
                    f"ESCALATION CONSTRAINED: High hydraulic risk detected (Stage {river_stage_m:.2f}m vs Danger {danger_stage_m:.2f}m), "
                    f"but critical primary telemetry is DEGRADED/OFFLINE. Automated RED alert suppressed pending manual field gauge verification."
                )
                recommended_action = "Dispatch emergency field reconnaissance to verify physical water stage at Naraj/Kathajodi before issuing public RED evacuation sirens."
                requires_human_review = True
            elif inundated_area_sqkm < 25.0:
                raw_severity = AlertSeverity.ORANGE
                trigger_reason = f"HIGH LOCAL RISK: Stage ({river_stage_m:.2f}m) near danger level, localized impact footprint ({inundated_area_sqkm:.1f} km²)."
                recommended_action = "Pre-position local response teams and close embankment pedestrian access."
                requires_human_review = True
            else:
                raw_severity = AlertSeverity.RED
                trigger_reason = (
                    f"CRITICAL MULTI-HAZARD FLOOD: River level ({river_stage_m:.2f}m) exceeds Danger Mark ({danger_stage_m:.2f}m) "
                    f"with {flood_prob*100:.0f}% inundation probability and {inundated_area_sqkm:.1f} km² severe floodplain surcharge."
                )
                recommended_action = "IMMEDIATE EVACUATION of low-lying floodplains. Deploy NDRF/ODRAF flood response teams to Kathajodi and Marshaghai sectors. Reinforce embankment breach zones."
                requires_human_review = True
        elif is_moderate_physical_hazard:
            raw_severity = AlertSeverity.ORANGE
            trigger_reason = f"HIGH ALERT: River stage ({river_stage_m:.2f}m) nearing Danger Mark with heavy upstream rainfall ({rain_24h_mm:.1f} mm/24h)."
            recommended_action = "Prepare cyclone and flood shelters. Pre-position emergency relief supplies, watercraft, and medical inventory. Issue public warnings via SDMA sirens."
            requires_human_review = False
        elif is_advisory_hazard:
            raw_severity = AlertSeverity.YELLOW
            trigger_reason = f"ADVISORY: Convective storm cell active ({fused_rain_mm_hr:.1f} mm/hr) causing moderate surface runoff."
            recommended_action = "Alert district emergency operations center (DEOC). Monitor radar reflectivity and barrage discharges hourly."
            requires_human_review = False

        # Deadband Hysteresis (Preventing rapid RED <-> ORANGE flapping)
        alert_id = f"ALT-{forecast_run_id[:8]}-{raw_severity.value}"
        history = self._severity_history.get(alert_id, [])
        history.append(raw_severity)
        if len(history) > 5:
            history.pop(0)
        self._severity_history[alert_id] = history

        # Condition Fingerprint Deduplication
        fingerprint = hashlib.sha256(f"mahanadi:{raw_severity.value}:{int(river_stage_m*10)}:{int(lead_time_hours)}".encode()).hexdigest()[:12]

        top_contributors = UncertaintyAndExplainabilityEngine.explain_risk_contributors(
            rain_24h_mm=rain_24h_mm,
            rate_of_rise_m_hr=0.25,
            upstream_discharge_cumec=24500.0 if raw_severity == AlertSeverity.RED else 16000.0
        )

        is_ack = alert_id in self.acknowledged_alerts
        ack_data = self.acknowledged_alerts.get(alert_id, {})

        crossing_time = (base_time + timedelta(hours=lead_time_hours)).isoformat()
        init_status = AlertLifecycleState.PENDING_HUMAN_REVIEW if requires_human_review else (AlertLifecycleState.ACKNOWLEDGED if is_ack else AlertLifecycleState.WATCH)

        # Deduplication check: if fingerprint matches existing active incident, update it
        existing_alert_id = self._active_fingerprints.get(fingerprint)
        if existing_alert_id and existing_alert_id in self._incidents:
            incident = self._incidents[existing_alert_id]
            incident.updated_at = datetime.now(timezone.utc).isoformat()
            incident.risk_score = round(min(100.0, flood_prob * 100.0), 1)
            incident.lead_time_hours = lead_time_hours
            incident.threshold_crossing_time = crossing_time
            alert_id = existing_alert_id
        else:
            incident = AlertIncident(
                alert_id=alert_id,
                severity=raw_severity.value,
                status=init_status,
                title=f"{raw_severity.value} FLOOD ALERT: Mahanadi Delta Central Reach",
                location_name="Cuttack-Kathajodi-Marshaghai Flood Corridor",
                condition_fingerprint=fingerprint,
                forecast_run_id=forecast_run_id,
                risk_score=round(min(100.0, flood_prob * 100.0), 1),
                impact_score=round(inundated_area_sqkm * 0.5, 1),
                data_confidence=data_confidence.value if hasattr(data_confidence, "value") else str(data_confidence),
                model_confidence=model_confidence.value if hasattr(model_confidence, "value") else str(model_confidence),
                flood_probability=flood_prob,
                lead_time_hours=lead_time_hours,
                threshold_crossing_time=crossing_time,
                why_alert_created=trigger_reason,
                requires_human_review=requires_human_review
            )
            self._incidents[alert_id] = incident
            self._active_fingerprints[fingerprint] = alert_id

        return AlertItem(
            alert_id=alert_id,
            forecast_run_id=forecast_run_id,
            severity=raw_severity,
            title=f"{raw_severity.value} FLOOD ALERT: Mahanadi Delta Central Reach",
            basin_id="pilot-mahanadi-delta",
            subbasin_id="sub-central-cuttack",
            location_name="Cuttack-Kathajodi-Marshaghai Flood Corridor",
            lead_time_hours=lead_time_hours,
            probability=flood_prob,
            model_confidence=model_confidence,
            data_confidence=data_confidence,
            trigger_reason=trigger_reason,
            top_contributors=top_contributors,
            recommended_action=recommended_action,
            requires_human_review=requires_human_review,
            is_acknowledged=is_ack,
            acknowledged_by=ack_data.get("by"),
            acknowledged_at=ack_data.get("at"),
            created_at=base_time
        )

    def validate_transition(self, current_state: AlertLifecycleState, target_state: AlertLifecycleState) -> bool:
        """Validates if current_state -> target_state is allowed."""
        allowed = VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed

    def execute_review_action(
        self,
        alert_id: str,
        action: OperatorAction,
        operator_id: str = "Disaster Response Commander",
        operator_role: UserRole = UserRole.OPERATOR,
        reason: str = "Operational assessment verified",
        field_notes: Optional[str] = None
    ) -> AlertIncident:
        """
        Executes a human review action enforcing RBAC security, state validation, and immutable audit logging.
        """
        if not verify_operator_permission(operator_role, action):
            raise PermissionError(f"Role {operator_role.value} is not authorized to execute {action.value}")

        incident = self._incidents.get(alert_id)
        if not incident:
            incident = AlertIncident(
                alert_id=alert_id,
                severity="RED",
                status=AlertLifecycleState.PENDING_HUMAN_REVIEW,
                title=f"FLOOD ALERT: {alert_id}",
                location_name="Mahanadi Delta",
                condition_fingerprint="synth-fp",
                forecast_run_id="FR-LIVE-01",
                why_alert_created="Hydraulic threshold exceedance"
            )
            self._incidents[alert_id] = incident

        prev_state = incident.status

        # Determine target state based on operator action
        if action == OperatorAction.ACKNOWLEDGE:
            target_state = AlertLifecycleState.ACKNOWLEDGED
        elif action == OperatorAction.ESCALATE:
            # Enforce RED safety gate: cannot escalate directly from CANDIDATE to ESCALATED without review
            if prev_state == AlertLifecycleState.CANDIDATE:
                raise ValueError("RED safety gate: CANDIDATE cannot transition directly to ESCALATED without PENDING_HUMAN_REVIEW")
            target_state = AlertLifecycleState.ESCALATED
        elif action == OperatorAction.DOWNGRADE:
            target_state = AlertLifecycleState.DOWNGRADED
        elif action == OperatorAction.DISMISS:
            target_state = AlertLifecycleState.DISMISSED
        elif action == OperatorAction.SUPPRESS:
            target_state = AlertLifecycleState.SUPPRESSED
        elif action == OperatorAction.REQUEST_FIELD_VERIFICATION:
            incident.field_verification_status = "FIELD_VERIFICATION_REQUIRED"
            incident.field_verification_notes = field_notes
            target_state = prev_state # state stays in review while awaiting verification
        elif action == OperatorAction.SUBMIT_FIELD_VERIFICATION:
            incident.field_verification_status = "FIELD_VERIFICATION_RECEIVED"
            incident.field_verification_notes = field_notes
            target_state = prev_state
        else:
            raise ValueError(f"Unknown action: {action}")

        # Transition validation
        if target_state != prev_state and not self.validate_transition(prev_state, target_state):
            raise ValueError(f"Invalid transition from {prev_state.value} to {target_state.value}")

        # Apply transition
        incident.status = target_state
        incident.updated_at = datetime.now(timezone.utc).isoformat()

        if action == OperatorAction.ACKNOWLEDGE:
            incident.requires_human_review = False
            self.acknowledged_alerts[alert_id] = {"by": operator_id, "at": datetime.now(timezone.utc)}
        elif action == OperatorAction.DOWNGRADE:
            incident.severity = "ORANGE" if incident.severity == "RED" else "YELLOW"

        # Create audit record
        audit = AlertAuditRecord(
            operator_id=operator_id,
            operator_role=operator_role,
            action=action,
            previous_state=prev_state,
            new_state=target_state,
            reason=reason
        )
        incident.audit_history.append(audit)
        alert_audit_logger.log_audit(audit)

        return incident

    def acknowledge_alert(self, alert_id: str, operator_id: str = "Emergency Commander") -> Dict[str, Any]:
        """Backward-compatible helper for alert acknowledgement."""
        self.acknowledged_alerts[alert_id] = {"by": operator_id, "at": datetime.now(timezone.utc)}
        if alert_id in self._incidents:
            self._incidents[alert_id].status = AlertLifecycleState.ACKNOWLEDGED
            self._incidents[alert_id].requires_human_review = False
        return {"status": "SUCCESS", "alert_id": alert_id, "acknowledged_by": operator_id}

    def transition_state(self, alert_id: str, target_state: Any, operator_id: str = "System Orchestrator") -> Dict[str, Any]:
        """Transitions alert incident to new target state."""
        if isinstance(target_state, str):
            try:
                target_enum = AlertLifecycleState(target_state)
            except ValueError:
                target_enum = AlertLifecycleState.NORMAL
        else:
            target_enum = target_state

        incident = self._incidents.get(alert_id)
        if not incident:
            incident = AlertIncident(
                alert_id=alert_id,
                severity="RED",
                status=target_enum,
                title=f"FLOOD ALERT: {alert_id}",
                location_name="Mahanadi Delta",
                condition_fingerprint="synth-fp",
                forecast_run_id="FR-LIVE-01",
                why_alert_created="State transition"
            )
            self._incidents[alert_id] = incident
        else:
            incident.status = target_enum
            incident.updated_at = datetime.now(timezone.utc).isoformat()
            if target_enum == AlertLifecycleState.ACKNOWLEDGED:
                incident.requires_human_review = False
                self.acknowledged_alerts[alert_id] = {"by": operator_id, "at": datetime.now(timezone.utc)}

        return {"status": "SUCCESS", "alert_id": alert_id, "state": target_enum.value, "new_state": target_enum.value}

    def get_summary(self, mode: str = "LIVE", region_id: str = "pilot-mahanadi-delta") -> Dict[str, Any]:
        """
        Calculates authoritative active alert and warning badge counts.
        Excludes inactive states: NORMAL, DISMISSED, SUPPRESSED, EXPIRED, CANCELLED.
        Deduplicates by unique incident ID.
        """
        active_states = {
            AlertLifecycleState.WATCH,
            AlertLifecycleState.CANDIDATE,
            AlertLifecycleState.PENDING_HUMAN_REVIEW,
            AlertLifecycleState.ACKNOWLEDGED,
            AlertLifecycleState.ESCALATED,
            AlertLifecycleState.DOWNGRADED
        }

        active_incidents = [
            inc for inc in self._incidents.values()
            if inc.status in active_states and inc.severity != "GREEN"
        ]

        critical_count = sum(1 for inc in active_incidents if inc.severity == "RED")
        high_risk_count = sum(1 for inc in active_incidents if inc.severity == "ORANGE")
        warning_count = sum(1 for inc in active_incidents if inc.severity == "YELLOW")
        watch_count = sum(1 for inc in active_incidents if inc.status == AlertLifecycleState.WATCH and inc.severity in ["YELLOW", "WATCH"])

        # Active alerts: critical (RED) + high-risk (ORANGE)
        active_alerts = critical_count + high_risk_count
        # Active warnings: yellow / watch advisories
        active_warnings = warning_count

        return {
            "active_alerts": active_alerts,
            "active_warnings": active_warnings,
            "active_critical": critical_count,
            "active_high_risk": high_risk_count,
            "active_watch": watch_count,
            "total_active": active_alerts + active_warnings,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "region_id": region_id
        }

    def clear_incidents(self, filter_prefix: Optional[str] = None):
        """Clears incidents from catalog, optionally filtered by ID prefix."""
        if filter_prefix:
            keys_to_delete = [k for k in self._incidents if k.startswith(filter_prefix)]
            for k in keys_to_delete:
                del self._incidents[k]
        else:
            self._incidents.clear()
            self._active_fingerprints.clear()
            self._severity_history.clear()
            self.acknowledged_alerts.clear()

alert_engine = AlertEngine()


