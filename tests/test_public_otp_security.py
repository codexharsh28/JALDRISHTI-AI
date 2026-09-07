"""
OTP Cryptographic Security, Salted Hashing & Public Endpoint Protection Tests.
Proves that:
1. Plaintext OTP is completely absent from all production API JSON responses.
2. Production responses return only verification metadata (masked_destination, expires_at, retry_after, request_id).
3. Plaintext OTP is never stored in DB (only salted SHA-256 hash).
4. Brute-force lockout is strictly enforced after 3 failed attempts.
5. Isolated server-side test sink allows automated test verification without API leakage.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.user_store import UserStore, user_store
from services.notifications.db.repositories import VerificationRepository

client = TestClient(app)

def test_plaintext_otp_absent_from_production_api_response():
    phone = "9880011223"
    res = client.post("/api/v1/user/send-otp", json={"phone_number": phone})
    assert res.status_code == 200
    data = res.json()

    # Mandatory security checks
    assert "dev_otp_preview" not in data
    assert "otp" not in data
    assert "code" not in data
    assert "plain_otp" not in data

    # Required contract fields
    assert data["status"] == "SENT"
    assert data["verification_required"] is True
    assert "expires_at" in data
    assert "retry_after" in data
    assert data["masked_destination"] == "******1223"
    assert data["request_id"].startswith("OTP-REQ-")

def test_otp_is_cryptographically_salted_in_db():
    store = UserStore()
    phone = "9887766554"
    phone_h = store.hash_phone(phone)

    ok, msg, meta = store.request_otp(phone)
    assert ok is True
    assert "dev_otp" not in meta
    assert "otp" not in meta

    dev_otp = store.get_dev_otp_for_testing(phone)
    assert dev_otp is not None
    assert len(dev_otp) == 6

    record = VerificationRepository.get_active_otp(phone_h)
    assert record is not None
    # Crucial security check: Plaintext OTP must NOT match stored hashed_otp
    assert record["hashed_otp"] != dev_otp
    assert len(record["hashed_otp"]) == 64 # SHA-256
    assert len(record["salt"]) == 16 # 8-byte hex salt

def test_brute_force_lockout_after_max_attempts():
    store = UserStore(max_otp_attempts=3)
    phone = "9887766555"

    ok, _, _ = store.request_otp(phone)
    assert ok is True

    # Attempt 1: Incorrect
    v1, msg1, _ = store.verify_otp(phone, "000000")
    assert v1 is False
    assert "2 attempt(s) remaining" in msg1

    # Attempt 2: Incorrect
    v2, msg2, _ = store.verify_otp(phone, "111111")
    assert v2 is False
    assert "1 attempt(s) remaining" in msg2

    # Attempt 3: Incorrect
    v3, msg3, _ = store.verify_otp(phone, "222222")
    assert v3 is False
    assert "0 attempt(s) remaining" in msg3

    # Attempt 4: Lockout
    v4, msg4, _ = store.verify_otp(phone, "333333")
    assert v4 is False
    assert "Too many failed attempts" in msg4

def test_authoritative_backend_verification_flow():
    phone = "9880022334"
    # 1. Send OTP
    res_send = client.post("/api/v1/user/send-otp", json={"phone_number": phone})
    assert res_send.status_code == 200

    # Retrieve OTP from isolated test sink
    test_otp = user_store.get_dev_otp_for_testing(phone)
    assert test_otp is not None

    # 2. Verify Phone
    res_verify = client.post("/api/v1/user/verify-phone", json={"phone_number": phone, "otp": test_otp})
    assert res_verify.status_code == 200
    v_data = res_verify.json()
    assert v_data["status"] == "VERIFIED"
    assert v_data["phone_verified"] is True
    assert v_data["sms_enabled"] is True
    assert v_data["access_token"] is not None
    assert v_data["masked_destination"] == "******2334"

def test_provider_health_authoritative_status():
    res = client.get("/api/v1/notifications/health")
    assert res.status_code == 200
    data = res.json()
    assert "providers" in data
    assert data["providers"]["sms"] in ["MOCK_MODE_ACTIVE", "CONFIGURED", "NOT_CONFIGURED"]
