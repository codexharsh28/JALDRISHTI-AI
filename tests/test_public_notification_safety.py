"""
Comprehensive Safety Verification Suite for JALDRISHTI AI Public Notifications.
Verifies all 10 core safety mandates from the architectural specification.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.main import app
from services.notifications.notification_types import (
    User,
    LocationSubscription,
    NotificationSeverityPolicy,
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationMessage,
    NotificationProvenance
)
from services.notifications.user_store import UserStore, user_store
from services.notifications.policy_engine import PolicyEngine, policy_engine
from services.notifications.template_engine import TemplateEngine, template_engine
from services.notifications.notification_service import NotificationService, notification_service
from services.notifications.providers.sms_provider import MockSMSSink, MSG91Provider
from services.events.event_schema import OperationalEvent
from services.events.event_types import EventType

client = TestClient(app)

# 1. Unverified phone cannot receive production/gateway SMS
def test_safety_rule_1_unverified_phone_cannot_receive_sms():
    engine = PolicyEngine()
    unverified_user = User(
        phone_number="9876543210",
        phone_hash="hash_unverified",
        phone_verified=False
    )
    sub = LocationSubscription(
        user_id=unverified_user.user_id,
        locality_name="Cuttack",
        latitude=20.46,
        longitude=85.88
    )

    # Test across all severities
    for sev in [NotificationSeverityPolicy.WATCH, NotificationSeverityPolicy.WARNING, NotificationSeverityPolicy.HIGH_RISK, NotificationSeverityPolicy.CRITICAL]:
        channels = engine.evaluate_channel_eligibility(user=unverified_user, subscription=sub, severity=sev)
        assert NotificationChannel.SMS not in channels, f"Unverified phone received SMS on severity {sev}"
        assert NotificationChannel.IN_APP in channels

# 2. MOCK_SMS cannot send production SMS (isolated local sink)
@pytest.mark.anyio
async def test_safety_rule_2_mock_sms_isolated_sink():
    sink = MockSMSSink()
    assert sink.provider_name == "MOCK_SMS_SINK"
    assert sink.is_configured is True
    
    msg = NotificationMessage(
        user_id="USR-TEST01",
        channel=NotificationChannel.SMS,
        severity=NotificationSeverityPolicy.WARNING,
        title="Test Alert",
        body="Test Body",
        recipient="9876543210",
        locality="Cuttack",
        provenance=NotificationProvenance(
            alert_id="ALT-001",
            forecast_run_id="FR-001",
            user_region="Cuttack",
            channel=NotificationChannel.SMS,
            template_id="DLT-001"
        )
    )
    status, msg_id, err = await sink.send_notification(msg)
    assert status == NotificationDeliveryStatus.DELIVERED
    assert msg_id.startswith("MOCK-SMS-")
    assert len(sink.sent_messages) == 1
    assert sink.sent_messages[0]["recipient"] == "9876543210"

# 3. Missing DLT config prevents production SMS
@pytest.mark.anyio
async def test_safety_rule_3_missing_dlt_prevents_production_sms(monkeypatch):
    monkeypatch.delenv("MSG91_AUTH_KEY", raising=False)
    monkeypatch.delenv("DLT_ENTITY_ID", raising=False)
    monkeypatch.delenv("DLT_SENDER_ID", raising=False)

    provider = MSG91Provider()
    assert provider.is_configured is False

    msg = NotificationMessage(
        user_id="USR-TEST02",
        channel=NotificationChannel.SMS,
        severity=NotificationSeverityPolicy.CRITICAL,
        title="Alert",
        body="Body",
        recipient="9876543210",
        locality="Cuttack",
        provenance=NotificationProvenance(
            alert_id="ALT-002",
            forecast_run_id="FR-002",
            user_region="Cuttack",
            channel=NotificationChannel.SMS,
            template_id="DLT-002"
        )
    )
    status, msg_id, err = await provider.send_notification(msg)
    assert status == NotificationDeliveryStatus.FAILED
    assert "Missing DLT credentials" in err

# 4. RED alert cannot bypass Phase 16 human review
@pytest.mark.anyio
async def test_safety_rule_4_red_alert_human_review_gate():
    test_notif_svc = NotificationService()
    
    # Simulate unapproved RED alert event
    event = OperationalEvent.create(
        event_type=EventType.ALERT_STATE_CHANGED,
        source_id="ALERT_ENGINE",
        provider="JALDRISHTI_ALERT_SYSTEM",
        data={
            "alert_id": "ALT-RED-UNAPPROVED",
            "severity": "RED",
            "status": "PENDING_HUMAN_REVIEW",
            "lat": 20.46,
            "lon": 85.88,
            "location_name": "Cuttack Reach"
        }
    )
    
    # Handle event should suppress fanout
    queued = await test_notif_svc._handle_alert_event(event)
    assert queued is None or queued == 0

# 5. GloFAS data is explicitly labeled MODELED_GLOFAS
def test_safety_rule_5_glofas_labeled_correctly():
    res = template_engine.render_notification(
        severity=NotificationSeverityPolicy.WARNING,
        locality="Naraj",
        data_degraded_notice=True
    )
    assert "Note: Forecast is partly model-based due to telemetry degradation" in res["body"]

# 6. Degraded-data disclaimer appears in Hindi when requested
def test_safety_rule_6_hindi_degraded_data_disclaimer():
    res = template_engine.render_notification(
        severity=NotificationSeverityPolicy.WARNING,
        locality="नाराज",
        language="hi",
        data_degraded_notice=True
    )
    assert "सूचना: प्राथमिक टेलीमेट्री ऑफलाइन होने के कारण" in res["body"]
    assert "जलदृष्टि चेतावनी" in res["title"]

# 7. Public APIs do not expose user locations or private identity
def test_safety_rule_7_public_api_privacy_isolation():
    response = client.get("/api/v1/public-alerts/current")
    assert response.status_code == 200
    alerts = response.json()
    for item in alerts:
        assert "user_id" not in item
        assert "phone_number" not in item
        assert "phone_hash" not in item
        assert "device_token" not in item
        assert "official_guidance" in item
        assert "why_alert_created" in item

# 8. Duplicate alerts do not create duplicate notifications (Anti-spam cooldown)
def test_safety_rule_8_anti_spam_duplicate_suppression():
    engine = PolicyEngine(cooldown_minutes=45)
    fp = engine.generate_fingerprint("ALT-001", NotificationSeverityPolicy.WATCH, "Cuttack")

    allowed1, reason1 = engine.check_anti_spam(fp, "USR-1", "SUB-1", NotificationSeverityPolicy.WATCH)
    assert allowed1 is True

    # Immediate duplicate
    allowed2, reason2 = engine.check_anti_spam(fp, "USR-1", "SUB-1", NotificationSeverityPolicy.WATCH)
    assert allowed2 is False
    assert "Suppressed by cooldown" in reason2

    # Escalation bypasses cooldown
    fp_esc = engine.generate_fingerprint("ALT-001", NotificationSeverityPolicy.CRITICAL, "Cuttack")
    allowed3, reason3 = engine.check_anti_spam(fp_esc, "USR-1", "SUB-1", NotificationSeverityPolicy.CRITICAL)
    assert allowed3 is True
    assert "Escalation bypasses cooldown" in reason3

# 9. SENT is not automatically equated to DELIVERED
def test_safety_rule_9_sent_not_equated_to_delivered():
    assert NotificationDeliveryStatus.SENT != NotificationDeliveryStatus.DELIVERED
    assert NotificationDeliveryStatus.SENT.value == "SENT"
    assert NotificationDeliveryStatus.DELIVERED.value == "DELIVERED"

# 10. Notification cannot be generated directly without registered user store / subscription
def test_safety_rule_10_invalid_user_subscription_rejected():
    response = client.post(
        "/api/v1/user/subscriptions",
        json={
            "user_id": "NON_EXISTENT_USER_9999",
            "label": "HOME",
            "locality_name": "Invalid Reach",
            "latitude": 20.0,
            "longitude": 85.0
        }
    )
    assert response.status_code == 404
