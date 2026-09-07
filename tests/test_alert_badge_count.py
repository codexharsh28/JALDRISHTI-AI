"""
Authoritative Test Suite for Alert & Warning Badge Count Integrity.
Validates single source of truth, lifecycle state exclusions, deduplication, and demo reset.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.alerts.alert_engine import AlertEngine, alert_engine
from services.alerts.alert_types import AlertLifecycleState, OperatorAction, UserRole, AlertIncident
from services.demo.demo_orchestrator import demo_orchestrator

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_alert_state():
    """Ensure clean alert state before and after each test."""
    alert_engine.clear_incidents()
    demo_orchestrator.reset_demo()
    yield
    alert_engine.clear_incidents()
    demo_orchestrator.reset_demo()

def test_zero_active_alerts_summary():
    """When no active incidents exist, badge counts must be strictly 0."""
    res = client.get("/api/v1/alerts/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["active_alerts"] == 0
    assert data["active_warnings"] == 0
    assert data["active_critical"] == 0
    assert data["active_high_risk"] == 0
    assert data["total_active"] == 0

def test_single_active_alert_count():
    """Single active critical incident should produce active_alerts = 1."""
    alert_engine.transition_state("ALT-TEST-01", AlertLifecycleState.PENDING_HUMAN_REVIEW)
    inc = alert_engine.get_incident_by_id("ALT-TEST-01")
    assert inc is not None
    inc.severity = "RED"

    res = client.get("/api/v1/alerts/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["active_alerts"] == 1
    assert data["active_critical"] == 1
    assert data["active_warnings"] == 0
    assert data["total_active"] == 1

def test_multiple_active_incidents_count():
    """Multiple distinct active incidents produce accurate severity breakdown."""
    # 1. Critical RED
    alert_engine.transition_state("ALT-RED-01", AlertLifecycleState.PENDING_HUMAN_REVIEW)
    inc1 = alert_engine.get_incident_by_id("ALT-RED-01")
    inc1.severity = "RED"

    # 2. High Risk ORANGE
    alert_engine.transition_state("ALT-ORANGE-01", AlertLifecycleState.ACKNOWLEDGED)
    inc2 = alert_engine.get_incident_by_id("ALT-ORANGE-01")
    inc2.severity = "ORANGE"

    # 3. Advisory YELLOW / WATCH
    alert_engine.transition_state("ALT-YELLOW-01", AlertLifecycleState.WATCH)
    inc3 = alert_engine.get_incident_by_id("ALT-YELLOW-01")
    inc3.severity = "YELLOW"

    res = client.get("/api/v1/alerts/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["active_alerts"] == 2 # RED + ORANGE
    assert data["active_critical"] == 1
    assert data["active_high_risk"] == 1
    assert data["active_warnings"] == 1 # YELLOW
    assert data["total_active"] == 3

def test_state_transition_does_not_duplicate_count():
    """When a single incident undergoes state transitions, badge count remains 1."""
    alert_id = "ALT-EVOLVING-01"
    
    # 1. Candidate
    alert_engine.transition_state(alert_id, AlertLifecycleState.CANDIDATE)
    inc = alert_engine.get_incident_by_id(alert_id)
    inc.severity = "ORANGE"
    
    res1 = client.get("/api/v1/alerts/summary")
    assert res1.json()["active_alerts"] == 1

    # 2. Escalated to RED
    alert_engine.transition_state(alert_id, AlertLifecycleState.ESCALATED)
    inc.severity = "RED"
    res2 = client.get("/api/v1/alerts/summary")
    assert res2.json()["active_alerts"] == 1
    assert res2.json()["active_critical"] == 1

    # 3. Acknowledged
    alert_engine.transition_state(alert_id, AlertLifecycleState.ACKNOWLEDGED)
    res3 = client.get("/api/v1/alerts/summary")
    assert res3.json()["active_alerts"] == 1

def test_dismissed_and_expired_incidents_excluded():
    """Dismissed, Expired, and Suppressed incidents MUST be excluded from badge count."""
    # Active incident
    alert_engine.transition_state("ALT-ACTIVE", AlertLifecycleState.ACKNOWLEDGED)
    inc_act = alert_engine.get_incident_by_id("ALT-ACTIVE")
    inc_act.severity = "RED"

    # Dismissed incident
    alert_engine.transition_state("ALT-DISMISSED", AlertLifecycleState.DISMISSED)
    inc_dis = alert_engine.get_incident_by_id("ALT-DISMISSED")
    inc_dis.severity = "RED"

    # Expired incident
    alert_engine.transition_state("ALT-EXPIRED", AlertLifecycleState.EXPIRED)
    inc_exp = alert_engine.get_incident_by_id("ALT-EXPIRED")
    inc_exp.severity = "ORANGE"

    # Suppressed incident
    alert_engine.transition_state("ALT-SUPPRESSED", AlertLifecycleState.SUPPRESSED)
    inc_sup = alert_engine.get_incident_by_id("ALT-SUPPRESSED")
    inc_sup.severity = "ORANGE"

    res = client.get("/api/v1/alerts/summary")
    data = res.json()
    assert data["active_alerts"] == 1
    assert data["total_active"] == 1

def test_demo_scenario_lifecycle_and_reset():
    """Demo scenario steps evolve alerts and demo reset clears them completely."""
    # Start demo
    demo_orchestrator.start_demo()
    
    # Stage 0: Calm baseline -> active count = 0
    res0 = client.get("/api/v1/alerts/summary")
    assert res0.json()["active_alerts"] == 0
    assert res0.json()["mode"] == "SIMULATION"

    # Step forward to Stage 4 (Inflow rising, ORANGE alert)
    for _ in range(4):
        demo_orchestrator.step_forward()

    res_stg4 = client.get("/api/v1/alerts/summary")
    assert res_stg4.json()["active_alerts"] == 1
    assert res_stg4.json()["active_high_risk"] == 1

    # Step forward to Stage 7 (Danger crossing, RED alert)
    for _ in range(3):
        demo_orchestrator.step_forward()

    res_stg7 = client.get("/api/v1/alerts/summary")
    assert res_stg7.json()["active_alerts"] == 1
    assert res_stg7.json()["active_critical"] == 1

    # Reset demo -> should clear synthetic demo alerts back to baseline 0
    demo_orchestrator.reset_demo()
    res_reset = client.get("/api/v1/alerts/summary")
    assert res_reset.json()["active_alerts"] == 0
    assert res_reset.json()["total_active"] == 0

def test_client_cannot_tamper_alert_count():
    """Summary is strictly computed backend-side and read-only."""
    # Attempting to POST or PUT to /summary fails
    res = client.post("/api/v1/alerts/summary", json={"active_alerts": 999})
    assert res.status_code in [404, 405]
