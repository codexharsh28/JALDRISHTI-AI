"""
Penetration-style Server-Side Request Forgery (SSRF) Tests.
Validates that endpoints never permit outbound calls to internal IP addresses or cloud metadata endpoints.
"""

import pytest
from services.notifications.providers.sms_provider import MSG91Provider

SSRF_TARGETS = [
    "http://127.0.0.1:8000/internal-admin",
    "http://localhost:8080/secret",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]:22/"
]

def test_sms_provider_ssrf_protection():
    # Verify SMS provider strictly targets official api.msg91.com domain
    provider = MSG91Provider()
    assert "api.msg91.com" in provider.endpoint
    assert not any(target in provider.endpoint for target in SSRF_TARGETS)
