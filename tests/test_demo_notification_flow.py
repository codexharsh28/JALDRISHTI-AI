"""
Mock Notification Flow & Multi-Channel Verification Tests during Demo.
"""

import pytest
from services.demo.demo_orchestrator import demo_orchestrator
from services.notifications.notification_queue import notification_queue
from services.notifications.user_store import user_store

def test_mock_notification_dispatched_at_alert_stage():
    demo_orchestrator.start_demo()
    # Step to stage 12 (Public Notification)
    for _ in range(12):
        demo_orchestrator.step_forward()

    status = demo_orchestrator.get_status()
    assert status["affected_citizen_notified"] is True
    assert status["outside_citizen_excluded"] is True

    # Verify mock SMS queue captures message
    assert len(notification_queue.mock_sms_sink.sent_messages) > 0
    last_msg = notification_queue.mock_sms_sink.sent_messages[-1]
    assert "[MOCK SMS]" in last_msg["title"]
    assert "9800000001" in last_msg["recipient"] or "******0001" in last_msg["recipient"]
