"""
Unit tests for Critical Impact Propagation & Facility Vulnerability Dynamics (Phase 15).
"""

import pytest
from services.inundation_evolution.evolution_types import InundationSnapshot, InundationDepthDistribution
from services.inundation_evolution.impact_propagator import ImpactPropagator

def test_impact_escalation_on_flood_surge():
    propagator = ImpactPropagator()
    
    # Moderate Flood State (220 sqkm)
    assets_mod = propagator.evaluate_asset_exposure(
        inundated_area_sqkm=220.0,
        flood_prob=0.65,
        stage_m=25.80,
        hydrology_source="OBSERVED_CWC"
    )
    high_risk_mod = [a for a in assets_mod if a.risk_state == "HIGH_RISK"]
    mod_risk_mod = [a for a in assets_mod if a.risk_state == "MODERATE_RISK"]
    assert len(high_risk_mod) == 0
    assert len(mod_risk_mod) > 0

    # Severe Flood Surge (450 sqkm)
    assets_sev = propagator.evaluate_asset_exposure(
        inundated_area_sqkm=450.0,
        flood_prob=0.92,
        stage_m=27.60,
        hydrology_source="OBSERVED_CWC"
    )
    high_risk_sev = [a for a in assets_sev if a.risk_state == "HIGH_RISK"]
    assert len(high_risk_sev) >= 4

def test_impact_source_degradation_labeling_glofas():
    """
    Requirement 17: When switching CWC -> GloFAS, UI and backend must indicate
    impact based on MODELED_GLOFAS and lower confidence.
    """
    propagator = ImpactPropagator()
    assets = propagator.evaluate_asset_exposure(
        inundated_area_sqkm=390.0,
        flood_prob=0.82,
        stage_m=26.90,
        hydrology_source="GLOFAS_ECMWF_SURROGATE"
    )
    for a in assets:
        assert a.dataset_state == "MODELED_GLOFAS"
        assert a.confidence == "DATA_DEGRADED"
        assert "MODELED_GLOFAS" in a.mitigation_protocol
