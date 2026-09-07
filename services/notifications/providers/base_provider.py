"""
Abstract Base Notification Provider for JALDRISHTI AI.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from services.notifications.notification_types import (
    NotificationMessage,
    NotificationDeliveryStatus
)

class NotificationProvider(ABC):
    """
    Abstract interface for dispatching notifications across channels.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    async def send_notification(
        self,
        message: NotificationMessage
    ) -> Tuple[NotificationDeliveryStatus, Optional[str], Optional[str]]:
        """
        Dispatches notification message.
        Returns: (delivery_status, provider_message_id, error_message)
        """
        pass
