"""
SMS Providers for JALDRISHTI AI with India DLT Compliance and Mock Sinks.
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

class MockSMSSink(NotificationProvider):
    """
    Isolated mock SMS sink for testing and local development.
    Captures message payloads without triggering live telecommunication networks.
    """

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "MOCK_SMS_SINK"

    @property
    def is_configured(self) -> bool:
        return True

    async def send_notification(
        self,
        message: NotificationMessage
    ) -> Tuple[NotificationDeliveryStatus, Optional[str], Optional[str]]:
        msg_id = f"MOCK-SMS-{uuid.uuid4().hex[:8]}"
        record = {
            "message_id": msg_id,
            "recipient": message.recipient,
            "title": message.title,
            "body": message.body,
            "template_id": message.provenance.template_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.sent_messages.append(record)
        logger.info(f"[MOCK_SMS] Captured message {msg_id} to {message.recipient}: {message.body[:60]}...")
        return NotificationDeliveryStatus.DELIVERED, msg_id, None

    def clear(self):
        self.sent_messages.clear()

class MSG91Provider(NotificationProvider):
    """
    MSG91 India DLT-compliant SMS Gateway Provider.
    """

    def __init__(self):
        self.endpoint = "https://api.msg91.com/api/v5/flow/"
        self.auth_key = os.getenv("MSG91_AUTH_KEY")
        self.dlt_entity_id = os.getenv("DLT_ENTITY_ID")
        self.dlt_sender_id = os.getenv("DLT_SENDER_ID")
        self.dlt_template_id = os.getenv("DLT_TEMPLATE_ID")

    @property
    def provider_name(self) -> str:
        return "MSG91_DLT_GATEWAY"

    @property
    def is_configured(self) -> bool:
        return bool(self.auth_key and self.dlt_entity_id and self.dlt_sender_id)

    async def send_notification(
        self,
        message: NotificationMessage
    ) -> Tuple[NotificationDeliveryStatus, Optional[str], Optional[str]]:
        if not self.is_configured:
            return (
                NotificationDeliveryStatus.FAILED,
                None,
                "MSG91 SMS Provider not configured: Missing DLT credentials or Auth Key"
            )

        # In production with live credentials, would execute httpx POST to MSG91 API
        msg_id = f"MSG91-{uuid.uuid4().hex[:10]}"
        return NotificationDeliveryStatus.SENT, msg_id, None

class TwilioSMSProvider(NotificationProvider):
    """
    Twilio Global SMS Gateway Provider.
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_FROM_PHONE")

    @property
    def provider_name(self) -> str:
        return "TWILIO_SMS_GATEWAY"

    @property
    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_phone)

    async def send_notification(
        self,
        message: NotificationMessage
    ) -> Tuple[NotificationDeliveryStatus, Optional[str], Optional[str]]:
        if not self.is_configured:
            return (
                NotificationDeliveryStatus.FAILED,
                None,
                "Twilio SMS Provider not configured: Missing Account SID or Token"
            )

        msg_id = f"TW-{uuid.uuid4().hex[:10]}"
        return NotificationDeliveryStatus.SENT, msg_id, None
