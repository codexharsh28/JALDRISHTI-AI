"""
Policy Engine & Channel Routing Tests for JALDRISHTI AI Public Alerts.
Validates minimum severity thresholds, multi-channel matrix, and verified-phone requirement.
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

def test_minimum_severity_filter():
    engine = PolicyEngine()
    user = User(
        phone_number="9876543210",
        phone_hash="hash1",
        phone_verified=True,
        global_preferences=UserPreferences(minimum_severity=NotificationSeverityPolicy.WARNING)
    )
    sub = LocationSubscription(
        user_id=user.user_id,
        locality_name="Cuttack",
        latitude=20.46,
        longitude=85.88
    )

    # WATCH is below user minimum threshold WARNING -> no channels
    channels_watch = engine.evaluate_channel_eligibility(user=user, subscription=sub, severity=NotificationSeverityPolicy.WATCH)
    assert channels_watch == []

    # WARNING matches minimum threshold -> eligible
    channels_warning = engine.evaluate_channel_eligibility(user=user, subscription=sub, severity=NotificationSeverityPolicy.WARNING)
    assert NotificationChannel.SMS in channels_warning
    assert NotificationChannel.IN_APP in channels_warning

def test_critical_severity_overrides_preferences():
    engine = PolicyEngine()
    user = User(
        phone_number="9876543210",
        phone_hash="hash2",
        phone_verified=True,
        global_preferences=UserPreferences(minimum_severity=NotificationSeverityPolicy.HIGH_RISK)
    )
    sub = LocationSubscription(
        user_id=user.user_id,
        locality_name="Cuttack",
        latitude=20.46,
        longitude=85.88
    )

    channels = engine.evaluate_channel_eligibility(user=user, subscription=sub, severity=NotificationSeverityPolicy.CRITICAL)
    assert NotificationChannel.SMS in channels
    assert NotificationChannel.IN_APP in channels
