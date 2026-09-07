"""
Unit tests for Event Bus Backpressure and Priority Shedding.
"""

import pytest
from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent
from services.events.event_bus import InMemoryEventBus

@pytest.mark.anyio
async def test_backpressure_priority_shedding():
    """Confirms that under queue saturation, LOW/NORMAL events are dropped, but CRITICAL alerts are retained."""
    bus = InMemoryEventBus(max_queue_size=5)

    # Fill queue to capacity with normal events
    for i in range(5):
        ev = OperationalEvent.create(
            event_type=EventType.SOURCE_DATA_RECEIVED,
            source_id=f"SRC_{i}",
            provider="Test",
            priority=EventPriority.NORMAL,
            data={"val": i}
        )
        await bus.publish(ev)

    # 6th NORMAL event should be dropped due to backpressure
    ev_normal = OperationalEvent.create(
        event_type=EventType.SOURCE_DATA_RECEIVED,
        source_id="SRC_OVERFLOW",
        provider="Test",
        priority=EventPriority.NORMAL,
        data={"val": 99}
    )
    published_normal = await bus.publish(ev_normal)
    assert published_normal is False
    assert bus.dropped_backpressure_count == 1

    # CRITICAL alert event MUST be accepted despite full queue
    ev_critical = OperationalEvent.create(
        event_type=EventType.HUMAN_REVIEW_REQUIRED,
        source_id="ALERT_SAFETY",
        provider="Alert Engine",
        priority=EventPriority.CRITICAL,
        data={"alert_id": "ALT-RED-01"}
    )
    published_critical = await bus.publish(ev_critical)
    assert published_critical is True
