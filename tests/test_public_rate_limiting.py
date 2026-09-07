"""
Rate Limiting & Abuse Prevention Tests for JALDRISHTI AI Public Endpoints.
Validates multi-dimensional sliding windows and Retry-After emission.
"""

import pytest
from services.notifications.security import MultiDimensionRateLimiter

def test_sliding_window_rate_limiting():
    limiter = MultiDimensionRateLimiter()
    ip = "192.168.1.100"

    # Allow 5 requests in 60 seconds
    for i in range(5):
        allowed, rem, retry_after = limiter.check_rate_limit(
            dimension_type="ip",
            identifier=ip,
            max_requests=5,
            window_seconds=60,
            lockout_seconds_on_breach=30
        )
        assert allowed is True
        assert rem == 4 - i

    # 6th request should be blocked
    allowed, rem, retry_after = limiter.check_rate_limit(
        dimension_type="ip",
        identifier=ip,
        max_requests=5,
        window_seconds=60,
        lockout_seconds_on_breach=30
    )
    assert allowed is False
    assert rem == 0
    assert retry_after > 0

def test_different_dimensions_isolated():
    limiter = MultiDimensionRateLimiter()
    phone1 = "hash_phone_111"
    phone2 = "hash_phone_222"

    # Exhaust phone1
    for _ in range(3):
        limiter.check_rate_limit("phone", phone1, max_requests=3, window_seconds=60)

    # phone1 is blocked
    allowed1, _, _ = limiter.check_rate_limit("phone", phone1, max_requests=3, window_seconds=60)
    assert allowed1 is False

    # phone2 remains unaffected
    allowed2, _, _ = limiter.check_rate_limit("phone", phone2, max_requests=3, window_seconds=60)
    assert allowed2 is True
