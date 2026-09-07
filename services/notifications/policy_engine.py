"""
Notification Policy & Anti-Spam Deduplication Engine for JALDRISHTI AI.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import hashlib
import logging

from services.notifications.notification_types import (
    NotificationChannel,
    NotificationSeverityPolicy,
    UserPreferences,
    User,
    LocationSubscription
)

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {
    NotificationSeverityPolicy.INFO: 0,
    NotificationSeverityPolicy.WATCH: 1,
    NotificationSeverityPolicy.WARNING: 2,
    NotificationSeverityPolicy.HIGH_RISK: 3,
    NotificationSeverityPolicy.CRITICAL: 4,
    NotificationSeverityPolicy.RESOLVED: 1
}

# Channel eligibility matrix by severity
CHANNEL_ROUTING_MATRIX = {
    NotificationSeverityPolicy.INFO: [NotificationChannel.IN_APP],
    NotificationSeverityPolicy.WATCH: [NotificationChannel.IN_APP, NotificationChannel.PUSH],
    NotificationSeverityPolicy.WARNING: [NotificationChannel.IN_APP, NotificationChannel.PUSH, NotificationChannel.SMS],
    NotificationSeverityPolicy.HIGH_RISK: [NotificationChannel.IN_APP, NotificationChannel.PUSH, NotificationChannel.SMS],
    NotificationSeverityPolicy.CRITICAL: [NotificationChannel.IN_APP, NotificationChannel.PUSH, NotificationChannel.SMS],
    NotificationSeverityPolicy.RESOLVED: [NotificationChannel.IN_APP, NotificationChannel.PUSH]
}

class PolicyEngine:
    """
    Enforces notification anti-spam fingerprinting, channel routing, and minimum severity policies.
    """

    def __init__(self, cooldown_minutes: int = 45):
        self.cooldown_minutes = cooldown_minutes
        # Fingerprint registry: fingerprint -> last_sent_timestamp
        self._sent_fingerprints: Dict[str, datetime] = {}
        # User notification history: (user_id, subscription_id) -> last_severity
        self._user_incident_state: Dict[Tuple[str, str], NotificationSeverityPolicy] = {}

    @staticmethod
    def generate_fingerprint(
        alert_id: str,
        severity: NotificationSeverityPolicy,
        locality: str,
        hazard: str = "FLOOD"
    ) -> str:
        """Creates deterministic anti-spam fingerprint."""
        raw = f"{alert_id}:{severity.value}:{locality.lower()}:{hazard}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def evaluate_channel_eligibility(
        self,
        user: User,
        subscription: LocationSubscription,
        severity: NotificationSeverityPolicy
    ) -> List[NotificationChannel]:
        """
        Determines which notification channels are eligible for a given user & severity.
        """
        prefs = subscription.preferences or user.global_preferences
        
        # 1. Check user minimum severity threshold (except for CRITICAL which always triggers)
        user_min_rank = SEVERITY_ORDER.get(prefs.minimum_severity, 1)
        event_rank = SEVERITY_ORDER.get(severity, 1)
        
        if event_rank < user_min_rank and severity != NotificationSeverityPolicy.CRITICAL:
            return []

        # 2. Check allowed channels for this severity level
        allowed_channels = CHANNEL_ROUTING_MATRIX.get(severity, [NotificationChannel.IN_APP])
        selected_channels = []

        if NotificationChannel.IN_APP in allowed_channels and prefs.in_app_enabled:
            selected_channels.append(NotificationChannel.IN_APP)

        if NotificationChannel.PUSH in allowed_channels and prefs.push_enabled:
            if user.fcm_device_tokens:
                selected_channels.append(NotificationChannel.PUSH)

        if NotificationChannel.SMS in allowed_channels and prefs.sms_enabled:
            # STRICT POLICY: SMS only dispatched if phone is verified
            if user.phone_verified:
                selected_channels.append(NotificationChannel.SMS)

        return selected_channels

    def check_anti_spam(
        self,
        fingerprint: str,
        user_id: str,
        subscription_id: str,
        severity: NotificationSeverityPolicy
    ) -> Tuple[bool, str]:
        """
        Checks whether a notification is allowed or blocked by anti-spam cooldown/hysteresis.
        Returns: (allowed, reason)
        """
        now = datetime.now(timezone.utc)
        user_key = (user_id, subscription_id)
        last_severity = self._user_incident_state.get(user_key)

        # If severity escalated, bypass cooldown immediately
        if last_severity:
            prev_rank = SEVERITY_ORDER.get(last_severity, 0)
            curr_rank = SEVERITY_ORDER.get(severity, 0)
            if curr_rank > prev_rank:
                self._sent_fingerprints[fingerprint] = now
                self._user_incident_state[user_key] = severity
                return True, "Escalation bypasses cooldown"

        # Check cooldown window
        if fingerprint in self._sent_fingerprints:
            last_sent = self._sent_fingerprints[fingerprint]
            if (now - last_sent) < timedelta(minutes=self.cooldown_minutes):
                return False, f"Suppressed by cooldown ({self.cooldown_minutes} min window)"

        self._sent_fingerprints[fingerprint] = now
        self._user_incident_state[user_key] = severity
        return True, "Eligible for dispatch"

# Global singleton
policy_engine = PolicyEngine()
