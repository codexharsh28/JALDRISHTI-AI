"""
Unit tests for Critical Asset Exposure & Facility Attributes (Phase 15).
"""

import pytest
from services.inundation_evolution.evolution_types import InundationSnapshot
from services.inundation_evolution.impact_propagator import ImpactPropagator, MAHANADI_ASSETS

def test_mahanadi_assets_catalog_structure():
    assert len(MAHANADI_ASSETS) >= 6
    asset_types = {a["asset_type"] for a in MAHANADI_ASSETS}
    assert "HOSPITAL" in asset_types
    assert "SHELTER" in asset_types
    assert "BRIDGE" in asset_types
    assert "POWER_SUBSTATION" in asset_types

def test_hospital_and_shelter_vulnerability_derivation():
    propagator = ImpactPropagator()
    assets = propagator.evaluate_asset_exposure(
        inundated_area_sqkm=410.0,
        flood_prob=0.85,
        stage_m=27.20
    )
    scb_hosp = next((a for a in assets if "SCB" in a.asset_id), None)
    assert scb_hosp is not None
    assert scb_hosp.asset_type == "HOSPITAL"
    assert scb_hosp.depth_class in ["1-2m", ">2m"]
    assert scb_hosp.flood_probability >= 0.70
