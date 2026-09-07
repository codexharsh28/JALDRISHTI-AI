"""
End-to-End Notification Orchestration and Observability Verification Suite.
Tests full pipeline: User -> Subscription -> Alert Fanout -> Queue -> In-App & SMS Mock -> Metrics API.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.main import app
from services.notifications.notification_types import (
    NotificationSeverityPolicy,
    NotificationDeliveryStatus,
    NotificationChannel,
    NotificationMessage,
    NotificationProvenance
)
from services.notifications.user_store import user_store
from services.notifications.notification_service import notification_service
from services.notifications.notification_queue import notification_queue
from services.notifications.providers.in_app_provider import in_app_provider

client = TestClient(app)

@pytest.mark.anyio
async def test_end_to_end_user_registration_and_fanout():
    # 1. Register a test citizen
    phone = "9876543299"
    user = user_store.register_user(phone_number=phone, preferred_language="en")
    assert user.user_id.startswith("USR-")

    # 2. Verify phone via OTP
    ok, msg, meta = user_store.request_otp(phone)
    assert ok is True
    dev_otp = user_store.get_dev_otp_for_testing(phone)
    assert dev_otp is not None
    v_ok, v_msg, token = user_store.verify_otp(phone, dev_otp)
    assert v_ok is True
    assert token is not None
    assert user_store.get_user_by_id(user.user_id).phone_verified is True

    # 3. Add HOME location subscription at Cuttack (20.46, 85.88)
    sub = user_store.add_subscription(
        user_id=user.user_id,
        label="HOME",
        locality_name="Cuttack Delta",
        latitude=20.46,
        longitude=85.88,
        radius_km=15.0
    )
    assert sub.subscription_id.startswith("SUB-")

    # 4. Trigger alert fanout for Cuttack reaching WARNING severity
    queued_count = await notification_service.process_alert_fanout(
        alert_id="ALT-E2E-001",
        severity=NotificationSeverityPolicy.WARNING,
        hazard="RIVERINE_FLOODING",
        target_lat=20.47,
        target_lon=85.89,
        locality="Cuttack Delta",
        forecast_run_id="FR-E2E-01"
    )
    assert queued_count >= 1

    # 5. Process queue item
    msg = await notification_queue._queue.get()
    await notification_queue._process_message(msg)
    notification_queue._queue.task_done()

    # 6. Verify delivery in user inbox
    inbox = in_app_provider.get_user_inbox(user.user_id)
    assert len(inbox) >= 1
    assert "JALDRISHTI" in inbox[0].title
    assert "Follow official SDMA/DDMA" in inbox[0].body
    assert inbox[0].provenance.alert_id == "ALT-E2E-001"

def test_notification_observability_endpoints():
    # Test health endpoint
    h_res = client.get("/api/v1/notifications/health")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["status"] == "HEALTHY"
    assert "providers" in h_data
    assert h_data["providers"]["in_app"] == "ONLINE"

    # Test metrics endpoint
    m_res = client.get("/api/v1/notifications/metrics")
    assert m_res.status_code == 200
    m_data = m_res.json()
    assert "total_queued" in m_data
    assert "delivery_rate_pct" in m_data
    assert "median_latency_ms" in m_data

    # Test providers endpoint
    p_res = client.get("/api/v1/notifications/providers")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert "active_sms_provider" in p_data
    assert "active_push_provider" in p_data
    assert "active_in_app_provider" in p_data
    assert p_data["mock_mode"] is True

def test_public_alerts_rest_endpoints():
    # Test current public alerts endpoint
    res = client.get("/api/v1/public-alerts/current")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
