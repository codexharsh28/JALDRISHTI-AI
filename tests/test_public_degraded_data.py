"""
Data-Degraded & Modeled GloFAS Disclosure Tests for JALDRISHTI AI Public Alerts.
Proves that telemetry outages and model fallbacks are transparently disclosed to citizens.
"""

import pytest
from services.notifications.template_engine import template_engine
from services.notifications.notification_types import NotificationSeverityPolicy

def test_degraded_telemetry_disclosure_english():
    rendered = template_engine.render_notification(
        severity=NotificationSeverityPolicy.WARNING,
        locality="Mundali Reach",
        language="en",
        data_degraded_notice=True
    )
    assert "Note: Forecast is partly model-based due to telemetry degradation" in rendered["body"]
    assert "Follow official SDMA/DDMA" in rendered["body"]

def test_degraded_telemetry_disclosure_hindi():
    rendered = template_engine.render_notification(
        severity=NotificationSeverityPolicy.WARNING,
        locality="मुंडाली",
        language="hi",
        data_degraded_notice=True
    )
    assert "सूचना: प्राथमिक टेलीमेट्री ऑफलाइन होने के कारण" in rendered["body"]
    assert "जलदृष्टि चेतावनी" in rendered["title"]
