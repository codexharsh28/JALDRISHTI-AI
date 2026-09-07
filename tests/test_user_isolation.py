"""
Broken Object Level Authorization (IDOR / BOLA) Isolation Tests for JALDRISHTI AI.
Proves that Citizen A cannot view, add, or delete Citizen B's subscriptions or notifications.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.user_store import user_store
from services.notifications.security import token_manager

client = TestClient(app)

def test_cross_user_subscription_access_blocked():
    # Citizen A
    user_a = user_store.register_user(phone_number="9990001111")
    token_a, _ = token_manager.create_access_token(user_id=user_a.user_id)
    
    # Citizen B
    user_b = user_store.register_user(phone_number="9990002222")
    token_b, _ = token_manager.create_access_token(user_id=user_b.user_id)

    # Citizen A attempts to read Citizen B's subscriptions with Citizen A's token
    headers_a = {"Authorization": f"Bearer {token_a}"}
    res = client.get(f"/api/v1/user/subscriptions?user_id={user_b.user_id}", headers=headers_a)
    assert res.status_code == 403
    assert "IDOR violation" in res.json()["detail"]

def test_cross_user_subscription_mutation_blocked():
    # Citizen A
    user_a = user_store.register_user(phone_number="9990003333")
    token_a, _ = token_manager.create_access_token(user_id=user_a.user_id)
    
    # Citizen B
    user_b = user_store.register_user(phone_number="9990004444")
    
    # Citizen A attempts to add a subscription on behalf of Citizen B
    headers_a = {"Authorization": f"Bearer {token_a}"}
    res = client.post(
        "/api/v1/user/subscriptions",
        headers=headers_a,
        json={
            "user_id": user_b.user_id,
            "label": "HOME",
            "locality_name": "Unauthorized Location",
            "latitude": 20.46,
            "longitude": 85.88
        }
    )
    assert res.status_code == 403
    assert "IDOR violation" in res.json()["detail"]

def test_cross_user_notifications_inbox_access_blocked():
    # Citizen A
    user_a = user_store.register_user(phone_number="9990005555")
    token_a, _ = token_manager.create_access_token(user_id=user_a.user_id)
    
    # Citizen B
    user_b = user_store.register_user(phone_number="9990006666")

    # Citizen A attempts to read Citizen B's inbox
    headers_a = {"Authorization": f"Bearer {token_a}"}
    res = client.get(f"/api/v1/user/notifications?user_id={user_b.user_id}", headers=headers_a)
    assert res.status_code == 403
