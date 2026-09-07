"""
Unit tests for Digital Basin Twin State Snapshot Generation & Versioning (Phase 17).
"""

import pytest
from datetime import datetime, timezone
from services.basin_state import DigitalBasinEngine, BasinStateStore, DigitalBasinState

def test_digital_basin_state_initialization():
    engine = DigitalBasinEngine(basin_id="pilot-mahanadi-delta")
    state = engine.get_current_state()

    assert state.basin_id == "pilot-mahanadi-delta"
    assert state.version >= 1
    assert 0.0 <= state.soil_moisture.saturation_index <= 1.0
    assert state.channel_storage.current_storage_mcm > 0.0
    assert len(state.barrage_operations.structures) >= 4
    assert state.tidal_boundary.total_water_level_m > 0.0

def test_digital_basin_twin_step_advancement_and_storage():
    engine = DigitalBasinEngine()
    store = BasinStateStore()
    
    t0 = datetime(2026, 8, 27, 14, 0, 0, tzinfo=timezone.utc)
    new_state = engine.compute_full_digital_twin_step(
        fused_rain_mm_hr=25.0,
        inflow_cumec=19500.0,
        outflow_cumec=18000.0,
        storm_surge_m=0.60,
        base_time=t0
    )

    assert new_state.version == 2
    assert new_state.basin_hydraulic_risk_index > 0.0
    
    store.record_state(new_state)
    latest = store.get_latest_state()
    assert latest is not None
    assert latest.version == 2
