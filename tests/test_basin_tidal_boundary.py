"""
Unit tests for Astronomical Tide & Estuarine Backwater Dynamics (Phase 17).
"""

import pytest
from datetime import datetime, timezone
from services.basin_state import DigitalBasinEngine

def test_tidal_boundary_harmonic_and_surge_computation():
    engine = DigitalBasinEngine()
    
    t0 = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
    tide_state = engine.update_tidal_boundary(base_time=t0, storm_surge_m=0.75)

    assert tide_state.station_id == "TIDE-PARADIP-01"
    assert tide_state.storm_surge_residual_m == 0.75
    assert tide_state.total_water_level_m == round(tide_state.astronomical_tide_m + 0.75, 2)
    assert tide_state.tidal_phase in ["FLOOD_TIDE", "EBB_TIDE", "HIGH_WATER_SLACK", "LOW_WATER_SLACK"]
    assert 5.0 <= tide_state.backwater_propagation_km <= 50.0
