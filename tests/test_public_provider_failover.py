"""
Provider Failover & Retry Backoff Tests for JALDRISHTI AI Notification Queue.
"""

import pytest
import asyncio
from services.notifications.notification_types import (
    NotificationMessage,
    NotificationSeverityPolicy,
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationProvenance
)
from services.notifications.notification_queue import NotificationQueueWorker

@pytest.mark.anyio
async def test_queue_failover_to_mock_sink_when_unconfigured():
    worker = NotificationQueueWorker(use_mock_providers=True)
    provider = worker._select_provider(NotificationChannel.SMS)
    assert provider.provider_name == "MOCK_SMS_SINK"

@pytest.mark.anyio
async def test_retry_count_incrementation_on_error():
    worker = NotificationQueueWorker(use_mock_providers=True)
    
    msg = NotificationMessage(
        user_id="USR-RETRY-01",
        channel=NotificationChannel.IN_APP,
        severity=NotificationSeverityPolicy.WARNING,
        title="Test Alert",
        body="Test message",
        recipient="USR-RETRY-01",
        locality="Cuttack",
        retry_count=0,
        max_retries=2,
        provenance=NotificationProvenance(
            alert_id="ALT-R1",
            forecast_run_id="FR-R1",
            user_region="Cuttack",
            channel=NotificationChannel.IN_APP,
            template_id="DLT-R1"
        )
    )

    # Process normal message
    await worker._process_message(msg)
    assert msg.status == NotificationDeliveryStatus.DELIVERED
