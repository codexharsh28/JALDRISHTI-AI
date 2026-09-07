"""
Unit tests for Population Exposure & WorldPop Integration (Phase 15).
"""

import pytest
from services.inundation_evolution.impact_propagator import ImpactPropagator

def test_population_exposed_now_and_forecast():
    propagator = ImpactPropagator()
    pop = propagator.evaluate_population_exposure(
        inundated_area_sqkm=350.0,
        flood_prob=0.80,
        previous_population_exposed=65000
    )
    assert pop.population_exposed_now > 80000
    assert pop.population_exposed_forecast >= pop.population_exposed_now
    assert pop.newly_exposed_population > 0
    assert "WorldPop" in pop.data_source

def test_population_exposure_with_glofas_degradation():
    propagator = ImpactPropagator()
    pop = propagator.evaluate_population_exposure(
        inundated_area_sqkm=350.0,
        flood_prob=0.80,
        hydrology_source="GLOFAS"
    )
    assert pop.dataset_state == "MODELED_GLOFAS"
