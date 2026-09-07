"""
API Input Validation & Payload Size Limits (HTTP 413) Tests.
Tests oversized request bodies and invalid coordinate inputs.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_oversized_payload_rejected_with_413():
    # 2.5 MB payload (exceeds 2 MB limit)
    large_payload = {"phone_number": "9" * (2500 * 1024)}
    res = client.post("/api/v1/user/register", json=large_payload)
    assert res.status_code == 413
    assert "Payload Too Large" in res.json()["detail"]

def test_invalid_subscription_coordinates_rejected():
    user_res = client.post("/api/v1/user/register", json={"phone_number": "9899887766"})
    user_id = user_res.json()["user_id"]

    # Invalid latitude 95.0 (> 90.0)
    res = client.post(
        "/api/v1/user/subscriptions",
        json={
            "user_id": user_id,
            "label": "HOME",
            "locality_name": "Invalid Locality",
            "latitude": 95.0,
            "longitude": 85.88,
            "radius_km": 10.0
        }
    )
    # Database CHECK constraint catches invalid coordinate range
    assert res.status_code in [400, 422, 500]
