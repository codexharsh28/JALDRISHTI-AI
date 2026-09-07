"""
Unit tests for Causal Explainability & "Why Did Risk Change?" Decomposition.
"""

import pytest
from services.risk.causal_explainer import CausalRiskExplainer
from services.risk.risk_calculator import RiskCalculator

def test_rainfall_driven_risk_explanation():
    prev_inputs = {"rain_24h_mm": 50.0, "fused_rain_mm_hr": 10.0}
    new_inputs = {"rain_24h_mm": 180.0, "fused_rain_mm_hr": 45.0}
    prev_subscores = {"meteorological": 4.5, "hydrological": 5.0, "inundation": 3.0, "exposure": 2.0, "confidence_adjustment": 0.0}
    new_subscores = {"meteorological": 16.5, "hydrological": 5.0, "inundation": 3.0, "exposure": 2.0, "confidence_adjustment": 0.0}

    contributors = CausalRiskExplainer.explain_risk_change(
        prev_inputs=prev_inputs,
        new_inputs=new_inputs,
        prev_subscores=prev_subscores,
        new_subscores=new_subscores,
        total_delta=12.0
    )

    assert len(contributors) > 0
    top = contributors[0]
    assert top.category == "PRECIPITATION"
    assert top.direction == "INCREASING_RISK"
    assert top.delta_score == 12.0
    assert "180.0 mm/24h" in str(top.evidence_value)

def test_river_driven_risk_explanation():
    prev_inputs = {"river_stage_m": 22.5, "discharge_cumec": 8000.0}
    new_inputs = {"river_stage_m": 26.8, "discharge_cumec": 22000.0}
    prev_subscores = {"meteorological": 5.0, "hydrological": 7.0, "inundation": 4.0, "exposure": 3.0, "confidence_adjustment": 0.0}
    new_subscores = {"meteorological": 5.0, "hydrological": 22.0, "inundation": 4.0, "exposure": 3.0, "confidence_adjustment": 0.0}

    contributors = CausalRiskExplainer.explain_risk_change(
        prev_inputs=prev_inputs,
        new_inputs=new_inputs,
        prev_subscores=prev_subscores,
        new_subscores=new_subscores,
        total_delta=15.0
    )

    hydro_contrib = next((c for c in contributors if c.category == "HYDROLOGY"), None)
    assert hydro_contrib is not None
    assert hydro_contrib.delta_score == 15.0
    assert hydro_contrib.direction == "INCREASING_RISK"

def test_confidence_driven_risk_explanation():
    """
    Requirement 14: If source quality degrades, risk explanation must show:
    data confidence decreased. Do NOT attribute to rainfall.
    """
    prev_inputs = {"data_confidence": "HIGH"}
    new_inputs = {"data_confidence": "DATA_DEGRADED"}
    prev_subscores = {"meteorological": 5.0, "hydrological": 5.0, "inundation": 3.0, "exposure": 2.0, "confidence_adjustment": 0.0}
    new_subscores = {"meteorological": 5.0, "hydrological": 5.0, "inundation": 3.0, "exposure": 2.0, "confidence_adjustment": 4.0}

    contributors = CausalRiskExplainer.explain_risk_change(
        prev_inputs=prev_inputs,
        new_inputs=new_inputs,
        prev_subscores=prev_subscores,
        new_subscores=new_subscores,
        total_delta=4.0
    )

    conf_contrib = next((c for c in contributors if c.category == "CONFIDENCE"), None)
    assert conf_contrib is not None
    assert conf_contrib.delta_score == 4.0
    assert "DATA_DEGRADED" in str(conf_contrib.evidence_value)

def test_mixed_causal_contributions_ordering():
    prev_inputs = {"rain_24h_mm": 60.0, "river_stage_m": 23.0, "inundated_area_sqkm": 100.0}
    new_inputs = {"rain_24h_mm": 120.0, "river_stage_m": 25.5, "inundated_area_sqkm": 280.0}
    prev_subscores = {"meteorological": 5.0, "hydrological": 8.0, "inundation": 4.0, "exposure": 2.0, "confidence_adjustment": 0.0}
    new_subscores = {"meteorological": 10.0, "hydrological": 15.0, "inundation": 9.0, "exposure": 2.0, "confidence_adjustment": 0.0}

    contributors = CausalRiskExplainer.explain_risk_change(
        prev_inputs=prev_inputs,
        new_inputs=new_inputs,
        prev_subscores=prev_subscores,
        new_subscores=new_subscores,
        total_delta=17.0
    )

    assert len(contributors) >= 3
    # Top contributor should have the highest magnitude
    assert abs(contributors[0].delta_score) >= abs(contributors[1].delta_score)
    assert abs(contributors[1].delta_score) >= abs(contributors[2].delta_score)
