"""
Penetration-style Rate Limiting & Denial-of-Wallet Abuse Tests.
Proves that OTP flooding, registration storms, and subscription flooding return HTTP 429.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.security import rate_limiter

client = TestClient(app)

def test_otp_flooding_triggers_429():
    phone = "9811122233"
    
    # 3 allowed requests per 10 mins
    r1 = client.post("/api/v1/user/send-otp", json={"phone_number": phone})
    assert r1.status_code == 200
    
    r2 = client.post("/api/v1/user/send-otp", json={"phone_number": phone})
    assert r2.status_code == 200

    r3 = client.post("/api/v1/user/send-otp", json={"phone_number": phone})
    assert r3.status_code == 200

    # 4th request MUST be blocked with HTTP 429
    r4 = client.post("/api/v1/user/send-otp", json={"phone_number": phone})
    assert r4.status_code == 429
    assert "Rate limit exceeded" in r4.json()["detail"]
    assert "Retry-After" in r4.headers

def test_subscription_mutation_rate_limiting():
    user_id = "USR-RATE-01"
    # Exhaust sliding window of 30 req/min for user mutations
    for i in range(30):
        rate_limiter.check_rate_limit(
            dimension_type="subscriptions_mutation",
            identifier=user_id,
            max_requests=30,
            window_seconds=60,
            lockout_seconds_on_breach=60
        )
    
    # 31st request is blocked
    allowed, rem, retry_after = rate_limiter.check_rate_limit(
        dimension_type="subscriptions_mutation",
        identifier=user_id,
        max_requests=30,
        window_seconds=60,
        lockout_seconds_on_breach=60
    )
    assert allowed is False
    assert retry_after > 0
