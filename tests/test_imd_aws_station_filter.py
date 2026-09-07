"""
Unit tests for geospatial basin containment and station discovery filtering.
"""

import pytest
from services.ingestion.live_adapters import IMDLiveAdapter

def test_compute_basin_geometry_inside_mahanadi():
    adapter = IMDLiveAdapter()
    # Cuttack coordinates: inside pilot basin
    inside, dist_km, subbasin = adapter.compute_basin_geometry(lat=20.462, lon=85.882)
    assert inside is True
    assert dist_km == 0.0
    assert subbasin == "sub-central-cuttack"

def test_compute_basin_geometry_outside_mahanadi():
    adapter = IMDLiveAdapter()
    # Rourkela / Sundargarh coordinates: outside pilot delta polygon
    inside, dist_km, subbasin = adapter.compute_basin_geometry(lat=22.260, lon=84.853)
    assert inside is False
    assert dist_km > 50.0
    assert subbasin is None
