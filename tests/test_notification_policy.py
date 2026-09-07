"""
Unit tests for Notification Channel Routing & Severity Policy.
"""

import pytest
from services.notifications.policy_engine import PolicyEngine
from services.notifications.notification_types import (
    NotificationChannel,
    NotificationSeverityPolicy,
    UserPreferences,
    User,
    LocationSubscription
)

def test_unverified_phone_cannot_receive_sms():
    engine = PolicyEngine()
    user = User(
        phone_number="9876543210",
        phone_hash="hash123",
        phone_verified=False
    )
    sub = LocationSubscription(
        user_id=user.user_id,
        label="HOME",
        locality_name="Cuttack",
        latitude=20.46,
        longitude=85.88
    )

    # For WARNING severity, verified phone gets SMS, unverified gets only IN_APP
    channels = engine.evaluate_channel_eligibility(
        user=user,
        subscription=sub,
        severity=NotificationSeverityPolicy.WARNING
    )
    assert NotificationChannel.SMS not in channels
    assert NotificationChannel.IN_APP in channels

def test_verified_phone_receives_sms_for_high_risk():
    engine = PolicyEngine()
    user = User(
        phone_number="9876543210",
        phone_hash="hash123",
        phone_verified=True,
        fcm_device_tokens=["token-xyz"]
    )
    sub = LocationSubscription(
        user_id=user.user_id,
        label="HOME",
        locality_name="Cuttack",
        latitude=20.46,
        longitude=85.88
    )

    channels = engine.evaluate_channel_eligibility(
        user=user,
        subscription=sub,
        severity=NotificationSeverityPolicy.HIGH_RISK
    )
    assert NotificationChannel.SMS in channels
    assert NotificationChannel.PUSH in channels
    assert NotificationChannel.IN_APP in channels
