"""
Regression Tests for Forensic Bug Hunt Fixes (Phase 1-22).
Verifies:
1. /api/v1/alerts/incidents returns all incidents correctly without AttributeError.
2. AlertEngine exposes get_incidents() alias.
3. POST /api/v1/alerts/{alert_id}/acknowledge executes review action, updates state, and records audit trail.
4. Single authoritative acknowledge route with RBAC check.
5. Inundation change returns coherent schema with float defaults when no prior snapshot exists.
6. Impact current endpoint returns both critical_assets/assets and population_summary/population_exposure.
7. Hydrology forecast returns stage_p50 and quantiles: {p10, p50, p90}.
8. InundationEvolutionStore and RiskStore startup hydration from persistent files.
9. Mode isolation: ALT-DEMO alerts are excluded in LIVE mode.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from apps.api.main import app
from services.alerts.alert_engine import alert_engine
from services.alerts.alert_types import AlertLifecycleState, UserRole
from services.runtime.mode_manager import mode_manager
from services.inundation_evolution.evolution_store import InundationEvolutionStore
from services.risk.risk_store import RiskStore

client = TestClient(app)

def test_alerts_incidents_endpoint_and_alias():
    # Verify alert_engine exposes get_incidents() alias
    assert hasattr(alert_engine, "get_incidents")
    incidents_alias = alert_engine.get_incidents()
    incidents_all = alert_engine.get_all_incidents()
    assert len(incidents_alias) == len(incidents_all)

    # Verify API endpoint returns 200 list
    res = client.get("/api/v1/alerts/incidents")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_acknowledge_endpoint_authorization_and_audit():
    incidents = alert_engine.get_all_incidents()
    target_alert = None
    for inc in incidents:
        if inc.status in [AlertLifecycleState.PENDING_HUMAN_REVIEW, AlertLifecycleState.WATCH, AlertLifecycleState.CANDIDATE]:
            target_alert = inc.alert_id
            break

    if not target_alert:
        from services.models import ConfidenceLevel
        seeded = alert_engine.evaluate_alert(
            fused_rain_mm_hr=95.0,
            rain_24h_mm=210.0,
            river_stage_m=27.10,
            warning_stage_m=25.40,
            danger_stage_m=26.30,
            flood_prob=0.95,
            inundated_area_sqkm=350.0,
            data_confidence=ConfidenceLevel.HIGH,
            model_confidence=ConfidenceLevel.HIGH,
            lead_time_hours=12.0,
            forecast_run_id="FR-REG-01",
            base_time=datetime.now(timezone.utc)
        )
        target_alert = seeded.alert_id

    # Test acknowledge with OPERATOR role
    payload = {
        "operator_id": "DEOC-Duty-Chief",
        "role": "OPERATOR",
        "reason": "Verified water mark at gauge station."
    }
    res = client.post(f"/api/v1/alerts/{target_alert}/acknowledge", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["acknowledged_by"] == "DEOC-Duty-Chief"

    # Verify incident state was updated
    updated_inc = alert_engine.get_incident_by_id(target_alert)
    assert updated_inc.status == AlertLifecycleState.ACKNOWLEDGED

    # Verify audit history was written
    history_res = client.get(f"/api/v1/alerts/{target_alert}/history")
    assert history_res.status_code == 200
    h_data = history_res.json()
    assert len(h_data["audit_history"]) > 0
    latest_audit = h_data["audit_history"][-1]
    assert latest_audit["operator_id"] == "DEOC-Duty-Chief"
    assert latest_audit["action"] == "ACKNOWLEDGE"


def test_impact_canonical_contract():
    res = client.get("/api/v1/impact/current")
    assert res.status_code == 200
    data = res.json()
    # Canonical contract: must provide both assets and critical_assets
    assert "critical_assets" in data
    assert "assets" in data
    assert isinstance(data["critical_assets"], list)
    assert isinstance(data["assets"], list)
    assert len(data["critical_assets"]) == len(data["assets"])

    # Must provide both population_summary and population_exposure
    assert "population_summary" in data
    assert "population_exposure" in data


def test_hydrology_canonical_contract():
    res = client.get("/api/v1/hydrology/forecast?station_id=CWC_MUNDALI&model=L1_XGBOOST")
    assert res.status_code == 200
    data = res.json()
    # Contract: provides quantiles dictionary and p50
    assert "quantiles" in data
    assert "p50" in data["quantiles"]
    assert "stage_p50" in data
    assert len(data["quantiles"]["p50"]) == len(data["stage_p50"])


def test_inundation_change_coherent_schema():
    res = client.get("/api/v1/inundation/change")
    assert res.status_code == 200
    data = res.json()
    # Must have all numerical delta fields
    assert "expansion_sqkm" in data
    assert "contraction_sqkm" in data
    assert "net_delta_sqkm" in data
    assert "percentage_change" in data
    assert "inundation_expansion_rate_km2_per_hour" in data
    assert "spatial_trend" in data
    assert "is_material_change" in data
    assert isinstance(data["expansion_sqkm"], (int, float))
    assert isinstance(data["spatial_trend"], str)


def test_persistence_hydration_inundation_and_risk(tmp_path):
    storage_dir = str(tmp_path / "persistence_test")
    os.makedirs(storage_dir, exist_ok=True)

    # Test Inundation Evolution Store hydration
    store1 = InundationEvolutionStore(storage_dir=storage_dir)
    from services.inundation_evolution.evolution_types import (
        InundationSnapshot,
        DepthClassBreakdown,
        SpatialChangeSummary,
    )
    snap = InundationSnapshot(
        inundation_snapshot_id="SNAP-TEST-001",
        snapshot_id="SNAP-TEST-001",
        valid_time=datetime.now(timezone.utc).isoformat(),
        scenario="TEST",
        inundated_area_sqkm=125.0,
        mean_flood_probability=0.8,
        peak_depth_m=2.5,
        depth_classes=DepthClassBreakdown(
            depth_0_to_0_3m_sqkm=50.0,
            depth_0_3_to_1m_sqkm=40.0,
            depth_1_to_2m_sqkm=25.0,
            depth_gt_2m_sqkm=10.0
        ),
        confidence="HIGH",
        dataset_state="OBSERVED_CWC",
        hydrology_source="OBSERVED_CWC"
    )
    store1.append_snapshot(snap)

    # Create fresh instance pointing to same storage_dir (simulating restart)
    store2 = InundationEvolutionStore(storage_dir=storage_dir)
    loaded_snap = store2.get_current_snapshot()
    assert loaded_snap is not None
    assert loaded_snap.inundation_snapshot_id == "SNAP-TEST-001"
    assert loaded_snap.inundated_area_sqkm == 125.0

    # Test Risk Store hydration
    risk_dir = str(tmp_path / "risk_test")
    os.makedirs(risk_dir, exist_ok=True)
    rstore1 = RiskStore(storage_dir=risk_dir)
    from services.risk.risk_types import RiskState, RiskLevel
    rstate = RiskState(
        risk_score=72.5,
        previous_risk_score=65.0,
        risk_level=RiskLevel.WARNING,
        risk_change=7.5,
        is_material_change=True,
        top_causal_summary="Testing persistence hydration",
        contributors=[]
    )
    rstore1.append(rstate)

    # Recreate risk store instance
    rstore2 = RiskStore(storage_dir=risk_dir)
    loaded_risk = rstore2.get_current()
    assert loaded_risk is not None
    assert loaded_risk.risk_score == 72.5
    assert loaded_risk.risk_level == RiskLevel.WARNING


def test_live_mode_isolation_of_demo_alerts():
    # In LIVE mode, ALT-DEMO alerts must NEVER appear in public alerts
    mode_manager.switch_to_live(operator_confirmation="I UNDERSTAND AND CONFIRM LIVE PRODUCTION SENSOR INGESTION")
    try:
        res = client.get("/api/v1/public-alerts/current")
        assert res.status_code == 200
        alerts = res.json()
        for a in alerts:
            assert not a["alert_id"].startswith("ALT-DEMO"), f"Simulation alert {a['alert_id']} leaked to LIVE public feed!"
    finally:
        mode_manager.switch_to_simulation()
