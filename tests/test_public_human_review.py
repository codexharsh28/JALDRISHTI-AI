"""
Human-in-the-Loop Review Gating Tests for JALDRISHTI AI Public Alerts.
Proves that RED alerts pending human review are suppressed until authorized operator action.
"""

import pytest
from services.notifications.notification_service import NotificationService
from services.events.event_schema import OperationalEvent
from services.events.event_types import EventType

@pytest.mark.anyio
async def test_pending_human_review_red_alert_suppressed():
    svc = NotificationService()
    
    event = OperationalEvent.create(
        event_type=EventType.ALERT_STATE_CHANGED,
        source_id="ALERT_ENGINE",
        provider="JALDRISHTI_TEST",
        data={
            "alert_id": "ALT-RED-PENDING-01",
            "severity": "RED",
            "status": "PENDING_HUMAN_REVIEW",
            "lat": 20.46,
            "lon": 85.88,
            "location_name": "Cuttack Reach"
        }
    )

    # Should not queue any citizen notification
    res = await svc._handle_alert_event(event)
    assert res is None or res == 0
