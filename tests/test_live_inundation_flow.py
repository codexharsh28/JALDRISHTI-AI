"""
Unit tests for End-to-End Live Inundation Event Streaming (Phase 15).
"""

import pytest
import asyncio
from services.inundation_evolution.evolution_service import InundationEvolutionService
from services.events.event_types import EventType
from services.events.event_bus import event_bus

def test_live_inundation_processing_flow():
    service = InundationEvolutionService()
    
    events_captured = []
    def _listener(ev):
        events_captured.append(ev)

    event_bus.subscribe(EventType.INUNDATION_UPDATED, _listener)
    event_bus.subscribe(EventType.INUNDATION_CHANGE_DETECTED, _listener)
    event_bus.subscribe(EventType.IMPACT_UPDATED, _listener)
    event_bus.subscribe(EventType.IMPACT_CHANGE_DETECTED, _listener)

    # Process new inundation surge
    snap, chg, assets, pop = asyncio.run(
        service.process_new_inundation(
            forecast_run_id="FR-TEST-STREAM-01",
            inundated_area_sqkm=435.0,
            flood_prob=0.88,
            stage_m=27.35,
            hydrology_source="OBSERVED_CWC",
            confidence="HIGH"
        )
    )

    assert snap.inundated_area_sqkm == 435.0
    assert chg.is_material_change is True
    assert len(assets) > 0
    assert pop.population_exposed_forecast > 0
    assert len(events_captured) >= 4
