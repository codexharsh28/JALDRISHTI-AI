"""
Unit tests for the JALDRISHTI AI Centralized Event Bus.
Validates publish, subscribe, wildcard subscription, and metrics.
"""

import pytest
import asyncio
from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent
from services.events.event_bus import InMemoryEventBus

@pytest.mark.anyio
async def test_event_bus_publish_and_subscribe():
    bus = InMemoryEventBus()
    received_events = []

    async def handler(event: OperationalEvent):
        received_events.append(event)

    bus.subscribe(EventType.HYDROLOGY_UPDATED, handler)

    ev = OperationalEvent.create(
        event_type=EventType.HYDROLOGY_UPDATED,
        source_id="TEST_SOURCE",
        provider="Test Provider",
        data={"stage_m": 26.5}
    )

    published = await bus.publish(ev)
    assert published is True
    await asyncio.sleep(0.05) # Allow async task dispatch

    assert len(received_events) == 1
    assert received_events[0].event_id == ev.event_id
    assert received_events[0].data["stage_m"] == 26.5

@pytest.mark.anyio
async def test_event_bus_wildcard_subscription():
    bus = InMemoryEventBus()
    received_wildcard = []

    async def wildcard_handler(event: OperationalEvent):
        received_wildcard.append(event)

    bus.subscribe_all(wildcard_handler)

    ev1 = OperationalEvent.create(event_type=EventType.SOURCE_DATA_RECEIVED, source_id="S1", provider="P1", data={})
    ev2 = OperationalEvent.create(event_type=EventType.INUNDATION_UPDATED, source_id="S2", provider="P2", data={})

    await bus.publish(ev1)
    await bus.publish(ev2)
    await asyncio.sleep(0.05)

    assert len(received_wildcard) == 2
    metrics = bus.get_metrics()
    assert metrics["published_count"] == 2
