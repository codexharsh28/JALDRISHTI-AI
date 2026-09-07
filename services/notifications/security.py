"""
Security, Authentication Tokens, Rate Limiting & Authorization for JALDRISHTI AI Public Notifications.
Enforces multi-dimensional rate limiting, brute force lockout, token signing, and IDOR protection.
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import base64
import json
import os
import time
import threading
import logging

logger = logging.getLogger(__name__)

def _get_auth_secret_key() -> str:
    secret = os.getenv("CITIZEN_AUTH_SECRET_KEY")
    if not secret:
        app_env = os.getenv("APP_ENV", "development").lower()
        if app_env in ["production", "staging"]:
            raise RuntimeError("CITIZEN_AUTH_SECRET_KEY environment variable is required in production/staging environment")
        logger.warning("CITIZEN_AUTH_SECRET_KEY not set in environment; using secure fallback for local development.")
        return "jaldrishti-citizen-auth-secret-key-2026-delta"
    return secret

AUTH_SECRET_KEY = _get_auth_secret_key()
TOKEN_TTL_HOURS = int(os.getenv("CITIZEN_TOKEN_TTL_HOURS", "24"))

def mask_phone_number(phone: str) -> str:
    """Masks phone number for privacy display (e.g. +919876543210 -> ******3210)."""
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) >= 4:
        return f"******{digits[-4:]}"
    return "******"

class TokenManager:
    """
    Signs and verifies secure HMAC-SHA256 citizen access tokens without external library overhead.
    """

    @staticmethod
    def create_access_token(
        user_id: str,
        role: str = "PUBLIC_USER",
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, str]:
        """Returns (token_string, expires_at_iso)."""
        expires_in = expires_delta or timedelta(hours=TOKEN_TTL_HOURS)
        exp = datetime.now(timezone.utc) + expires_in
        payload = {
            "sub": user_id,
            "role": role,
            "exp": int(exp.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "iss": "jaldrishti.ai"
        }
        raw_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = hmac.new(
            AUTH_SECRET_KEY.encode(),
            raw_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        token = f"{raw_payload}.{signature}"
        return token, exp.isoformat()

    @staticmethod
    def verify_access_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verifies token integrity, signature, and expiration.
        Returns: (is_valid, payload_dict, error_message)
        """
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return False, None, "Invalid token format"

            raw_payload, signature = parts[0], parts[1]
            # Verify signature using constant-time comparison
            expected_sig = hmac.new(
                AUTH_SECRET_KEY.encode(),
                raw_payload.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                return False, None, "Invalid token signature"

            # Pad base64 payload if needed
            pad = len(raw_payload) % 4
            b64_str = raw_payload + ("=" * (4 - pad) if pad else "")
            payload_json = base64.urlsafe_b64decode(b64_str.encode()).decode()
            payload = json.loads(payload_json)

            # Check expiration
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if payload.get("exp", 0) < now_ts:
                return False, None, "Token has expired"

            return True, payload, None
        except Exception as e:
            return False, None, f"Token validation error: {str(e)}"

class MultiDimensionRateLimiter:
    """
    Sliding window rate limiter across IP, user_id, phone_hash, and action dimensions.
    Returns whether request is allowed, remaining requests, and retry-after seconds.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Storage: dimension_key -> list of timestamp floats
        self._requests: Dict[str, List[float]] = {}
        # Lockout registry: dimension_key -> lockout_until_timestamp
        self._lockouts: Dict[str, float] = {}

    def check_rate_limit(
        self,
        dimension_type: str,
        identifier: str,
        max_requests: int = 10,
        window_seconds: int = 60,
        lockout_seconds_on_breach: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Returns: (is_allowed, remaining_quota, retry_after_seconds)
        """
        now = time.time()
        key = f"{dimension_type}:{identifier}"

        with self._lock:
            # Check active lockout
            if key in self._lockouts:
                lockout_end = self._lockouts[key]
                if now < lockout_end:
                    retry_after = int(lockout_end - now) + 1
                    return False, 0, retry_after
                else:
                    del self._lockouts[key]

            # Prune old timestamps
            history = self._requests.get(key, [])
            cutoff = now - window_seconds
            history = [t for t in history if t > cutoff]

            if len(history) >= max_requests:
                # Apply lockout
                self._lockouts[key] = now + lockout_seconds_on_breach
                self._requests[key] = history
                return False, 0, lockout_seconds_on_breach

            # Record current hit
            history.append(now)
            self._requests[key] = history
            remaining = max(0, max_requests - len(history))
            return True, remaining, 0

    def reset_limit(self, dimension_type: str, identifier: str) -> None:
        key = f"{dimension_type}:{identifier}"
        with self._lock:
            if key in self._requests:
                del self._requests[key]
            if key in self._lockouts:
                del self._lockouts[key]

# Global singleton instances
token_manager = TokenManager()
rate_limiter = MultiDimensionRateLimiter()
