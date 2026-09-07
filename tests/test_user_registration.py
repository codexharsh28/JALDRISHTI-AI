"""
Unit tests for Public User Registration & Location Subscriptions.
"""

import pytest
from services.notifications.user_store import UserStore

def test_user_registration_and_phone_hashing():
    store = UserStore()
    user = store.register_user(phone_number="+919876543210", preferred_language="hi")

    assert user.user_id.startswith("USR-")
    assert user.phone_number == "9876543210"
    assert len(user.phone_hash) == 64 # SHA-256
    assert user.phone_verified is False
    assert user.preferred_language == "hi"

def test_multi_location_subscriptions():
    store = UserStore()
    phone = "9876500001"
    user = store.register_user(phone_number=phone)
    # Clear any old subscriptions from previous runs if any
    for sub in list(user.subscriptions):
        store.delete_subscription(user.user_id, sub.subscription_id)

    sub_home = store.add_subscription(
        user_id=user.user_id,
        label="HOME",
        locality_name="Cuttack Cantonment",
        latitude=20.46,
        longitude=85.88,
        radius_km=10.0
    )
    sub_work = store.add_subscription(
        user_id=user.user_id,
        label="WORK",
        locality_name="Bhubaneswar Rasulgarh",
        latitude=20.29,
        longitude=85.84,
        radius_km=5.0
    )

    assert len(user.subscriptions) == 2
    assert sub_home.label == "HOME"
    assert sub_work.label == "WORK"

    # Delete subscription
    assert store.delete_subscription(user.user_id, sub_work.subscription_id) is True
    assert len(user.subscriptions) == 1
