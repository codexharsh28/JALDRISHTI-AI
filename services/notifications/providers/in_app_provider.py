"""
In-App Notification Provider & Inbox Store for JALDRISHTI AI.
Persists notifications to memory and database repository.
"""

from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import threading
import uuid
import logging

from services.notifications.notification_types import (
    NotificationMessage,
    NotificationDeliveryStatus
)
from services.notifications.providers.base_provider import NotificationProvider
from services.notifications.db.repositories import NotificationRepository

logger = logging.getLogger(__name__)

class InAppNotificationProvider(NotificationProvider):
    """
    Persists in-app notifications into user inboxes and database repository.
    """

    def __init__(self, max_inbox_size: int = 100):
        self.max_inbox_size = max_inbox_size
        self._lock = threading.Lock()
        # Inboxes keyed by user_id -> deque of NotificationMessage
        self._inboxes: Dict[str, deque] = {}
        # Global notification catalog keyed by notification_id
        self._all_notifications: Dict[str, NotificationMessage] = {}

    @property
    def provider_name(self) -> str:
        return "IN_APP_INBOX_STORE"

    @property
    def is_configured(self) -> bool:
        return True

    async def send_notification(
        self,
        message: NotificationMessage
    ) -> Tuple[NotificationDeliveryStatus, Optional[str], Optional[str]]:
        with self._lock:
            if message.user_id not in self._inboxes:
                self._inboxes[message.user_id] = deque(maxlen=self.max_inbox_size)

            msg_id = message.notification_id
            self._inboxes[message.user_id].append(message)
            self._all_notifications[msg_id] = message

            # Persist to database repository
            try:
                NotificationRepository.record_notification(message)
            except Exception as e:
                logger.warning(f"[IN_APP] Database notification record error: {e}")

            logger.info(f"[IN_APP] Delivered in-app alert {msg_id} to user {message.user_id}")
            return NotificationDeliveryStatus.DELIVERED, msg_id, None

    def get_user_inbox(self, user_id: str, limit: int = 50) -> List[NotificationMessage]:
        with self._lock:
            inbox = self._inboxes.get(user_id, deque())
            return list(reversed(list(inbox)))[:limit]

    def get_notification_by_id(self, notification_id: str) -> Optional[NotificationMessage]:
        with self._lock:
            return self._all_notifications.get(notification_id)

    def get_all_recent_notifications(self, limit: int = 100) -> List[NotificationMessage]:
        with self._lock:
            return list(reversed(list(self._all_notifications.values())))[:limit]

# Global singleton
in_app_provider = InAppNotificationProvider()
