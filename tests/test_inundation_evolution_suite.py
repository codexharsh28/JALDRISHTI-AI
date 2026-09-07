"""
Inundation Evolution & Impact Tests: Spatial Differencing, Asset Exposure, Population Overlay, and Modeled GloFAS Provenance.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from services.inundation_evolution.differencing_engine import InundationDifferencingEngine
from services.inundation_evolution.impact_propagator import ImpactPropagator
from services.inundation_evolution.evolution_service import InundationEvolutionService
from services.inundation_evolution.evolution_types import InundationSnapshot

# 1. Spatial Differencing (Expansion & Contraction)
def test_spatial_differencing_expansion():
    prev_snap = InundationSnapshot(
        forecast_run_id="FR-01",
        inundated_area_sqkm=250.0,
        flood_prob_mean=0.60
    )
    curr_snap = InundationSnapshot(
        forecast_run_id="FR-02",
        inundated_area_sqkm=310.0,
        flood_prob_mean=0.75
    )
    summary = InundationDifferencingEngine.compute_spatial_change(curr_snap, prev_snap, elapsed_hours=1.0)
    assert summary.spatial_trend == "EXPANDING"
    assert summary.net_change_sqkm == 60.0
    assert summary.rate_of_expansion_sqkm_per_hr == 60.0

def test_spatial_differencing_contraction():
    prev_snap = InundationSnapshot(
        forecast_run_id="FR-01",
        inundated_area_sqkm=300.0,
        flood_prob_mean=0.70
    )
    curr_snap = InundationSnapshot(
        forecast_run_id="FR-02",
        inundated_area_sqkm=240.0,
        flood_prob_mean=0.55
    )
    summary = InundationDifferencingEngine.compute_spatial_change(curr_snap, prev_snap, elapsed_hours=1.0)
    assert summary.spatial_trend == "CONTRACTING"
    assert summary.net_change_sqkm == -60.0

# 2. Critical Asset & Population Exposure
def test_impact_propagator_assets():
    propagator = ImpactPropagator()
    assets = propagator.evaluate_asset_exposure(
        inundated_area_sqkm=350.0,
        flood_prob=0.85,
        stage_m=27.10
    )
    assert len(assets) > 0
    scb_hospital = next((a for a in assets if "SCB Medical" in a.asset_name), None)
    assert scb_hospital is not None
    assert scb_hospital.risk_state in ["HIGH_RISK", "CRITICAL_THREAT"]

def test_impact_propagator_modeled_glofas_provenance():
    propagator = ImpactPropagator()
    assets = propagator.evaluate_asset_exposure(
        inundated_area_sqkm=350.0,
        flood_prob=0.85,
        stage_m=27.10,
        hydrology_source="MODELED_GLOFAS"
    )
    # Must explicitly state MODELED_GLOFAS
    for a in assets:
        assert a.dataset_state == "MODELED_GLOFAS"
        assert "MODELED_GLOFAS" in a.mitigation_protocol

def test_impact_propagator_population():
    propagator = ImpactPropagator()
    pop_summary = propagator.evaluate_population_exposure(
        inundated_area_sqkm=418.8,
        flood_prob=0.88,
        previous_population_exposed=95000,
        hydrology_source="MODELED_GLOFAS"
    )
    assert pop_summary.population_exposed_forecast > 100000
    assert pop_summary.newly_exposed_population > 0
    assert pop_summary.dataset_state == "MODELED_GLOFAS"

# 3. Live Inundation Evolution Flow
def test_live_inundation_evolution_flow():
    svc = InundationEvolutionService()
    svc.initialize()
    curr_snap, change, assets, pop = asyncio.run(svc.process_new_inundation(
        forecast_run_id="FR-EVOL-01",
        inundated_area_sqkm=380.0,
        flood_prob=0.82,
        stage_m=26.80,
        hydrology_source="OBSERVED_CWC"
    ))
    assert curr_snap.inundated_area_sqkm == 380.0
    assert len(assets) > 0
    assert pop.population_exposed_forecast > 0
