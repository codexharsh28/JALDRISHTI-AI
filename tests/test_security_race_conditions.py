"""
Concurrency, Race Conditions & Database Transaction Atomicity Tests.
"""

import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from services.notifications.user_store import user_store
from services.notifications.db.repositories import VerificationRepository

def test_concurrent_otp_verification_single_use():
    phone = "9890001122"
    ok, msg, meta = user_store.request_otp(phone)
    assert ok is True
    otp = user_store.get_dev_otp_for_testing(phone)
    assert otp is not None

    def attempt_verification():
        return user_store.verify_otp(phone, otp)

    # 5 concurrent verification attempts using the same single-use OTP
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(attempt_verification) for _ in range(5)]
        results = [f.result() for f in futures]

    # Exactly 1 attempt must succeed; remaining 4 must fail because OTP is deleted immediately
    successes = sum(1 for ok, msg, token in results if ok is True)
    assert successes == 1
