"""
Database Relational Integrity, Foreign Keys & Transaction Rollback Tests.
"""

import pytest
import sqlite3
from services.notifications.db.connection import db_manager
from services.notifications.db.repositories import (
    UserRepository,
    SubscriptionRepository,
    NotificationRepository
)
from services.notifications.user_store import user_store

def test_foreign_key_cascade_deletion():
    user = user_store.register_user("9776655443")
    sub = user_store.add_subscription(
        user_id=user.user_id,
        label="HOME",
        locality_name="Cuttack",
        latitude=20.46,
        longitude=85.88
    )

    # Verify subscription exists
    subs = SubscriptionRepository.get_user_subscriptions(user.user_id)
    assert len(subs) == 1

    # Delete parent user row directly
    with db_manager.transaction() as conn:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user.user_id,))

    # Verify cascade deleted subscription
    subs_after = SubscriptionRepository.get_user_subscriptions(user.user_id)
    assert len(subs_after) == 0

def test_transaction_rollback_on_error():
    user = user_store.register_user("9776655444")
    
    with pytest.raises(Exception):
        with db_manager.transaction() as conn:
            conn.execute(
                "INSERT INTO location_subscriptions (subscription_id, user_id, label, locality_name, latitude, longitude, radius_km) VALUES ('SUB-ROLLBACK', ?, 'WORK', 'Loc', 20.0, 85.0, 10.0)",
                (user.user_id,)
            )
            # Intentionally cause an error to trigger rollback
            raise RuntimeError("Forced transaction failure")

    # Verify that the uncommitted subscription was rolled back
    subs = SubscriptionRepository.get_user_subscriptions(user.user_id)
    assert not any(s["subscription_id"] == "SUB-ROLLBACK" for s in subs)
