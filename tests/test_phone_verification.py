"""
Unit tests for Salted OTP Phone Verification, Expiration & Rate Limiting.
"""

import pytest
from services.notifications.user_store import UserStore

def test_otp_request_and_verification_flow():
    store = UserStore()
    phone = "9123456780"

    ok, msg, meta = store.request_otp(phone)
    assert ok is True
    assert meta["verification_required"] is True
    assert meta["masked_destination"] == "******6780"

    dev_otp = store.get_dev_otp_for_testing(phone)
    assert dev_otp is not None
    assert len(dev_otp) == 6

    # Verify with correct OTP
    v_ok, v_msg, token = store.verify_otp(phone, dev_otp)
    assert v_ok is True
    assert token is not None
    user = store.get_user_by_phone(phone)
    assert user is not None
    assert user.phone_verified is True

def test_invalid_otp_and_max_attempts():
    store = UserStore(max_otp_attempts=2)
    phone = "9123456781"

    store.request_otp(phone)

    # Attempt 1: wrong
    ok1, msg1, _ = store.verify_otp(phone, "000000")
    assert ok1 is False
    assert "1 attempt(s) remaining" in msg1

    # Attempt 2: wrong
    ok2, msg2, _ = store.verify_otp(phone, "111111")
    assert ok2 is False

    # Attempt 3: exceeded
    ok3, msg3, _ = store.verify_otp(phone, "222222")
    assert ok3 is False
    assert "Too many failed attempts" in msg3
