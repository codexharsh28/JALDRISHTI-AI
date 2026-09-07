"""
Notification Anti-Spam, Cooldown & State Evolution Deduplication Tests.
Validates that model fluctuations do not generate duplicate spam messages.
"""

import pytest
from services.notifications.policy_engine import PolicyEngine
from services.notifications.notification_types import NotificationSeverityPolicy

def test_minor_probability_fluctuations_do_not_generate_duplicate_alerts():
    engine = PolicyEngine(cooldown_minutes=45)
    
    # Alert ALT-101 at WARNING
    fp1 = engine.generate_fingerprint(
        alert_id="ALT-101",
        severity=NotificationSeverityPolicy.WARNING,
        locality="Cuttack Reach",
        hazard="FLOOD"
    )

    # First dispatch allowed
    allowed1, reason1 = engine.check_anti_spam(fp1, "USR-101", "SUB-101", NotificationSeverityPolicy.WARNING)
    assert allowed1 is True

    # 2 minutes later, model score shifts from 67% to 68% (same severity WARNING)
    allowed2, reason2 = engine.check_anti_spam(fp1, "USR-101", "SUB-101", NotificationSeverityPolicy.WARNING)
    assert allowed2 is False
    assert "Suppressed by cooldown" in reason2

def test_escalation_to_high_risk_bypasses_cooldown():
    engine = PolicyEngine(cooldown_minutes=45)
    
    fp_watch = engine.generate_fingerprint("ALT-102", NotificationSeverityPolicy.WATCH, "Cuttack Reach")
    allowed1, _ = engine.check_anti_spam(fp_watch, "USR-102", "SUB-102", NotificationSeverityPolicy.WATCH)
    assert allowed1 is True

    # Escalation to HIGH_RISK immediately bypasses cooldown
    fp_high = engine.generate_fingerprint("ALT-102", NotificationSeverityPolicy.HIGH_RISK, "Cuttack Reach")
    allowed2, reason2 = engine.check_anti_spam(fp_high, "USR-102", "SUB-102", NotificationSeverityPolicy.HIGH_RISK)
    assert allowed2 is True
    assert "Escalation bypasses cooldown" in reason2
