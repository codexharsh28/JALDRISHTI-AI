"""
Transactional Database Repositories for JALDRISHTI AI Public Notifications.
Implements normalized relational persistence for users, subscriptions, notifications, and audits.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json
import uuid

from services.notifications.db.connection import db_manager
from services.notifications.notification_types import (
    User,
    LocationSubscription,
    UserPreferences,
    NotificationMessage,
    NotificationDeliveryStatus,
    NotificationChannel,
    NotificationSeverityPolicy,
    NotificationProvenance,
    DeliveryRecord
)

class UserRepository:
    """
    CRUD repository for users and phone hashes.
    """

    @staticmethod
    def create_or_get_user(
        phone_hash: str,
        phone_masked: str,
        preferred_language: str = "en",
        role: str = "PUBLIC_USER"
    ) -> Tuple[Dict[str, Any], bool]:
        """Returns (user_row, created_boolean)."""
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE phone_hash = ?", (phone_hash,))
            row = cursor.fetchone()
            if row:
                return dict(row), False

            user_id = f"USR-{uuid.uuid4().hex[:8]}"
            conn.execute(
                """
                INSERT INTO users (user_id, phone_hash, phone_masked, phone_verified, preferred_language, role, status, created_at, updated_at)
                VALUES (?, ?, ?, 0, ?, ?, 'ACTIVE', ?, ?)
                """,
                (user_id, phone_hash, phone_masked, preferred_language, role, now, now)
            )
            # Create default preferences
            pref_id = f"PREF-{uuid.uuid4().hex[:6]}"
            conn.execute(
                """
                INSERT INTO notification_preferences (preference_id, user_id, sms_enabled, push_enabled, in_app_enabled, email_enabled, minimum_severity, preferred_language, quiet_mode, created_at, updated_at)
                VALUES (?, ?, 1, 1, 1, 0, 'WATCH', ?, 0, ?, ?)
                """,
                (pref_id, user_id, preferred_language, now, now)
            )

            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone()), True

    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_phone_hash(phone_hash: str) -> Optional[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE phone_hash = ?", (phone_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def set_phone_verified(user_id: str, verified: bool = True) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.transaction() as conn:
            conn.execute(
                "UPDATE users SET phone_verified = ?, updated_at = ? WHERE user_id = ?",
                (1 if verified else 0, now, user_id)
            )

    @staticmethod
    def get_all_users() -> List[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE status = 'ACTIVE'")
            return [dict(r) for r in cursor.fetchall()]

class VerificationRepository:
    """
    CRUD repository for salted OTP verification records.
    """

    @staticmethod
    def store_otp(
        phone_hash: str,
        salt: str,
        hashed_otp: str,
        expires_at: datetime
    ) -> str:
        ver_id = f"VER-{uuid.uuid4().hex[:8]}"
        with db_manager.transaction() as conn:
            # Invalidate any prior active OTPs for this phone hash
            conn.execute("DELETE FROM user_verifications WHERE phone_hash = ?", (phone_hash,))
            conn.execute(
                """
                INSERT INTO user_verifications (verification_id, phone_hash, salt, hashed_otp, attempts, max_attempts, expires_at)
                VALUES (?, ?, ?, ?, 0, 3, ?)
                """,
                (ver_id, phone_hash, salt, hashed_otp, expires_at.isoformat())
            )
        return ver_id

    @staticmethod
    def get_active_otp(phone_hash: str) -> Optional[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_verifications WHERE phone_hash = ? ORDER BY created_at DESC LIMIT 1",
                (phone_hash,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def increment_attempt(verification_id: str) -> int:
        with db_manager.transaction() as conn:
            conn.execute(
                "UPDATE user_verifications SET attempts = attempts + 1 WHERE verification_id = ?",
                (verification_id,)
            )
            cursor = conn.execute("SELECT attempts FROM user_verifications WHERE verification_id = ?", (verification_id,))
            row = cursor.fetchone()
            return row["attempts"] if row else 3

    @staticmethod
    def delete_otp(phone_hash: str) -> None:
        with db_manager.transaction() as conn:
            conn.execute("DELETE FROM user_verifications WHERE phone_hash = ?", (phone_hash,))

class SubscriptionRepository:
    """
    CRUD repository for location subscriptions.
    """

    @staticmethod
    def create_subscription(
        user_id: str,
        label: str,
        locality_name: str,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        geohash: Optional[str] = None
    ) -> Dict[str, Any]:
        sub_id = f"SUB-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT INTO location_subscriptions (subscription_id, user_id, label, locality_name, latitude, longitude, geohash, radius_km, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sub_id, user_id, label, locality_name, latitude, longitude, geohash, radius_km, now, now)
            )
            cursor = conn.execute("SELECT * FROM location_subscriptions WHERE subscription_id = ?", (sub_id,))
            return dict(cursor.fetchone())

    @staticmethod
    def get_user_subscriptions(user_id: str) -> List[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT * FROM location_subscriptions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def delete_subscription(user_id: str, subscription_id: str) -> bool:
        with db_manager.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM location_subscriptions WHERE subscription_id = ? AND user_id = ?",
                (subscription_id, user_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_all_subscriptions() -> List[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT * FROM location_subscriptions")
            return [dict(r) for r in cursor.fetchall()]

class NotificationRepository:
    """
    Repository for storing and querying notifications and delivery history.
    """

    @staticmethod
    def record_notification(msg: NotificationMessage) -> None:
        with db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO notifications (
                    notification_id, user_id, subscription_id, alert_id, forecast_run_id,
                    risk_state_id, channel, severity, title, body, recipient_masked,
                    locality, template_id, data_state, region_id, fingerprint, deeplink_url,
                    status, retry_count, max_retries, provider_name, provider_message_id,
                    delivery_latency_ms, error_message, issued_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg.notification_id, msg.user_id, msg.subscription_id, msg.provenance.alert_id,
                    msg.provenance.forecast_run_id, msg.provenance.risk_state_id, msg.channel.value,
                    msg.severity.value, msg.title, msg.body,
                    f"******{msg.recipient[-4:]}" if len(msg.recipient) >= 10 else msg.recipient[:10],
                    msg.locality, msg.provenance.template_id, msg.provenance.data_state,
                    getattr(msg.provenance, "region_id", "MAHANADI_DELTA"),
                    getattr(msg, "fingerprint", "FP-DEFAULT"), msg.deeplink_url,
                    msg.status.value, msg.retry_count, msg.max_retries, msg.provider_name,
                    msg.provider_message_id, msg.delivery_latency_ms, msg.error_message, msg.issued_at
                )
            )

    @staticmethod
    def record_delivery_attempt(record: DeliveryRecord) -> None:
        with db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT INTO notification_deliveries (
                    delivery_id, notification_id, user_id, channel, provider, status,
                    response_code, latency_ms, error_details, attempt_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id, record.notification_id, record.user_id, record.channel.value,
                    record.provider, record.status.value, record.response_code, record.latency_ms,
                    record.error_details, record.attempt_timestamp
                )
            )

    @staticmethod
    def get_user_notifications(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM notifications WHERE user_id = ? ORDER BY issued_at DESC LIMIT ?",
                (user_id, limit)
            )
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_notification_by_id(notification_id: str) -> Optional[Dict[str, Any]]:
        with db_manager.transaction() as conn:
            cursor = conn.execute("SELECT * FROM notifications WHERE notification_id = ?", (notification_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

class AuditRepository:
    """
    Append-only security and operational audit log repository.
    """

    @staticmethod
    def log_event(
        event_type: str,
        action: str,
        status: str,
        actor_id: str = "SYSTEM",
        actor_role: str = "SYSTEM",
        ip_address: Optional[str] = None,
        target_resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        audit_id = f"AUD-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (audit_id, event_type, actor_id, actor_role, ip_address, target_resource, action, status, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id, event_type, actor_id, actor_role, ip_address, target_resource,
                    action, status, json.dumps(details or {}) if details else None, now
                )
            )
        return audit_id

    @staticmethod
    def get_audit_logs(
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        if action:
            query += " AND action = ?"
            params.append(action)
        if status:
            query += " AND status = ?"
            params.append(status)

        count_query = f"SELECT COUNT(*) as count FROM ({query})"
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        
        with db_manager.transaction() as conn:
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["count"]

            params.extend([limit, offset])
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                item = dict(r)
                if item.get("details"):
                    try:
                        item["details"] = json.loads(item["details"])
                    except Exception:
                        pass
                logs.append(item)
            return logs, total
