"""
Unit tests for Phase 14 Risk State Versioning & Level Boundaries.
"""

import pytest
from services.risk.risk_types import RiskLevel, RiskState, RiskContributor
from services.risk.risk_calculator import RiskCalculator

def test_risk_level_thresholds():
    # 1. Normal State (< 25 pts)
    score_normal, level_normal, sub_normal = RiskCalculator.calculate_risk_score(
        fused_rain_mm_hr=2.0,
        rain_24h_mm=10.0,
        river_stage_m=20.5,
        danger_stage_m=26.3,
        discharge_cumec=4500.0,
        flood_prob=0.05,
        inundated_area_sqkm=15.0
    )
    assert score_normal < 25.0
    assert level_normal == RiskLevel.NORMAL

    # 2. Watch State (25 - 45 pts)
    score_watch, level_watch, sub_watch = RiskCalculator.calculate_risk_score(
        fused_rain_mm_hr=25.0,
        rain_24h_mm=60.0,
        river_stage_m=24.0,
        danger_stage_m=26.3,
        discharge_cumec=12000.0,
        flood_prob=0.25,
        inundated_area_sqkm=120.0
    )
    assert 25.0 <= score_watch < 45.0
    assert level_watch == RiskLevel.WATCH

    # 3. Warning State (45 - 65 pts)
    score_warn, level_warn, sub_warn = RiskCalculator.calculate_risk_score(
        fused_rain_mm_hr=45.0,
        rain_24h_mm=120.0,
        river_stage_m=25.5,
        danger_stage_m=26.3,
        discharge_cumec=18000.0,
        flood_prob=0.60,
        inundated_area_sqkm=260.0
    )
    assert 45.0 <= score_warn < 65.0
    assert level_warn == RiskLevel.WARNING

    # 4. Critical State (>= 80 pts)
    score_crit, level_crit, sub_crit = RiskCalculator.calculate_risk_score(
        fused_rain_mm_hr=85.0,
        rain_24h_mm=250.0,
        river_stage_m=27.5,
        danger_stage_m=26.3,
        discharge_cumec=28000.0,
        flood_prob=0.95,
        inundated_area_sqkm=550.0,
        population_exposed=180000,
        critical_assets_exposed=38
    )
    assert score_crit >= 80.0
    assert level_crit == RiskLevel.CRITICAL

def test_risk_state_immutability_and_versioning():
    state = RiskState(
        state_version=1042,
        risk_score=56.4,
        previous_risk_score=38.2,
        risk_level=RiskLevel.WARNING,
        risk_change=18.2,
        is_material_change=True,
        forecast_run_id="FR-2026-TEST"
    )
    assert state.state_version == 1042
    assert state.risk_score == 56.4
    assert state.risk_change == 18.2
    assert state.is_material_change is True
    assert state.risk_level == RiskLevel.WARNING
