"""
Deterministic Scenario Trajectory & Physical Bounds Tests.
Verifies DEMO-MAHANADI-STORM-01 stages, monotonic time progression, and valid hydrometeorological trajectories.
"""

import pytest
from services.demo.demo_scenario import DEMO_SCENARIO_STAGES

def test_scenario_stages_count_and_order():
    assert len(DEMO_SCENARIO_STAGES) == 14
    for i, stage in enumerate(DEMO_SCENARIO_STAGES):
        assert stage.index == i
        assert stage.stage_id.startswith(f"T{i}_")

def test_rainfall_rising_and_falling_trajectory():
    # Peak rainfall should occur at stage T3 (48.0 mm/hr)
    rates = [s.rainfall_rate_mm_hr for s in DEMO_SCENARIO_STAGES]
    peak_idx = rates.index(max(rates))
    assert peak_idx == 3
    assert rates[peak_idx] == 48.0
    
    # Rainfall should gradually decay to 0 by stage T13
    assert rates[-1] == 0.0

def test_stage_and_discharge_physical_bounds():
    for stage in DEMO_SCENARIO_STAGES:
        assert 20.0 <= stage.river_stage_m <= 28.0
        assert 1000.0 <= stage.river_discharge_cumec <= 35000.0
        assert stage.inundated_area_sqkm >= 0.0
        assert 0.0 <= stage.risk_score <= 100.0
