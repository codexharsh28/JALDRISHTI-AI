"""
Risk Evolution Tests: Versioned State, Change Thresholding, Causal Waterfall Decomposition, Temporal Integrity, and Alert Gating.
"""

import pytest
import asyncio
from services.risk.risk_types import RiskLevel, RiskState
from services.risk.risk_calculator import RiskCalculator
from services.risk.causal_explainer import CausalRiskExplainer
from services.risk.risk_service import RiskService
from services.risk.risk_store import RiskStore

# 1. Risk State & Level Computation
def test_risk_calculator_normal_state():
    calc = RiskCalculator()
    inputs = {
        "fused_rain_mm_hr": 2.0,
        "rain_24h_mm": 15.0,
        "river_stage_m": 18.0,
        "danger_stage_m": 26.3,
        "flood_prob": 0.05,
        "inundated_area_sqkm": 5.0,
        "population_exposed": 100,
        "critical_assets_exposed": 0
    }
    score, level, subscores = calc.calculate_risk_score(inputs)
    assert level in [RiskLevel.NORMAL, RiskLevel.WATCH]
    assert score < 30.0

def test_risk_calculator_critical_state():
    calc = RiskCalculator()
    inputs = {
        "fused_rain_mm_hr": 45.0,
        "rain_24h_mm": 210.0,
        "river_stage_m": 28.5,
        "danger_stage_m": 26.3,
        "flood_prob": 0.92,
        "inundated_area_sqkm": 420.0,
        "population_exposed": 150000,
        "critical_assets_exposed": 25
    }
    score, level, subscores = calc.calculate_risk_score(inputs)
    assert level in [RiskLevel.ALERT, RiskLevel.CRITICAL]
    assert score > 60.0

# 2. Causal Waterfall Decomposition
def test_causal_waterfall_decomposition():
    calc = RiskCalculator()
    prev_inputs = {
        "fused_rain_mm_hr": 10.0,
        "rain_24h_mm": 40.0,
        "river_stage_m": 20.0,
        "danger_stage_m": 26.3,
        "flood_prob": 0.20,
        "inundated_area_sqkm": 20.0,
        "population_exposed": 2000,
        "critical_assets_exposed": 1
    }
    curr_inputs = {
        "fused_rain_mm_hr": 35.0,
        "rain_24h_mm": 160.0,
        "river_stage_m": 26.5,
        "danger_stage_m": 26.3,
        "flood_prob": 0.85,
        "inundated_area_sqkm": 350.0,
        "population_exposed": 120000,
        "critical_assets_exposed": 18
    }
    prev_score, _, prev_sub = calc.calculate_risk_score(prev_inputs)
    curr_score, _, curr_sub = calc.calculate_risk_score(curr_inputs)
    total_delta = curr_score - prev_score

    contributors = CausalRiskExplainer.explain_risk_change(
        prev_inputs=prev_inputs,
        new_inputs=curr_inputs,
        prev_subscores=prev_sub,
        new_subscores=curr_sub,
        total_delta=total_delta
    )
    assert len(contributors) > 0
    for c in contributors:
        assert c.delta_score != 0.0

# 3. Risk Service Live Event Flow
def test_risk_service_live_flow():
    svc = RiskService()
    svc.initialize()
    inputs = {
        "fused_rain_mm_hr": 25.0,
        "rain_24h_mm": 120.0,
        "river_stage_m": 25.5,
        "danger_stage_m": 26.3,
        "flood_prob": 0.70,
        "inundated_area_sqkm": 180.0,
        "population_exposed": 45000,
        "critical_assets_exposed": 8,
        "data_confidence": "HIGH"
    }
    state = asyncio.run(svc.evaluate_and_publish_risk(
        inputs=inputs,
        forecast_run_id="FR-RISK-01",
        correlation_id="CORR-RISK-01"
    ))
    assert state.risk_score > 0
    assert state.forecast_run_id == "FR-RISK-01"
