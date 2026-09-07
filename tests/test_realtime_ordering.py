"""
Unit tests for handling out-of-order operational events.
"""

import pytest
from datetime import datetime, timezone, timedelta
from services.events.event_types import EventType
from services.events.event_schema import OperationalEvent
from services.events.event_store import EventStore

def test_out_of_order_causal_chain_reconstruction(tmp_path):
    """Verifies that events arriving out of order are properly sorted by chronological occurrence."""
    store = EventStore(event_dir=tmp_path)
    now = datetime.now(timezone.utc)
    corr_id = "CORR-CHAIN-01"

    # Event 2 arrives before Event 1
    ev2 = OperationalEvent.create(
        event_type=EventType.HYDROLOGY_UPDATED,
        source_id="HYDRO",
        provider="Streamflow",
        occurred_at=now + timedelta(minutes=10),
        correlation_id=corr_id,
        data={"stage": 26.5}
    )

    ev1 = OperationalEvent.create(
        event_type=EventType.SOURCE_DATA_RECEIVED,
        source_id="CWC_GAUGE",
        provider="CWC",
        occurred_at=now,
        correlation_id=corr_id,
        data={"stage": 25.8}
    )

    store.append(ev2)
    store.append(ev1)

    chain = store.get_causal_chain(ev2.event_id)
    assert len(chain) == 2
    # Check that events in chain are chronologically ordered
    assert chain[0].created_at <= chain[1].created_at
