"""
Automated Integration Tests for Phase 6 Live Data Ingestion & Operational Mode Plane.
Tests provider cadence, coalescing, locking, mock opt-in, provenance graph, and mode transitions.
"""

import pytest
import time
from fastapi.testclient import TestClient
from apps.api.main import app

from services.runtime.mode_manager import mode_manager, SystemMode, DataState
from services.scheduler.live_scheduler import live_scheduler
from services.runtime.current_state import current_state_manager
from services.ingestion.live_adapters import MockLiveProvider

client = TestClient(app)

def setup_function():
    # Reset mode manager and scheduler state before each test
    mode_manager.switch_to_simulation()
    live_scheduler._last_fetch_timestamps.clear()
    current_state_manager._is_forecast_running = False
    current_state_manager._pending_updates.clear()

def test_default_system_mode_is_simulation():
    res = client.get("/api/v1/live/status")
    assert res.status_code == 200
    data = res.json()
    assert data["system_mode"] == "SIMULATION"
    assert data["data_state"] == "SYNTHETIC"
    assert data["live_ingestion_active"] is False

def test_live_mode_safety_lock_requires_confirmation():
    # Attempting to switch without confirmation must fail
    res = client.post("/api/v1/live/connect?confirm=false")
    assert res.status_code == 400
    assert "SAFETY LOCK" in res.json()["detail"]

    # Explicit confirmation succeeds
    res_ok = client.post("/api/v1/live/connect?confirm=true")
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["status"] == "CONNECTED"
    assert data["mode_status"]["system_mode"] == "LIVE"

def test_mock_live_provider_disabled_by_default():
    mock_prov = MockLiveProvider()
    assert mock_prov.is_opted_in is False
    result = mock_prov.fetch()
    assert result.source_state == "NOT_CONFIGURED"
    assert result.ingestion_run.data_state != "LIVE_OPERATIONAL"

def test_provider_specific_cadence_enforcement():
    # First poll executes
    run1 = live_scheduler.poll_provider("IMD_ODISHA_AWS", force=False)
    assert run1 is not None
    assert run1.status in ("SUCCESS", "FAILED")
    assert run1.ingestion_run_id.startswith("ING-IMD-")

    # Immediate second poll is rate limited (min interval is 300s)
    run2 = live_scheduler.poll_provider("IMD_ODISHA_AWS", force=False)
    assert run2 is None

    # Force poll bypasses rate limiting
    run3 = live_scheduler.poll_provider("IMD_ODISHA_AWS", force=True)
    assert run3 is not None

def test_live_mode_with_degraded_data_state():
    mode_manager.switch_to_live(operator_confirmation=True)
    
    # Simulate degraded feeds (e.g. radar offline, satellite delayed)
    mock_health = {
        "IMD_AWS": "HEALTHY",
        "RADAR": "UNAVAILABLE",
        "INSAT": "NOT_CONFIGURED",
        "IMERG": "DEGRADED"
    }
    mode_manager.update_data_health_state(mock_health, confidence="LOW")
    status = mode_manager.get_status()
    assert status.system_mode == SystemMode.LIVE
    assert status.data_state == DataState.DEGRADED
    assert status.data_confidence in ["LOW", "DATA_DEGRADED"]

def test_coalesced_forecast_triggering():
    # Notify multiple sources arriving rapidly
    current_state_manager.notify_source_update("IMD_ODISHA_AWS")
    current_state_manager.notify_source_update("NASA_GPM_IMERG_EARLY")
    current_state_manager.notify_source_update("CWC_WRIS_TELEMETRY")

    # Trigger forecast once
    chain = current_state_manager.trigger_coalesced_forecast(force=True)
    assert chain is not None
    assert chain.forecast_run_id.startswith("FR-LIVE-")
    assert "IMD_ODISHA_AWS" in chain.trigger_cause or "Coalesced" in chain.trigger_cause
    assert len(chain.contributing_ingestion_runs) >= 1

def test_prevent_overlapping_forecast_runs():
    # Lock the running state
    current_state_manager._is_forecast_running = True
    result = current_state_manager.trigger_coalesced_forecast(force=False)
    assert result is None
    current_state_manager._is_forecast_running = False

def test_complete_provenance_chain_queryable():
    chain = current_state_manager.trigger_coalesced_forecast(force=True)
    assert chain is not None
    run_id = chain.forecast_run_id

    res = client.get(f"/api/v1/live/provenance/{run_id}")
    assert res.status_code == 200
    prov_data = res.json()
    assert prov_data["forecast_run_id"] == run_id
    assert "contributing_ingestion_runs" in prov_data
    assert "model_hierarchy" in prov_data
    assert "inundation_output" in prov_data
    assert "alerts_issued" in prov_data
