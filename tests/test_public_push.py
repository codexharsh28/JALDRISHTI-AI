"""
Push Notification (FCM HTTP v1 & Mock Sink) Tests for JALDRISHTI AI.
"""

import pytest
from services.notifications.providers.push_provider import MockPushSink, FCMPushProvider
from services.notifications.notification_types import (
    NotificationMessage,
    NotificationSeverityPolicy,
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationProvenance
)

@pytest.mark.anyio
async def test_mock_push_sink_delivery():
    sink = MockPushSink()
    sink.clear()

    msg = NotificationMessage(
        user_id="USR-PUSH-01",
        channel=NotificationChannel.PUSH,
        severity=NotificationSeverityPolicy.HIGH_RISK,
        title="JALDRISHTI ALERT",
        body="Flood alert near Cuttack",
        recipient="fcm-device-token-12345",
        locality="Cuttack",
        deeplink_url="/public-portal?alert_id=ALT-1",
        provenance=NotificationProvenance(
            alert_id="ALT-1",
            forecast_run_id="FR-1",
            user_region="Cuttack",
            channel=NotificationChannel.PUSH,
            template_id="DLT-1"
        )
    )

    status, push_id, err = await sink.send_notification(msg)
    assert status == NotificationDeliveryStatus.DELIVERED
    assert push_id.startswith("MOCK-FCM-")
    assert len(sink.sent_pushes) == 1
    assert sink.sent_pushes[0]["deeplink"] == "/public-portal?alert_id=ALT-1"

@pytest.mark.anyio
async def test_fcm_unconfigured_fails_safely(monkeypatch):
    monkeypatch.delenv("FIREBASE_CREDENTIALS_PATH", raising=False)
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)

    provider = FCMPushProvider()
    assert provider.is_configured is False

    msg = NotificationMessage(
        user_id="USR-PUSH-02",
        channel=NotificationChannel.PUSH,
        severity=NotificationSeverityPolicy.WARNING,
        title="Advisory",
        body="Advisory body",
        recipient="fcm-token-67890",
        locality="Cuttack",
        provenance=NotificationProvenance(
            alert_id="ALT-2",
            forecast_run_id="FR-2",
            user_region="Cuttack",
            channel=NotificationChannel.PUSH,
            template_id="DLT-2"
        )
    )

    status, pid, err = await provider.send_notification(msg)
    assert status == NotificationDeliveryStatus.FAILED
    assert "Missing Firebase credentials" in err
