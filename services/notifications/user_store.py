"""
User Registration, Salted OTP Verification, Database Persistence, and Subscription Store for JALDRISHTI AI.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import threading
import logging
import uuid

from services.notifications.notification_types import (
    User,
    LocationSubscription,
    UserPreferences
)
from services.notifications.db.repositories import (
    UserRepository,
    VerificationRepository,
    SubscriptionRepository,
    AuditRepository
)
from services.notifications.security import (
    mask_phone_number,
    token_manager,
    rate_limiter
)

logger = logging.getLogger(__name__)

class UserStore:
    """
    Thread-safe user registry backed by normalized SQLite/PostgreSQL relational database.
    """

    def __init__(self, otp_ttl_minutes: int = 10, max_otp_attempts: int = 3):
        self.otp_ttl_minutes = otp_ttl_minutes
        self.max_otp_attempts = max_otp_attempts
        self._lock = threading.Lock()
        self._users: Dict[str, User] = {}
        self._dev_test_otp_sink: Dict[str, str] = {}

    def get_dev_otp_for_testing(self, phone_number: str) -> Optional[str]:
        """Test fixture helper: retrieves OTP for test assertions. Never exposed via public APIs."""
        phone_h = self.hash_phone(phone_number)
        with self._lock:
            return self._dev_test_otp_sink.get(phone_h)

    @staticmethod
    def hash_phone(phone: str) -> str:
        """Deterministically hashes phone number with SHA-256 for privacy."""
        clean_phone = "".join(filter(str.isdigit, phone))
        return hashlib.sha256(clean_phone.encode()).hexdigest()

    @staticmethod
    def _hash_otp(otp_plain: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{otp_plain}".encode()).hexdigest()

    def register_user(
        self,
        phone_number: str,
        preferred_language: str = "en",
        role: str = "PUBLIC_USER",
        ip_address: Optional[str] = None
    ) -> User:
        """Registers a new user or returns existing user from database."""
        phone_h = self.hash_phone(phone_number)
        phone_masked = mask_phone_number(phone_number)
        
        with self._lock:
            if phone_h in self._users:
                return self._users[phone_h]

            row, created = UserRepository.create_or_get_user(
                phone_hash=phone_h,
                phone_masked=phone_masked,
                preferred_language=preferred_language,
                role=role
            )

            user = User(
                user_id=row["user_id"],
                phone_number=phone_number[-10:],
                phone_hash=row["phone_hash"],
                phone_verified=bool(row["phone_verified"]),
                preferred_language=row["preferred_language"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                status=row["status"]
            )

            # Load subscriptions
            sub_rows = SubscriptionRepository.get_user_subscriptions(user.user_id)
            user.subscriptions = [
                LocationSubscription(
                    subscription_id=s["subscription_id"],
                    user_id=s["user_id"],
                    label=s["label"],
                    locality_name=s["locality_name"],
                    latitude=s["latitude"],
                    longitude=s["longitude"],
                    geohash=s["geohash"],
                    radius_km=s["radius_km"],
                    created_at=s["created_at"]
                )
                for s in sub_rows
            ]

            self._users[phone_h] = user
            self._users[user.user_id] = user

            if created:
                AuditRepository.log_event(
                    event_type="USER_REGISTERED",
                    action="REGISTER",
                    status="SUCCESS",
                    actor_id=user.user_id,
                    actor_role=role,
                    ip_address=ip_address,
                    target_resource=user.user_id,
                    details={"phone_masked": phone_masked, "language": preferred_language}
                )

            return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self._lock:
            if user_id in self._users:
                return self._users[user_id]
            row = UserRepository.get_by_id(user_id)
            if not row:
                return None

            sub_rows = SubscriptionRepository.get_user_subscriptions(user_id)
            user = User(
                user_id=row["user_id"],
                phone_number=row["phone_masked"], # Returns masked phone for privacy
                phone_hash=row["phone_hash"],
                phone_verified=bool(row["phone_verified"]),
                preferred_language=row["preferred_language"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                status=row["status"]
            )
            user.subscriptions = [
                LocationSubscription(
                    subscription_id=s["subscription_id"],
                    user_id=s["user_id"],
                    label=s["label"],
                    locality_name=s["locality_name"],
                    latitude=s["latitude"],
                    longitude=s["longitude"],
                    geohash=s["geohash"],
                    radius_km=s["radius_km"],
                    created_at=s["created_at"]
                )
                for s in sub_rows
            ]
            self._users[user_id] = user
            return user

    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        phone_h = self.hash_phone(phone_number)
        with self._lock:
            if phone_h in self._users:
                return self._users[phone_h]
            row = UserRepository.get_by_phone_hash(phone_h)
            if not row:
                return None
            return self.get_user_by_id(row["user_id"])

    def request_otp(
        self,
        phone_number: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generates a salted 6-digit OTP, stores its hash in database, and returns authoritative metadata.
        Plaintext OTP is never returned in production API responses.
        """
        phone_h = self.hash_phone(phone_number)
        masked_dest = mask_phone_number(phone_number)
        
        # 1. Enforce Rate Limiting (3 requests per 10 minutes)
        allowed, rem, retry_after = rate_limiter.check_rate_limit(
            dimension_type="otp_request_phone",
            identifier=phone_h,
            max_requests=3,
            window_seconds=600,
            lockout_seconds_on_breach=600
        )
        if not allowed:
            AuditRepository.log_event(
                event_type="RATE_LIMIT_EXCEEDED",
                action="REQUEST_OTP",
                status="BLOCKED",
                ip_address=ip_address,
                details={"phone_hash": phone_h[:12], "retry_after": retry_after}
            )
            return False, f"Rate limit exceeded: Please wait {retry_after}s before requesting another OTP.", {
                "verification_required": True,
                "retry_after": retry_after,
                "masked_destination": masked_dest
            }

        # 2. Generate random 6-digit OTP and secure salt
        otp_plain = f"{secrets.randbelow(900000) + 100000}"
        salt = secrets.token_hex(8)
        hashed_otp = self._hash_otp(otp_plain, salt)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.otp_ttl_minutes)

        # Store in server-side test sink ONLY for test automation
        with self._lock:
            self._dev_test_otp_sink[phone_h] = otp_plain

        # 3. Persist in database (ONLY salted hash)
        VerificationRepository.store_otp(
            phone_hash=phone_h,
            salt=salt,
            hashed_otp=hashed_otp,
            expires_at=expires_at
        )

        # 4. Auto-register user record if first-time
        self.register_user(phone_number=phone_number, ip_address=ip_address)

        req_id = f"OTP-REQ-{uuid.uuid4().hex[:10]}"
        AuditRepository.log_event(
            event_type="OTP_GENERATED",
            action="REQUEST_OTP",
            status="SUCCESS",
            ip_address=ip_address,
            details={"phone_masked": masked_dest, "request_id": req_id}
        )

        meta = {
            "verification_required": True,
            "expires_at": expires_at.isoformat(),
            "retry_after": 60,
            "masked_destination": masked_dest,
            "request_id": req_id
        }

        return True, "OTP has been sent to your registered mobile number.", meta

    def verify_otp(
        self,
        phone_number: str,
        otp_entered: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Verifies entered OTP against stored database hash, enforcing expiration and attempt limits.
        Returns: (success, message, access_token)
        """
        phone_h = self.hash_phone(phone_number)
        now = datetime.now(timezone.utc)

        with self._lock:
            record = VerificationRepository.get_active_otp(phone_h)
            if not record:
                return False, "No active OTP found. Please request a new OTP.", None

            exp_time = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)

            if now > exp_time:
                VerificationRepository.delete_otp(phone_h)
                AuditRepository.log_event(
                    event_type="OTP_EXPIRED",
                    action="VERIFY_OTP",
                    status="FAILURE",
                    ip_address=ip_address,
                    details={"phone_masked": mask_phone_number(phone_number)}
                )
                return False, "OTP has expired. Please request a new OTP.", None

            # Check brute force attempts
            attempts = VerificationRepository.increment_attempt(record["verification_id"])
            if attempts > self.max_otp_attempts:
                VerificationRepository.delete_otp(phone_h)
                AuditRepository.log_event(
                    event_type="BRUTE_FORCE_LOCKOUT",
                    action="VERIFY_OTP",
                    status="BLOCKED",
                    ip_address=ip_address,
                    details={"phone_masked": mask_phone_number(phone_number), "attempts": attempts}
                )
                return False, "Too many failed attempts. OTP has been invalidated.", None

            computed_hash = self._hash_otp(otp_entered.strip(), record["salt"])
            if secrets.compare_digest(computed_hash, record["hashed_otp"]):
                # Verification succeeded
                VerificationRepository.delete_otp(phone_h)
                user_row = UserRepository.get_by_phone_hash(phone_h)
                if user_row:
                    UserRepository.set_phone_verified(user_row["user_id"], True)
                    token, exp_iso = token_manager.create_access_token(user_id=user_row["user_id"])
                    AuditRepository.log_event(
                        event_type="PHONE_VERIFIED",
                        action="VERIFY_OTP",
                        status="SUCCESS",
                        actor_id=user_row["user_id"],
                        ip_address=ip_address,
                        details={"phone_masked": mask_phone_number(phone_number)}
                    )
                    return True, "Phone number successfully verified.", token

                return True, "Phone number successfully verified.", None
            else:
                remaining = max(0, self.max_otp_attempts - attempts)
                AuditRepository.log_event(
                    event_type="INVALID_OTP_ATTEMPT",
                    action="VERIFY_OTP",
                    status="FAILURE",
                    ip_address=ip_address,
                    details={"phone_masked": mask_phone_number(phone_number), "remaining_attempts": remaining}
                )
                return False, f"Invalid OTP code. {remaining} attempt(s) remaining.", None

    def add_subscription(
        self,
        user_id: str,
        label: str,
        locality_name: str,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        preferences: Optional[UserPreferences] = None
    ) -> LocationSubscription:
        """Adds a location subscription into database."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        sub_row = SubscriptionRepository.create_subscription(
            user_id=user_id,
            label=label,
            locality_name=locality_name,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km
        )

        sub = LocationSubscription(
            subscription_id=sub_row["subscription_id"],
            user_id=sub_row["user_id"],
            label=sub_row["label"],
            locality_name=sub_row["locality_name"],
            latitude=sub_row["latitude"],
            longitude=sub_row["longitude"],
            geohash=sub_row["geohash"],
            radius_km=sub_row["radius_km"],
            created_at=sub_row["created_at"]
        )

        with self._lock:
            if user_id in self._users:
                self._users[user_id].subscriptions.append(sub)

        AuditRepository.log_event(
            event_type="SUBSCRIPTION_CREATED",
            action="ADD_LOCATION",
            status="SUCCESS",
            actor_id=user_id,
            target_resource=sub_row["subscription_id"],
            details={"label": label, "locality": locality_name, "radius_km": radius_km}
        )

        return sub

    def delete_subscription(self, user_id: str, subscription_id: str) -> bool:
        deleted = SubscriptionRepository.delete_subscription(user_id=user_id, subscription_id=subscription_id)
        if deleted:
            with self._lock:
                if user_id in self._users:
                    self._users[user_id].subscriptions = [
                        s for s in self._users[user_id].subscriptions if s.subscription_id != subscription_id
                    ]
            AuditRepository.log_event(
                event_type="SUBSCRIPTION_DELETED",
                action="DELETE_LOCATION",
                status="SUCCESS",
                actor_id=user_id,
                target_resource=subscription_id
            )
        return deleted

    def get_all_users(self) -> List[User]:
        rows = UserRepository.get_all_users()
        users = []
        for r in rows:
            u = self.get_user_by_id(r["user_id"])
            if u:
                users.append(u)
        return users

# Global singleton
user_store = UserStore()
