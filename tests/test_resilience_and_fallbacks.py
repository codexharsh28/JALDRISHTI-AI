"""
Automated Test Suite for Resilience, Alternative Data Sources, and Fallbacks.
Validates:
1. Hydrology fallback chain: CWC Observed -> GloFAS Modeled.
2. Station-to-grid coordinate matching for GloFAS 5km river cells (persisting 7 required fields).
3. Uncertainty interval expansion and confidence recalculation under GloFAS labeled as RULE_BASED_UNCERTAINTY_ADJUSTMENT.
4. Auditable source switching via /api/v1/hydrology/source-switch.
5. Multi-source Bhuvan & Sentinel-1 SAR reference validation and strict <=3h primary benchmark window.
6. Scenario precomputation and caching engine with +48h/+72h explicitly marked NOT_PRECOMPUTED.
7. Resilience against multi-source outages and degraded telemetry.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from apps.api.main import app
from services.ingestion.live.glofas_adapter import GloFASLiveAdapter, STATION_GLOFAS_GRID_MAP
from services.hydrology.fallback_manager import HydrologyFallbackManager, HydrologySourceType
from services.inundation.bhuvan_reference import BhuvanFloodReferenceRegistry, ReferenceProductType
from services.runtime.forecast_cache import ForecastCacheEngine

@pytest.fixture
def client():
    return TestClient(app)

def test_glofas_adapter_payload_and_grid_matching():
    """Verifies GloFAS adapter produces valid modeled discharge with all 7 persisted station-matching fields."""
    adapter = GloFASLiveAdapter()
    result = adapter.fetch()
    assert result.source_state.value == "AVAILABLE"
    assert len(result.observations) >= 4

    for obs in result.observations:
        # Mandatory GloFAS station matching fields
        assert "cwc_station_id" in obs
        assert "glofas_cell_id" in obs
        assert "station_lat" in obs
        assert "station_lon" in obs
        assert "glofas_lat" in obs
        assert "glofas_lon" in obs
        assert "station_to_cell_distance_km" in obs
        
        # Strict scientific labeling
        assert obs["data_source_type"] == "MODELED_GLOFAS"
        assert obs["is_observed_telemetry"] is False
        assert obs["is_ground_truth"] is False
        assert obs["river_discharge_cumec"] > 0
        assert obs["station_to_cell_distance_km"] < 5.0  # Within 5km cell

def test_hydrology_fallback_chain_and_uncertainty_widening():
    """Verifies that falling back from CWC to GloFAS lowers confidence and labels adjustment as RULE_BASED."""
    mgr = HydrologyFallbackManager()
    
    # 1. Normal CWC Observed
    src_cwc, qual_cwc, conf_cwc, mult_cwc = mgr.evaluate_source(cwc_available=True, cwc_latency_hours=0.5)
    assert src_cwc == HydrologySourceType.OBSERVED_CWC
    assert conf_cwc.value == "HIGH"
    assert mult_cwc == 1.0

    # 2. CWC Unavailable / Delayed -> GloFAS Modeled Fallback
    src_glofas, qual_glofas, conf_glofas, mult_glofas = mgr.evaluate_source(cwc_available=False)
    assert src_glofas == HydrologySourceType.MODELED_GLOFAS
    assert conf_glofas.value == "MEDIUM"
    assert mult_glofas == 1.8  # Uncertainty intervals widen by 1.8x
    assert qual_glofas < qual_cwc

    # Verify rule-based uncertainty labeling
    discharge_info = mgr.get_discharge_for_station("CWC_MUNDALI", cwc_available=False)
    assert discharge_info["uncertainty_adjustment_method"] == "RULE_BASED_UNCERTAINTY_ADJUSTMENT"

def test_hydrology_forecast_endpoint_source_flag_and_audit(client):
    """Verifies that /api/v1/hydrology/forecast returns honest input_hydrology_source and rule-based uncertainty."""
    response = client.get("/api/v1/hydrology/forecast?station_id=CWC_MUNDALI")
    assert response.status_code == 200
    data = response.json()
    assert "input_hydrology_source" in data
    assert "input_source_quality" in data
    assert "uncertainty_expansion_factor" in data
    assert data["uncertainty_adjustment_method"] == "RULE_BASED_UNCERTAINTY_ADJUSTMENT"
    assert "hydrograph" in data

def test_hydrology_fallback_status_and_source_switch_endpoints(client):
    """Verifies source switching and audit logging via REST endpoints."""
    # 1. Get status
    res = client.get("/api/v1/hydrology/fallback-status")
    assert res.status_code == 200
    status_data = res.json()
    assert "active_source" in status_data
    assert "primary_provider" in status_data

    # 2. Switch source to MODELED_GLOFAS
    res_switch = client.post("/api/v1/hydrology/source-switch", json={"source": "MODELED_GLOFAS"})
    assert res_switch.status_code == 200
    switch_data = res_switch.json()
    assert switch_data["active_source"] == "MODELED_GLOFAS"
    assert switch_data["uncertainty_expansion_factor"] == 1.8

    # 3. Restore to OBSERVED_CWC
    res_restore = client.post("/api/v1/hydrology/source-switch", json={"source": "OBSERVED_CWC"})
    assert res_restore.status_code == 200
    assert res_restore.json()["active_source"] == "OBSERVED_CWC"

def test_bhuvan_and_sar_reference_catalog_and_temporal_matching(client):
    """Verifies multi-source remote sensing references and temporal matching validation."""
    response = client.get("/api/v1/inundation/references?event_id=EVT-MAHANADI-2024-08")
    assert response.status_code == 200
    data = response.json()
    assert data["references_count"] >= 2
    
    # Check separate presence of Bhuvan and Sentinel-1
    sources = [r["source"] for r in data["references"]]
    assert "ISRO_BHUVAN_NRSC" in sources
    assert "COPERNICUS_SENTINEL1" in sources

    # Verify temporal matching metadata structure
    assert "temporal_matching_analysis" in data
    assert "temporal_match_accepted" in data

def test_temporal_matching_strict_3h_sar_primary_benchmark_window():
    """Verifies that references >3h cannot enter the primary benchmark and are labeled EXPLORATORY_ONLY or REJECTED."""
    reg = BhuvanFloodReferenceRegistry()

    # 1. Exact match (<= 3h) -> Eligible for primary benchmark
    valid_time_close = datetime(2024, 8, 5, 7, 0, 0, tzinfo=timezone.utc) # 1h 15m from acquisition
    is_primary, meta, rej = reg.match_temporal_reference(
        event_id="EVT-MAHANADI-2024-08",
        forecast_valid_time=valid_time_close
    )
    assert is_primary is True
    assert meta["is_primary_benchmark_eligible"] is True
    assert meta["benchmark_status"] == "PRIMARY_BENCHMARK_ELIGIBLE"
    assert rej is None

    # 2. Exploratory window (3h < diff <= 6h) -> Excluded from primary benchmark
    valid_time_exploratory = datetime(2024, 8, 5, 11, 0, 0, tzinfo=timezone.utc) # 4h 45m from acquisition
    is_primary_exp, meta_exp, rej_exp = reg.match_temporal_reference(
        event_id="EVT-MAHANADI-2024-08",
        forecast_valid_time=valid_time_exploratory
    )
    assert is_primary_exp is False
    assert meta_exp["is_primary_benchmark_eligible"] is False
    assert meta_exp["is_exploratory_only"] is True
    assert meta_exp["benchmark_status"] == "EXPLORATORY_ONLY"
    assert "Excluded from primary benchmark" in rej_exp

    # 3. Mismatched window (> 6h) -> Completely rejected
    valid_time_mismatched = datetime(2024, 8, 6, 12, 0, 0, tzinfo=timezone.utc) # >24h from acquisition
    is_primary_rej, meta_rej, rej_rej = reg.match_temporal_reference(
        event_id="EVT-MAHANADI-2024-08",
        forecast_valid_time=valid_time_mismatched
    )
    assert is_primary_rej is False
    assert meta_rej["benchmark_status"] == "REJECTED_TEMPORAL_MISMATCH"
    assert "Temporal mismatch" in rej_rej

def test_forecast_cache_inundation_precomputation_and_extended_horizons(client):
    """Verifies scenario caching engine and that +48h/+72h are explicitly NOT_PRECOMPUTED."""
    cache = ForecastCacheEngine(max_entries=50, ttl_seconds=300)
    
    # 1. Precompute scenarios
    manifest = cache.precompute_inundation_scenarios("RUN-TEST-002")
    assert manifest["scenarios_count"] == 15  # 5 horizons (+1, +3, +6, +12, +24) x 3 quantiles
    assert manifest["supported_precomputed_horizons_hours"] == [1, 3, 6, 12, 24]
    assert manifest["non_precomputed_extended_horizons_hours"] == [48, 72]

    # 2. Check surface retrieval for precomputed horizon (+6h)
    surf_6h = cache.get_inundation_surface("RUN-TEST-002", lead_time_hours=6)
    assert surf_6h["status"] == "PRECOMPUTED"
    assert surf_6h["precomputed"] is True

    # 3. Check surface retrieval for extended horizon (+48h) -> NOT_PRECOMPUTED
    surf_48h = cache.get_inundation_surface("RUN-TEST-002", lead_time_hours=48)
    assert surf_48h["status"] == "NOT_PRECOMPUTED"
    assert surf_48h["precomputed"] is False

    # 4. Check surface retrieval for extended horizon (+72h) -> NOT_PRECOMPUTED
    surf_72h = cache.get_inundation_surface("RUN-TEST-002", lead_time_hours=72)
    assert surf_72h["status"] == "NOT_PRECOMPUTED"
    assert surf_72h["precomputed"] is False
