# JALDRISHTI AI — Public Notification Rate Limiting & Abuse Prevention

## 1. Multi-Dimensional Threat Model
Public endpoints (especially SMS OTP generation and subscription management) are vulnerable to automated enumeration, SMS pumping fraud, and denial-of-wallet attacks. JALDRISHTI AI enforces a 3-tier sliding window rate limiter:

| Dimension | Scope | Limit | Window | Action on Breach |
| :--- | :--- | :--- | :--- | :--- |
| **IP Address** | `POST /api/v1/user/send-otp` | 10 req | 1 hour | 429 Too Many Requests (`Retry-After: 3600`) |
| **Phone Number (Hashed)** | `POST /api/v1/user/send-otp` | 3 req | 10 mins | 429 Too Many Requests (`Retry-After: 600`) |
| **User ID / Token** | `/api/v1/user/subscriptions` | 30 req | 1 min | 429 Rate Limit (`Retry-After: 60`) |

---

## 2. Sliding Window Algorithm
The sliding window counter tracks UTC timestamps in circular buffers per key. Stale requests older than `window_seconds` are purged dynamically before checking if `current_count < max_requests`.

---

## 3. Brute-Force Lockout Policy
- Maximum allowed OTP verification attempts per cycle: **3 attempts**.
- On the 4th consecutive invalid attempt:
  1. The OTP hash and salt are permanently deleted from `user_verifications`.
  2. The phone identifier is locked out for 15 minutes.
  3. A high-priority security audit event (`BRUTE_FORCE_LOCKOUT`) is logged with IP address and timestamp.
