"""
Unit tests for Admin Navigation & Backend Authorization.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.security import TokenManager

client = TestClient(app)

def test_admin_endpoint_unauthorized_without_token():
    res = client.get("/api/v1/security/status")
    assert res.status_code == 401
    data = res.json()
    assert "detail" in data

def test_admin_endpoint_forbidden_for_public_citizen():
    public_token, _ = TokenManager.create_access_token(user_id="user-citizen-01", role="PUBLIC_USER")
    res = client.get("/api/v1/security/status", headers={"Authorization": f"Bearer {public_token}"})
    assert res.status_code == 403
    data = res.json()
    assert "detail" in data

def test_admin_endpoint_authorized_for_admin():
    admin_token, _ = TokenManager.create_access_token(user_id="admin-operator-01", role="ADMIN")
    res = client.get("/api/v1/security/status", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HARDENED"
    assert "rate_limits" in data
    assert "dlt_configuration" in data
