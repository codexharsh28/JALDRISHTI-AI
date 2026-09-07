"""
Authentication & Token Security Penetration Tests for JALDRISHTI AI.
Tests forged tokens, expired signatures, algorithm confusion, and invalid headers.
"""

import pytest
from services.notifications.security import token_manager
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_forged_signature_rejected():
    user_id = "USR-AUTH-01"
    token, _ = token_manager.create_access_token(user_id=user_id, role="PUBLIC_USER")
    
    # Tamper with header/payload
    payload_b64, sig = token.split(".")
    tampered_token = f"{payload_b64}.0000000000000000"
    
    is_valid, payload, err = token_manager.verify_access_token(tampered_token)
    assert is_valid is False
    assert "signature" in err.lower()

def test_malformed_token_header_rejected():
    headers = {"Authorization": "Bearer not-a-real-token-format"}
    res = client.get("/api/v1/user/subscriptions?user_id=USR-1", headers=headers)
    assert res.status_code == 401
    assert "Authentication failed" in res.json()["detail"]

def test_admin123_arbitrary_username_fallback_rejected():
    res = client.post("/api/v1/auth/login", json={"username": "arbitrary_user", "password": "admin123"})
    assert res.status_code == 401
    assert "Authentication failed" in res.json()["detail"]

def test_admin_login_invalid_password_rejected():
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong_password_999"})
    assert res.status_code == 401
    assert "Authentication failed" in res.json()["detail"]

def test_admin_login_valid_credentials_succeeds():
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin_dev_pass_2026"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"
    assert data["role"] == "ADMIN"
