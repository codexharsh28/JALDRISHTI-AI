"""
Public Notification Subsystem for JALDRISHTI AI.
"""

from services.notifications.notification_types import (
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationSeverityPolicy,
    GeofenceMatch,
    UserPreferences,
    LocationSubscription,
    User,
    NotificationProvenance,
    NotificationMessage,
    DeliveryRecord
)
from services.notifications.user_store import UserStore, user_store
from services.notifications.geofence_engine import GeofenceEngine, geofence_engine
from services.notifications.template_engine import TemplateEngine, template_engine
from services.notifications.policy_engine import PolicyEngine, policy_engine
from services.notifications.notification_queue import NotificationQueueWorker, notification_queue
from services.notifications.notification_service import NotificationService, notification_service
from services.notifications.providers import (
    NotificationProvider,
    MockSMSSink,
    MSG91Provider,
    TwilioSMSProvider,
    MockPushSink,
    FCMPushProvider,
    InAppNotificationProvider,
    in_app_provider
)

__all__ = [
    "NotificationChannel",
    "NotificationDeliveryStatus",
    "NotificationSeverityPolicy",
    "GeofenceMatch",
    "UserPreferences",
    "LocationSubscription",
    "User",
    "NotificationProvenance",
    "NotificationMessage",
    "DeliveryRecord",
    "UserStore",
    "user_store",
    "GeofenceEngine",
    "geofence_engine",
    "TemplateEngine",
    "template_engine",
    "PolicyEngine",
    "policy_engine",
    "NotificationQueueWorker",
    "notification_queue",
    "NotificationService",
    "notification_service",
    "NotificationProvider",
    "MockSMSSink",
    "MSG91Provider",
    "TwilioSMSProvider",
    "MockPushSink",
    "FCMPushProvider",
    "InAppNotificationProvider",
    "in_app_provider"
]
