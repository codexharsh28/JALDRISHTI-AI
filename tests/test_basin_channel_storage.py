"""
Unit tests for Reach Channel Storage Volume, Routing & Backwater Head (Phase 17).
"""

import pytest
from services.basin_state import DigitalBasinEngine

def test_channel_storage_accumulation_under_inflow_surplus():
    engine = DigitalBasinEngine()
    initial_storage = engine.get_current_state().channel_storage.current_storage_mcm

    # Inflow (22000 cumec) > Outflow (16000 cumec)
    updated = engine.update_channel_storage(
        inflow_cumec=22000.0,
        outflow_cumec=16000.0,
        dt_hours=2.0
    )

    assert updated.current_storage_mcm > initial_storage
    assert updated.capacity_utilization_pct == round((updated.current_storage_mcm / updated.max_safe_storage_mcm) * 100.0, 1)

def test_channel_storage_backwater_head_calculation():
    engine = DigitalBasinEngine()
    
    # High storm tide (2.8m) increases backwater head
    updated = engine.update_channel_storage(
        inflow_cumec=18000.0,
        outflow_cumec=18000.0,
        dt_hours=1.0,
        downstream_water_level_m=2.80
    )

    assert updated.backwater_head_m > 0.30
