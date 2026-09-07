"""
Unit tests for Inundation Spatial Differencing & Flood Rate of Change (Phase 15).
"""

import pytest
from services.inundation_evolution.evolution_types import InundationSnapshot, InundationDepthDistribution
from services.inundation_evolution.differencing_engine import (
    InundationDifferencingEngine,
    MIN_AREA_DELTA_SQKM,
    MIN_PROB_DELTA
)

def test_flood_expansion_calculation():
    prev = InundationSnapshot(
        inundation_snapshot_id="SNAP-PREV-01",
        inundated_area_sqkm=250.0,
        mean_flood_probability=0.60
    )
    curr = InundationSnapshot(
        inundation_snapshot_id="SNAP-CURR-01",
        inundated_area_sqkm=310.0,
        mean_flood_probability=0.75
    )

    diff = InundationDifferencingEngine.compute_spatial_change(curr, prev, elapsed_hours=2.0)
    assert diff.expansion_sqkm == 60.0
    assert diff.contraction_sqkm == 0.0
    assert diff.net_delta_sqkm == 60.0
    assert diff.spatial_trend == "EXPANDING"
    assert diff.inundation_expansion_rate_km2_per_hour == 30.0
    assert diff.is_material_change is True

def test_flood_contraction_recession_calculation():
    prev = InundationSnapshot(
        inundation_snapshot_id="SNAP-PREV-02",
        inundated_area_sqkm=420.0,
        mean_flood_probability=0.88
    )
    curr = InundationSnapshot(
        inundation_snapshot_id="SNAP-CURR-02",
        inundated_area_sqkm=380.0,
        mean_flood_probability=0.80
    )

    diff = InundationDifferencingEngine.compute_spatial_change(curr, prev, elapsed_hours=1.0)
    assert diff.expansion_sqkm == 0.0
    assert diff.contraction_sqkm == 40.0
    assert diff.net_delta_sqkm == -40.0
    assert diff.spatial_trend == "CONTRACTING"
    assert diff.inundation_expansion_rate_km2_per_hour == -40.0
    assert diff.is_material_change is True

def test_sub_threshold_stability_noise_suppression():
    prev = InundationSnapshot(
        inundation_snapshot_id="SNAP-PREV-03",
        inundated_area_sqkm=300.0,
        mean_flood_probability=0.70
    )
    curr = InundationSnapshot(
        inundation_snapshot_id="SNAP-CURR-03",
        inundated_area_sqkm=300.8,
        mean_flood_probability=0.71
    )

    diff = InundationDifferencingEngine.compute_spatial_change(curr, prev, elapsed_hours=1.0)
    assert diff.net_delta_sqkm == 0.8
    assert diff.spatial_trend == "STABLE"
    assert diff.is_material_change is False
