"""
Automated Secret Leakage & Plaintext Credential Absence Tests.
Scans endpoint responses and public schemas to ensure API keys, DLT secrets, and plaintext OTPs are never exposed.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
import json

client = TestClient(app)

def test_no_hardcoded_secrets_in_health_and_providers():
    res_h = client.get("/api/v1/notifications/health")
    assert res_h.status_code == 200
    text_h = json.dumps(res_h.json())
    assert "MSG91_AUTH_KEY" not in text_h
    assert "FIREBASE_CREDENTIALS" not in text_h

    res_p = client.get("/api/v1/notifications/providers")
    assert res_p.status_code == 200
    data_p = res_p.json()
    assert "auth_key" not in data_p
    assert "private_key" not in data_p

def test_no_plaintext_otp_in_send_otp_payload():
    res = client.post("/api/v1/user/send-otp", json={"phone_number": "9812345678"})
    assert res.status_code == 200
    data = res.json()
    assert "dev_otp_preview" not in data
    assert "otp" not in data
    assert "code" not in data
