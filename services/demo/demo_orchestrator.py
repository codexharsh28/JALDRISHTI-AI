"""
Central Demo Orchestrator for JALDRISHTI AI.
Executes the deterministic 14-stage end-to-end scenario across all platform subsystems,
propagating monotonic events through the EventBus and triggering geofenced mock alerts.
"""

from typing import Dict, Any, Optional
import threading
import logging
from datetime import datetime, timezone

from services.demo.demo_scenario import DEMO_SCENARIO_STAGES, DemoScenarioStage
from services.demo.demo_state import DemoState
from services.events.event_schema import OperationalEvent
from services.events.event_store import event_store
from services.events.event_types import EventType, EventPriority
from services.notifications.user_store import user_store
from services.notifications.notification_queue import notification_queue
from services.notifications.notification_types import (
    NotificationMessage,
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationProvenance,
    NotificationSeverityPolicy
)
from services.models import AlertSeverity

logger = logging.getLogger(__name__)

class DemoOrchestrator:
    """
    Central state machine and driver for the 14-stage demonstration scenario.
    """

    def __init__(self):
        self.state = DemoState()
        self._lock = threading.RLock()
        self._timer: Optional[threading.Timer] = None
        self.seed_mock_citizens()

    def seed_mock_citizens(self):
        """
        Seeds two mock citizens:
        1. DEMO USER (Inside Cuttack flood polygon, registered for SMS & Push)
        2. OUTSIDE USER (Outside flood polygon in Sundargarh/Rourkela)
        """
        try:
            # 1. Affected User in Cuttack (20.4625, 85.8830)
            u1 = user_store.register_user(phone_number="9800000001", preferred_language="or")
            user_store.add_subscription(
                user_id=u1.user_id,
                label="HOME",
                locality_name="Cuttack Delta Floodplain",
                latitude=20.4625,
                longitude=85.8830,
                radius_km=15.0
            )

            # 2. Outside User in Sundargarh (22.1200, 84.0300)
            u2 = user_store.register_user(phone_number="9800000002", preferred_language="en")
            user_store.add_subscription(
                user_id=u2.user_id,
                label="HOME",
                locality_name="Sundargarh Reach",
                latitude=22.1200,
                longitude=84.0300,
                radius_km=10.0
            )
            logger.info("Demo mock citizens successfully initialized in UserStore.")
        except Exception as e:
            logger.warning(f"Mock citizens initialization notice: {e}")

    def start_demo(self) -> Dict[str, Any]:
        """Starts or restarts the DEMO-MAHANADI-STORM-01 scenario at T0."""
        with self._lock:
            self.state.is_active = True
            self.state.is_playing = True
            self.state.current_step = 0
            self.state.operator_review_acknowledged = False
            self.state.affected_citizen_notified = False
            self.state.outside_citizen_excluded = True
            self.state.last_step_advanced_at = datetime.now(timezone.utc)
            self._dispatch_stage_events(self.state.current_stage)
            return self.state.to_dict()

    def pause_demo(self) -> Dict[str, Any]:
        """Pauses the automatic clock advancement."""
        with self._lock:
            self.state.is_playing = False
            if self._timer:
                self._timer.cancel()
            return self.state.to_dict()

    def resume_demo(self) -> Dict[str, Any]:
        """Resumes automatic clock advancement."""
        with self._lock:
            self.state.is_playing = True
            self.state.last_step_advanced_at = datetime.now(timezone.utc)
            return self.state.to_dict()

    def step_forward(self) -> Dict[str, Any]:
        """Advances the scenario to the next stage."""
        with self._lock:
            if self.state.current_step < len(DEMO_SCENARIO_STAGES) - 1:
                self.state.current_step += 1
                self.state.last_step_advanced_at = datetime.now(timezone.utc)
                next_stg = self.state.current_stage
                if next_stg.requires_operator_review:
                    self.state.operator_review_acknowledged = False
                self._dispatch_stage_events(next_stg)
            return self.state.to_dict()

    def step_backward(self) -> Dict[str, Any]:
        """Steps back to the previous stage."""
        with self._lock:
            if self.state.current_step > 0:
                self.state.current_step -= 1
                self.state.last_step_advanced_at = datetime.now(timezone.utc)
                prev_stg = self.state.current_stage
                if prev_stg.requires_operator_review:
                    self.state.operator_review_acknowledged = False
                self._dispatch_stage_events(prev_stg)
            return self.state.to_dict()

    def reset_demo(self) -> Dict[str, Any]:
        """Resets the demo scenario state completely and clears demo alert incidents."""
        with self._lock:
            self.state.is_active = False
            self.state.is_playing = False
            self.state.current_step = 0
            self.state.operator_review_acknowledged = False
            self.state.affected_citizen_notified = False
            self.state.outside_citizen_excluded = True
            try:
                from services.alerts.alert_engine import alert_engine
                alert_engine.clear_incidents("ALT-DEMO")
            except Exception:
                pass
            try:
                from services.risk.risk_store import risk_store
                risk_store.clear_demo_states()
            except Exception:
                pass
            return self.state.to_dict()

    def acknowledge_operator_gate(self) -> Dict[str, Any]:
        """Acknowledges the human operator review gate for high-risk alerts."""
        with self._lock:
            self.state.operator_review_acknowledged = True
            stage = self.state.current_stage
            self._dispatch_mock_notifications(stage)
            return self.state.to_dict()

    def set_speed(self, speed: float) -> Dict[str, Any]:
        """Sets the scenario playback multiplier."""
        with self._lock:
            self.state.playback_speed = max(0.5, min(10.0, float(speed)))
            return self.state.to_dict()

    def get_status(self) -> Dict[str, Any]:
        """Returns the current state snapshot."""
        with self._lock:
            return self.state.to_dict()

    def _dispatch_stage_events(self, stage: DemoScenarioStage):
        """
        Dispatches causal events to the event store for the given stage.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # 1. Rainfall observation & fusion events
        ev1 = OperationalEvent.create(
            event_type=EventType.RAIN_OBSERVATION_UPDATED,
            source_id="DEMO_RADAR_AWS_FUSION",
            provider="DEMO_PRECIP_ENGINE",
            data={
                "source": "DEMO_RADAR_AWS_FUSION",
                "mean_rate_mm_hr": stage.rainfall_rate_mm_hr,
                "acc_6h_mm": stage.rainfall_acc_6h_mm,
                "stage": stage.name,
                "timestamp": now_iso
            },
            mode="SIMULATION",
            data_state="SYNTHETIC",
            priority=EventPriority.NORMAL
        )
        event_store.append(ev1)

        # 2. Hydrology / River Update
        ev2 = OperationalEvent.create(
            event_type=EventType.RIVER_OBSERVATION_UPDATED,
            source_id="CWC_MUNDALI",
            provider="CWC_TELEMETRY",
            data={
                "station_id": "CWC_MUNDALI",
                "stage_m": stage.river_stage_m,
                "discharge_cumec": stage.river_discharge_cumec,
                "rate_of_rise_m_hr": 0.25 if stage.index in [3, 4, 5] else 0.05,
                "warning_level_m": 25.40,
                "danger_level_m": 26.30,
                "timestamp": now_iso
            },
            mode="SIMULATION",
            data_state="SYNTHETIC",
            priority=EventPriority.HIGH
        )
        event_store.append(ev2)

        # 3. Inundation & Impact Update
        ev3 = OperationalEvent.create(
            event_type=EventType.INUNDATION_UPDATED,
            source_id="INUNDATION_SURROGATE",
            provider="Spatial Hydraulic Surrogate",
            data={
                "inundated_area_sqkm": stage.inundated_area_sqkm,
                "max_depth_m": 1.65 if stage.index >= 7 else (0.45 if stage.index >= 4 else 0.0),
                "exposed_population": stage.exposed_population,
                "exposed_villages": stage.exposed_villages,
                "timestamp": now_iso
            },
            mode="SIMULATION",
            data_state="SYNTHETIC",
            priority=EventPriority.HIGH
        )
        event_store.append(ev3)

        # 4. Risk State Shift
        ev4 = OperationalEvent.create(
            event_type=EventType.RISK_STATE_CHANGED,
            source_id="RISK_ENGINE",
            provider="Multi-Source Causal Decomposition",
            data={
                "risk_score": stage.risk_score,
                "previous_risk_score": stage.previous_risk_score,
                "material_risk_delta": stage.material_risk_delta,
                "risk_level": stage.alert_severity.value,
                "top_causal_driver": stage.top_causal_driver,
                "timestamp": now_iso
            },
            mode="SIMULATION",
            data_state="SYNTHETIC",
            priority=EventPriority.HIGH
        )
        event_store.append(ev4)

        # 5. Alert Trigger & Dispatch if applicable
        demo_alert_id = "ALT-DEMO-MAHANADI-01"
        try:
            from services.alerts.alert_engine import alert_engine
            from services.alerts.alert_types import AlertLifecycleState
            if stage.alert_severity == AlertSeverity.GREEN:
                alert_engine.clear_incidents("ALT-DEMO")
            elif stage.alert_severity == AlertSeverity.YELLOW:
                alert_engine.transition_state(demo_alert_id, AlertLifecycleState.WATCH)
                inc = alert_engine.get_incident_by_id(demo_alert_id)
                if inc:
                    inc.severity = "YELLOW"
            elif stage.alert_severity == AlertSeverity.ORANGE:
                alert_engine.transition_state(demo_alert_id, AlertLifecycleState.CANDIDATE)
                inc = alert_engine.get_incident_by_id(demo_alert_id)
                if inc:
                    inc.severity = "ORANGE"
            elif stage.alert_severity == AlertSeverity.RED:
                stat = AlertLifecycleState.ACKNOWLEDGED if self.state.operator_review_acknowledged else AlertLifecycleState.PENDING_HUMAN_REVIEW
                alert_engine.transition_state(demo_alert_id, stat)
                inc = alert_engine.get_incident_by_id(demo_alert_id)
                if inc:
                    inc.severity = "RED"
        except Exception:
            pass

        if stage.alert_severity in [AlertSeverity.ORANGE, AlertSeverity.RED]:
            ev5 = OperationalEvent.create(
                event_type=EventType.ALERT_CANDIDATE_CREATED,
                source_id="ALERT_GATE",
                provider="JALDRISHTI Early Warning Engine",
                data={
                    "alert_id": f"ALT-DEMO-{stage.stage_id}",
                    "severity": stage.alert_severity.value,
                    "headline": stage.headline,
                    "target_locality": "Cuttack-Mahanadi Basin Lowlands",
                    "requires_review": stage.requires_operator_review,
                    "timestamp": now_iso
                },
                mode="SIMULATION",
                data_state="SYNTHETIC",
                priority=EventPriority.CRITICAL if stage.alert_severity == AlertSeverity.RED else EventPriority.HIGH
            )
            event_store.append(ev5)

        if stage.requires_operator_review:
            if self.state.operator_review_acknowledged:
                self._dispatch_mock_notifications(stage)
        elif stage.is_notification_dispatched:
            self._dispatch_mock_notifications(stage)

    def _dispatch_mock_notifications(self, stage: DemoScenarioStage):
        """
        Dispatches targeted mock notifications demonstrating geofenced delivery.
        """
        self.state.affected_citizen_notified = True
        self.state.outside_citizen_excluded = True

        prov = NotificationProvenance(
            alert_id=f"ALT-DEMO-{stage.stage_id}",
            forecast_run_id="FR-DEMO-MAHANADI-01",
            risk_state_id=f"RSK-DEMO-{stage.stage_id}",
            template_id="TEMPL_FLASH_FLOOD_WARNING_EN",
            user_region="Cuttack-Mahanadi",
            channel=NotificationChannel.SMS
        )

        # 1. Enqueue Mock SMS for affected user in Cuttack
        msg_sms = NotificationMessage(
            notification_id=f"NOTIF-SMS-{stage.stage_id}",
            user_id="9800000001",
            channel=NotificationChannel.SMS,
            title="[MOCK SMS] JALDRISHTI AI FLOOD ALERT",
            body=f"DEMO ALERT: {stage.headline}. Stage {stage.river_stage_m}m. Move to higher ground immediately.",
            recipient="+91******0001",
            severity=NotificationSeverityPolicy.CRITICAL if stage.alert_severity == AlertSeverity.RED else NotificationSeverityPolicy.WARNING,
            locality="Cuttack Delta Lowlands",
            provenance=prov
        )
        notification_queue.mock_sms_sink.sent_messages.append({
            "message_id": f"MOCK-SMS-{stage.stage_id}",
            "recipient": msg_sms.recipient,
            "title": msg_sms.title,
            "body": msg_sms.body,
            "template_id": prov.template_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # 2. In-App Notification (Recorded in repository)
        try:
            from services.notifications.db.repositories import NotificationRepository
            NotificationRepository.record_notification(msg_sms)
        except Exception as e:
            logger.warning(f"Failed to record demo notification: {e}")
        logger.info(f"[DEMO] Targeted Mock Notification dispatched to Cuttack citizen; Outside citizen excluded.")

demo_orchestrator = DemoOrchestrator()
