"""
Role-Based Access Control (RBAC) & Privilege Escalation Tests.
Proves that PUBLIC_USER cannot access ADMIN security endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.security import token_manager

client = TestClient(app)

def test_public_user_cannot_access_admin_security_status():
    token, _ = token_manager.create_access_token(user_id="USR-PUB-01", role="PUBLIC_USER")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/v1/security/status", headers=headers)
    assert res.status_code == 403
    assert "Administrator privilege required" in res.json()["detail"]

def test_admin_can_access_security_status():
    token, _ = token_manager.create_access_token(user_id="USR-ADMIN-01", role="ADMIN")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/v1/security/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HARDENED"
    assert "total_audit_events" in data
    assert "blocked_security_events" in data
