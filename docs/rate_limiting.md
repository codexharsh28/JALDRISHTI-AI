# JALDRISHTI AI — Rate Limiting, Sliding Windows & Abuse Prevention

## 1. Multi-Dimensional Sliding Window Algorithm
Rate limiting in JALDRISHTI AI operates on timestamp-tracked sliding windows per unique key. This prevents "burst at window boundary" attacks common in simple fixed counters.

---

## 2. Default Configuration Matrix (`config/security.yaml`)

| Dimension | Window | Threshold | Lockout on Breach | Target Endpoint |
| :--- | :--- | :--- | :--- | :--- |
| **Phone Hash** | 10 mins | 3 requests | 10 mins | `POST /api/v1/user/send-otp` |
| **Phone Hash** | 10 mins | 5 requests | 15 mins | `POST /api/v1/user/verify-phone` |
| **Client IP** | 1 hour | 10 requests | 1 hour | `POST /api/v1/user/register` |
| **User ID** | 1 min | 30 requests | 1 min | `POST/DELETE /api/v1/user/subscriptions` |
| **Client IP** | 1 min | 120 requests | 1 min | `GET /api/v1/public-alerts/*` |
| **WebSocket IP** | Continuous | 20 connections | Immediate reject | `/ws/v1/live` |

---

## 3. Response on Breach
When a rate limit is exceeded, JALDRISHTI AI returns `HTTP 429 Too Many Requests` with a standard `Retry-After: <seconds>` response header and does NOT disclose whether the account/phone exists.
