"""
Penetration-style Broken Object Level Authorization (IDOR / BOLA) Tests.
Validates that an attacker cannot read, alter, or delete other citizens' resources.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.notifications.user_store import user_store
from services.notifications.security import token_manager

client = TestClient(app)

def test_idor_cross_user_subscriptions_read_blocked():
    user1 = user_store.register_user("9800000001")
    token1, _ = token_manager.create_access_token(user1.user_id, role="PUBLIC_USER")
    
    user2 = user_store.register_user("9800000002")
    user_store.add_subscription(user2.user_id, "HOME", "Cuttack", 20.46, 85.88)

    headers = {"Authorization": f"Bearer {token1}"}
    res = client.get(f"/api/v1/user/subscriptions?user_id={user2.user_id}", headers=headers)
    assert res.status_code == 403
    assert "IDOR violation" in res.json()["detail"]

def test_idor_cross_user_subscription_delete_blocked():
    user1 = user_store.register_user("9800000003")
    token1, _ = token_manager.create_access_token(user1.user_id, role="PUBLIC_USER")
    
    user2 = user_store.register_user("9800000004")
    sub2 = user_store.add_subscription(user2.user_id, "HOME", "Bhubaneswar", 20.29, 85.84)

    headers = {"Authorization": f"Bearer {token1}"}
    res = client.delete(f"/api/v1/user/subscriptions/{sub2.subscription_id}?user_id={user2.user_id}", headers=headers)
    assert res.status_code == 403
    assert "IDOR violation" in res.json()["detail"]

def test_idor_cross_user_inbox_read_blocked():
    user1 = user_store.register_user("9800000005")
    token1, _ = token_manager.create_access_token(user1.user_id, role="PUBLIC_USER")
    
    user2 = user_store.register_user("9800000006")

    headers = {"Authorization": f"Bearer {token1}"}
    res = client.get(f"/api/v1/user/notifications?user_id={user2.user_id}", headers=headers)
    assert res.status_code == 403
