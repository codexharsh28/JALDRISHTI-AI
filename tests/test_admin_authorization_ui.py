"""
Integration tests for Admin Authorization UI contracts.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.security import TokenManager

client = TestClient(app)

def test_admin_rbac_role_detection():
    # Operator token
    op_token, _ = TokenManager.create_access_token(user_id="op-01", role="OPERATOR")
    res = client.get("/api/v1/security/status", headers={"Authorization": f"Bearer {op_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["rbac_role"] in ["OPERATOR", "ADMIN"]

def test_forged_admin_token_rejected():
    forged_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJBRE1JTiJ9.INVALID_SIGNATURE"
    res = client.get("/api/v1/security/status", headers={"Authorization": f"Bearer {forged_token}"})
    assert res.status_code in [401, 403]

import os
def test_admin_login_and_logout_endpoints():
    # Valid login
    valid_pass = os.getenv("ADMIN_PASSWORD", "admin_dev_pass_2026")
    login_res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": valid_pass,
        "requested_role": "ADMIN"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["role"] == "ADMIN"

    token = login_data["access_token"]

    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "SUCCESS"

def test_admin_observability_endpoints():
    token, _ = TokenManager.create_access_token(user_id="admin-01", role="ADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Database stats
    db_res = client.get("/api/v1/admin/database/stats", headers=headers)
    assert db_res.status_code == 200
    assert "table_stats" in db_res.json()
    assert "engine" in db_res.json()

    # 2. Event bus metrics
    eb_res = client.get("/api/v1/admin/event-bus/metrics", headers=headers)
    assert eb_res.status_code == 200
    assert "total_events_stored" in eb_res.json()

    # 3. WebSocket metrics
    ws_res = client.get("/api/v1/admin/websocket/metrics", headers=headers)
    assert ws_res.status_code == 200
    assert "active_connections" in ws_res.json()
    assert ws_res.json()["max_connection_limit"] == 100

    # 4. Models catalog
    mod_res = client.get("/api/v1/admin/models/catalog", headers=headers)
    assert mod_res.status_code == 200
    assert len(mod_res.json()["models"]) >= 4

def test_human_review_action_validation():
    token, _ = TokenManager.create_access_token(user_id="op-02", role="OPERATOR")
    headers = {"Authorization": f"Bearer {token}"}

    # Missing reason
    res_bad = client.post("/api/v1/admin/human-review/action", headers=headers, json={
        "alert_id": "ALT-TEST-01",
        "action": "ACKNOWLEDGE",
        "reason": ""
    })
    assert res_bad.status_code == 400

    # Valid acknowledge with reason
    res_ok = client.post("/api/v1/admin/human-review/action", headers=headers, json={
        "alert_id": "ALT-TEST-01",
        "action": "ACKNOWLEDGE",
        "reason": "Verified water level cresting below danger mark by field team"
    })
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "SUCCESS"
