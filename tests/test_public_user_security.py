"""
Security & Token Authentication Tests for JALDRISHTI AI Public Users.
Validates HMAC-SHA256 token verification, role enforcement, and masked phone protection.
"""

import pytest
from datetime import timedelta
from services.notifications.security import (
    token_manager,
    mask_phone_number,
    rate_limiter
)
from services.notifications.user_store import user_store

def test_token_creation_and_validation():
    user_id = "USR-TEST-001"
    token, exp = token_manager.create_access_token(user_id=user_id, role="PUBLIC_USER")
    
    is_valid, payload, err = token_manager.verify_access_token(token)
    assert is_valid is True
    assert payload["sub"] == user_id
    assert payload["role"] == "PUBLIC_USER"
    assert err is None

def test_tampered_token_rejected():
    user_id = "USR-TEST-002"
    token, _ = token_manager.create_access_token(user_id=user_id)
    
    # Tamper with signature
    parts = token.split(".")
    tampered = f"{parts[0]}.deadbeef12345678"
    is_valid, payload, err = token_manager.verify_access_token(tampered)
    assert is_valid is False
    assert "signature" in err.lower()

def test_expired_token_rejected():
    user_id = "USR-TEST-003"
    # Create token expired 1 hour ago
    token, _ = token_manager.create_access_token(user_id=user_id, expires_delta=timedelta(hours=-1))
    
    is_valid, payload, err = token_manager.verify_access_token(token)
    assert is_valid is False
    assert "expired" in err.lower()

def test_phone_masking_privacy():
    assert mask_phone_number("9876543210") == "******3210"
    assert mask_phone_number("+919123456789") == "******6789"
    assert mask_phone_number("123") == "******"
