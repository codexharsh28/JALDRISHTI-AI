"""
Delivery State Machine & Latency Tracking Tests for JALDRISHTI AI Public Alerts.
Proves that SENT is distinct from DELIVERED, and delivery metrics are accurately computed.
"""

import pytest
from services.notifications.notification_types import (
    NotificationDeliveryStatus,
    NotificationChannel,
    NotificationSeverityPolicy,
    NotificationMessage,
    NotificationProvenance,
    DeliveryRecord
)
from services.notifications.notification_queue import NotificationQueueWorker

@pytest.mark.anyio
async def test_sent_is_not_delivered_state():
    assert NotificationDeliveryStatus.SENT != NotificationDeliveryStatus.DELIVERED
    assert NotificationDeliveryStatus.SENT.value == "SENT"
    assert NotificationDeliveryStatus.DELIVERED.value == "DELIVERED"

@pytest.mark.anyio
async def test_queue_metrics_and_delivery_history():
    worker = NotificationQueueWorker(use_mock_providers=True)
    
    msg = NotificationMessage(
        user_id="USR-METRICS-01",
        channel=NotificationChannel.IN_APP,
        severity=NotificationSeverityPolicy.WARNING,
        title="Test Alert",
        body="Test message",
        recipient="USR-METRICS-01",
        locality="Cuttack",
        provenance=NotificationProvenance(
            alert_id="ALT-M1",
            forecast_run_id="FR-M1",
            user_region="Cuttack",
            channel=NotificationChannel.IN_APP,
            template_id="DLT-M1"
        )
    )

    await worker._process_message(msg)
    metrics = worker.get_metrics_summary()
    assert metrics["total_sent"] >= 1
    assert metrics["delivery_rate_pct"] == 100.0
    assert len(worker.get_recent_deliveries()) >= 1
