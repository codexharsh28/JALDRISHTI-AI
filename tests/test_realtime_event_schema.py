"""
Unit tests for Event Schema immutability, versioning, and provenance integrity.
"""

import pytest
from pydantic import ValidationError
from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent

def test_event_schema_immutability():
    """Confirms that OperationalEvent instances are strictly frozen/immutable."""
    ev = OperationalEvent.create(
        event_type=EventType.FORECAST_COMPLETED,
        source_id="FORECAST_CORE",
        provider="JALDRISHTI ML",
        data={"run_id": "RUN-001"}
    )
    assert ev.event_version == "1.0.0"
    assert ev.payload_hash is not None

    with pytest.raises(ValidationError):
        # Attempting mutation must raise ValidationError
        ev.source_id = "MUTATED_SOURCE"

def test_event_correlation_and_causation_chaining():
    """Verifies that causation_id and correlation_id trace causal lineage."""
    root_ev = OperationalEvent.create(
        event_type=EventType.SOURCE_DATA_RECEIVED,
        source_id="IMD_AWS",
        provider="IMD",
        data={"rain": 25.0}
    )

    child_ev = OperationalEvent.create(
        event_type=EventType.RAINFALL_FUSION_UPDATED,
        source_id="FUSION_ENGINE",
        provider="Fusion",
        data={"fused_rain": 24.5},
        correlation_id=root_ev.correlation_id,
        causation_id=root_ev.event_id
    )

    assert child_ev.correlation_id == root_ev.correlation_id
    assert child_ev.causation_id == root_ev.event_id
