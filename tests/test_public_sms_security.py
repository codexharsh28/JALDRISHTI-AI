"""
SMS Security, DLT Compliance & Credential Protection Tests for JALDRISHTI AI.
Proves that missing DLT credentials block production dispatches and tests never hit live gateways.
"""

import pytest
from services.notifications.providers.sms_provider import MSG91Provider, MockSMSSink
from services.notifications.notification_types import (
    NotificationMessage,
    NotificationSeverityPolicy,
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationProvenance
)

@pytest.mark.anyio
async def test_msg91_dlt_validation_blocks_unconfigured(monkeypatch):
    monkeypatch.delenv("MSG91_AUTH_KEY", raising=False)
    monkeypatch.delenv("DLT_ENTITY_ID", raising=False)
    monkeypatch.delenv("DLT_SENDER_ID", raising=False)

    provider = MSG91Provider()
    assert provider.is_configured is False
    assert provider.provider_name == "MSG91_DLT_GATEWAY"

    msg = NotificationMessage(
        user_id="USR-SEC-01",
        channel=NotificationChannel.SMS,
        severity=NotificationSeverityPolicy.CRITICAL,
        title="Emergency Alert",
        body="Emergency message body",
        recipient="9876543210",
        locality="Cuttack",
        provenance=NotificationProvenance(
            alert_id="ALT-SEC-01",
            forecast_run_id="FR-SEC-01",
            user_region="Cuttack",
            channel=NotificationChannel.SMS,
            template_id="DLT-JALDRISHTI-CRITICAL-EN"
        )
    )
    status, msg_id, err = await provider.send_notification(msg)
    assert status == NotificationDeliveryStatus.FAILED
    assert "Missing DLT credentials" in err

@pytest.mark.anyio
async def test_mock_sms_sink_captures_in_memory_only():
    sink = MockSMSSink()
    sink.clear()
    assert len(sink.sent_messages) == 0

    msg = NotificationMessage(
        user_id="USR-SEC-02",
        channel=NotificationChannel.SMS,
        severity=NotificationSeverityPolicy.WARNING,
        title="Advisory",
        body="Advisory message body",
        recipient="9876543210",
        locality="Cuttack",
        provenance=NotificationProvenance(
            alert_id="ALT-SEC-02",
            forecast_run_id="FR-SEC-02",
            user_region="Cuttack",
            channel=NotificationChannel.SMS,
            template_id="DLT-JALDRISHTI-WARNING-EN"
        )
    )
    status, msg_id, err = await sink.send_notification(msg)
    assert status == NotificationDeliveryStatus.DELIVERED
    assert len(sink.sent_messages) == 1
    assert sink.sent_messages[0]["template_id"] == "DLT-JALDRISHTI-WARNING-EN"
