"""
Public Notification Orchestration Service for JALDRISHTI AI.
Subscribes to operational alert events, fans out to subscribed users via geofencing,
and coordinates multilingual SMS, Push, and In-App delivery.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timezone
import logging

from services.notifications.notification_types import (
    User,
    LocationSubscription,
    NotificationSeverityPolicy,
    NotificationChannel,
    NotificationMessage,
    NotificationProvenance,
    GeofenceMatch
)
from services.notifications.user_store import user_store
from services.notifications.geofence_engine import geofence_engine
from services.notifications.template_engine import template_engine
from services.notifications.policy_engine import policy_engine
from services.notifications.notification_queue import notification_queue
from services.events.event_bus import event_bus
from services.events.event_types import EventType
from services.events.event_schema import OperationalEvent

logger = logging.getLogger(__name__)

# Map backend AlertSeverity / state to NotificationSeverityPolicy
SEVERITY_MAPPING = {
    "GREEN": NotificationSeverityPolicy.INFO,
    "YELLOW": NotificationSeverityPolicy.WATCH,
    "ORANGE": NotificationSeverityPolicy.WARNING,
    "RED": NotificationSeverityPolicy.CRITICAL,
    "RESOLVED": NotificationSeverityPolicy.RESOLVED
}

class NotificationService:
    """
    Coordinates public alert fanout, geofencing, template rendering, and delivery queueing.
    """

    def __init__(self):
        self._initialized = False

    def initialize(self) -> None:
        """Subscribes to domain events on the event bus."""
        if not self._initialized:
            event_bus.subscribe(EventType.ALERT_STATE_CHANGED, self._handle_alert_event)
            event_bus.subscribe(EventType.ALERT_ACKNOWLEDGED, self._handle_alert_event)
            event_bus.subscribe(EventType.ALERT_DECISION_EXECUTED, self._handle_alert_event)
            self._initialized = True
            logger.info("[NOTIFICATION_SERVICE] Initialized and subscribed to alert domain events.")

    async def _handle_alert_event(self, event: OperationalEvent) -> None:
        """Handles alert event from event bus and initiates citizen notification fanout."""
        data = event.data or {}
        alert_id = data.get("alert_id", "ALT-LIVE")
        severity_str = data.get("severity", "YELLOW")
        status_str = data.get("status", "WATCH")
        location_lat = float(data.get("lat", 20.46))
        location_lon = float(data.get("lon", 85.88))
        locality_name = data.get("location_name", "Mahanadi Delta Reach")
        data_state = data.get("data_confidence", "OBSERVED_CWC")
        forecast_run_id = data.get("forecast_run_id", event.correlation_id or "FR-LIVE")

        # STRICT HUMAN REVIEW GATE: RED alerts MUST be approved/escalated/acknowledged by an operator
        if severity_str == "RED" and status_str == "PENDING_HUMAN_REVIEW":
            logger.info(f"[NOTIFICATION_SERVICE] Suppressing public RED notification for {alert_id}: Awaiting human operator approval.")
            return

        severity_policy = SEVERITY_MAPPING.get(severity_str, NotificationSeverityPolicy.WATCH)
        if status_str == "EXPIRED" or status_str == "CANCELLED":
            severity_policy = NotificationSeverityPolicy.RESOLVED

        await self.process_alert_fanout(
            alert_id=alert_id,
            severity=severity_policy,
            hazard="RIVERINE_FLOODING",
            target_lat=location_lat,
            target_lon=location_lon,
            locality=locality_name,
            forecast_run_id=forecast_run_id,
            data_state=data_state
        )

    async def process_alert_fanout(
        self,
        alert_id: str,
        severity: NotificationSeverityPolicy,
        hazard: str,
        target_lat: float,
        target_lon: float,
        locality: str,
        forecast_run_id: str,
        data_state: str = "OBSERVED_CWC"
    ) -> int:
        """
        Fans out notification to all matching location subscriptions in the basin.
        Returns: count of notifications queued.
        """
        all_users = user_store.get_all_users()
        queued_count = 0
        is_degraded = (data_state in ["DATA_DEGRADED", "MODELED_GLOFAS", "STALE", "OFFLINE"])

        for user in all_users:
            for sub in user.subscriptions:
                # 1. Geofence evaluation
                match, dist_km = geofence_engine.evaluate_geofence_match(
                    user_lat=sub.latitude,
                    user_lon=sub.longitude,
                    target_lat=target_lat,
                    target_lon=target_lon,
                    subscription_radius_km=sub.radius_km
                )

                if match == GeofenceMatch.OUTSIDE_AREA:
                    continue

                # 2. Channel eligibility check
                channels = policy_engine.evaluate_channel_eligibility(
                    user=user,
                    subscription=sub,
                    severity=severity
                )

                if not channels:
                    continue

                # 3. Anti-spam deduplication & cooldown check
                fingerprint = policy_engine.generate_fingerprint(
                    alert_id=alert_id,
                    severity=severity,
                    locality=sub.locality_name,
                    hazard=hazard
                )
                allowed, reason = policy_engine.check_anti_spam(
                    fingerprint=fingerprint,
                    user_id=user.user_id,
                    subscription_id=sub.subscription_id,
                    severity=severity
                )

                if not allowed:
                    logger.debug(f"[NOTIFICATION_SERVICE] User {user.user_id} subscription {sub.subscription_id}: {reason}")
                    continue

                # 4. Render template in user's preferred language
                lang = (sub.preferences.preferred_language if sub.preferences else user.preferred_language) or "en"
                rendered = template_engine.render_notification(
                    severity=severity,
                    locality=sub.locality_name,
                    expected_time="next 6–12 hours",
                    language=lang,
                    data_degraded_notice=is_degraded
                )

                # 5. Enqueue message per eligible channel
                for ch in channels:
                    recipient = (
                        user.phone_number if ch == NotificationChannel.SMS else
                        (user.fcm_device_tokens[0] if user.fcm_device_tokens and ch == NotificationChannel.PUSH else user.user_id)
                    )

                    msg = NotificationMessage(
                        user_id=user.user_id,
                        subscription_id=sub.subscription_id,
                        channel=ch,
                        severity=severity,
                        title=rendered["title"],
                        body=rendered["body"],
                        recipient=recipient,
                        locality=sub.locality_name,
                        deeplink_url=f"/public-portal?alert_id={alert_id}",
                        provenance=NotificationProvenance(
                            alert_id=alert_id,
                            forecast_run_id=forecast_run_id,
                            user_region=sub.locality_name,
                            channel=ch,
                            template_id=rendered["template_id"],
                            data_state=data_state
                        )
                    )
                    await notification_queue.enqueue(msg)
                    queued_count += 1

        logger.info(f"[NOTIFICATION_SERVICE] Fanout complete for alert {alert_id} ({severity.value}): {queued_count} messages queued.")
        return queued_count

# Global singleton
notification_service = NotificationService()
