"""
Unit tests for Soil Moisture Infiltration, Deficit & 30-Day API Dynamics (Phase 17).
"""

import pytest
from services.basin_state import DigitalBasinEngine

def test_soil_moisture_recharge_under_heavy_rain():
    engine = DigitalBasinEngine()
    initial_sat = engine.get_current_state().soil_moisture.saturation_index

    # 40mm/hr intense rainfall for 2 hours
    updated = engine.update_soil_moisture(fused_rain_mm_hr=40.0, dt_hours=2.0)
    
    assert updated.saturation_index >= initial_sat
    assert updated.moisture_deficit_mm <= 150.0 * (1.0 - updated.saturation_index) + 0.1
    assert updated.antecedent_precipitation_index_30d > 0.0

def test_soil_moisture_depletion_in_dry_period():
    engine = DigitalBasinEngine()
    # Initial wet state
    engine.update_soil_moisture(fused_rain_mm_hr=30.0, dt_hours=3.0)
    sat_wet = engine.get_current_state().soil_moisture.saturation_index

    # Dry period (0 rain for 12 hours)
    updated = engine.update_soil_moisture(fused_rain_mm_hr=0.0, dt_hours=12.0)
    
    assert updated.saturation_index < sat_wet
    assert updated.moisture_deficit_mm > 0.0
