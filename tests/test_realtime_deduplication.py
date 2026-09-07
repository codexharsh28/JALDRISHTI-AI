"""
Unit tests for Event Deduplication and Idempotency.
"""

import pytest
from datetime import datetime, timezone
from services.events.event_types import EventType
from services.events.event_schema import OperationalEvent
from services.events.event_store import EventStore

def test_event_store_deduplication(tmp_path):
    """Verifies that identical observation events are rejected at the storage boundary."""
    store = EventStore(event_dir=tmp_path)
    now = datetime.now(timezone.utc)

    ev1 = OperationalEvent.create(
        event_type=EventType.SOURCE_DATA_RECEIVED,
        source_id="IMD_AWS_BHUBANESWAR",
        provider="IMD",
        occurred_at=now,
        data={"rain_mm": 45.0}
    )

    ev2 = OperationalEvent.create(
        event_type=EventType.SOURCE_DATA_RECEIVED,
        source_id="IMD_AWS_BHUBANESWAR",
        provider="IMD",
        occurred_at=now,
        data={"rain_mm": 45.0}
    )

    # First event should be stored
    assert store.append(ev1) is True
    # Second duplicate observation should be rejected
    assert store.append(ev2) is False
    assert len(store._events_by_id) == 1
