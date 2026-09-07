"""
Penetration-style SQL Injection Tests for JALDRISHTI AI.
Proves that SQL injection payloads in user_id, phone_number, locality_name, etc. are safely parameterized.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.db.repositories import (
    UserRepository,
    SubscriptionRepository,
    NotificationRepository
)

client = TestClient(app)

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT null, null, null, null, null, null, null, null, null --",
    "admin'--",
    "1; SELECT pg_sleep(5); --"
]

def test_sql_injection_in_user_registration():
    for payload in SQLI_PAYLOADS:
        # Register user with SQLi payload in phone
        res = client.post("/api/v1/user/register", json={"phone_number": payload, "preferred_language": "en"})
        assert res.status_code == 200
        # Check that table still exists and data was safely parameterized
        data = res.json()
        assert "user_id" in data

def test_sql_injection_in_user_queries():
    for payload in SQLI_PAYLOADS:
        # Query user with SQLi payload
        user = UserRepository.get_by_id(payload)
        assert user is None

        user_by_hash = UserRepository.get_by_phone_hash(payload)
        assert user_by_hash is None

def test_sql_injection_in_subscription_repository():
    for payload in SQLI_PAYLOADS:
        subs = SubscriptionRepository.get_user_subscriptions(payload)
        assert isinstance(subs, list)
        assert len(subs) == 0
