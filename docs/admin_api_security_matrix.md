# JALDRISHTI AI — Admin API Security & RBAC Matrix

**Date**: 2026-08-31  

---

## Administrative & Operations API Endpoints

| Endpoint Path | HTTP Method | Minimum Required Role | Rate Limit Policy | Audit Logging Behavior |
|---|---|---|---|---|
| `/api/v1/auth/login` | `POST` | `ANY` | 5 requests / minute per IP | Audits `LOGIN_SUCCESS` or `LOGIN_FAILURE` |
| `/api/v1/auth/logout` | `POST` | `OPERATOR` / `ADMIN` | None | Audits `LOGOUT_EXECUTED` |
| `/api/v1/security/status` | `GET` | `OPERATOR` / `ADMIN` | 30 requests / minute | Audits `SECURITY_STATUS_VERIFY` |
| `/api/v1/admin/audit-logs` | `GET` | `ADMIN` | 20 requests / minute | Audits `AUDIT_LOG_QUERY` |
| `/api/v1/admin/human-review` | `GET` | `OPERATOR` / `ADMIN` | 30 requests / minute | Read-only candidate list fetch |
| `/api/v1/admin/human-review/action` | `POST` | `OPERATOR` / `ADMIN` | 10 requests / minute | Audits `ALERT_ACKNOWLEDGED`, `ALERT_DOWNGRADED`, or `ALERT_DISMISSED` with actor & reason |
| `/api/v1/admin/rate-limits` | `GET` | `ADMIN` | 20 requests / minute | Exposes aggregate metrics without user PII |
| `/api/v1/live/imd-aws/refresh` | `POST` | `OPERATOR` / `ADMIN` | 5s minimum provider cooldown | Audits `IMD_AWS_MANUAL_REFRESH` |
| `/api/v1/live/connect` | `POST` | `ADMIN` | Require `confirm=true` safety lock | Audits `MODE_CHANGED_TO_LIVE` |

---

## Security Error Response Contracts

- **Missing / Invalid Bearer Token**: `HTTP 401 Unauthorized`
- **Insufficient Role Privileges (e.g. PUBLIC_USER calling admin endpoint)**: `HTTP 403 Forbidden`
- **Rate Limit Exceeded**: `HTTP 429 Too Many Requests` (includes `Retry-After` header)
- **Missing Required Reason / Confirmation Parameter**: `HTTP 400 Bad Request`

