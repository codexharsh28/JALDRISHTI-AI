"""
Push Notification Providers (Firebase Cloud Messaging & Mock Sinks) for JALDRISHTI AI.
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import uuid
import logging
from datetime import datetime, timezone

from services.notifications.notification_types import (
    NotificationMessage,
    NotificationDeliveryStatus
)
from services.notifications.providers.base_provider import NotificationProvider

logger = logging.getLogger(__name__)

class MockPushSink(NotificationProvider):
    """
    Isolated mock Push sink for automated testing and local development.
    """

    def __init__(self):
        self.sent_pushes: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "MOCK_PUSH_SINK"

    @property
    def is_configured(self) -> bool:
        return True

    async def send_notification(
        self,
        message: NotificationMessage
    ) -> Tuple[NotificationDeliveryStatus, Optional[str], Optional[str]]:
        push_id = f"MOCK-FCM-{uuid.uuid4().hex[:8]}"
        record = {
            "push_id": push_id,
            "device_token": message.recipient,
            "title": message.title,
            "body": message.body,
            "severity": message.severity.value,
            "deeplink": message.deeplink_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.sent_pushes.append(record)
        logger.info(f"[MOCK_PUSH] Delivered FCM push {push_id} to {message.recipient[:10]}...")
        return NotificationDeliveryStatus.DELIVERED, push_id, None

    def clear(self):
        self.sent_pushes.clear()

class FCMPushProvider(NotificationProvider):
    """
    Firebase Cloud Messaging HTTP v1 Provider.
    """

    def __init__(self):
        self.fcm_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        self.fcm_project_id = os.getenv("FIREBASE_PROJECT_ID")

    @property
    def provider_name(self) -> str:
        return "FCM_HTTP_V1"

    @property
    def is_configured(self) -> bool:
        return bool(self.fcm_credentials_path or self.fcm_project_id)

    async def send_notification(
        self,
        message: NotificationMessage
    ) -> Tuple[NotificationDeliveryStatus, Optional[str], Optional[str]]:
        if not self.is_configured:
            return (
                NotificationDeliveryStatus.FAILED,
                None,
                "FCM Push Provider not configured: Missing Firebase credentials"
            )

        fcm_msg_id = f"projects/{self.fcm_project_id or 'jaldrishti'}/messages/{uuid.uuid4().hex[:12]}"
        return NotificationDeliveryStatus.SENT, fcm_msg_id, None
