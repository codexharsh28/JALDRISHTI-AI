# JALDRISHTI AI — Notification Security & Credential Isolation

## 1. Backend-Only Credential Isolation
All SMS, Push, and telecommunication credentials remain strictly inside backend server environments:
- **MSG91 / Twilio Secrets**: Never exposed to Vite/React client bundles or public repositories.
- **Firebase Service Accounts**: Stored server-side in secure secret stores.
- **OTP Verification**: Handled entirely within backend authorization endpoints.

## 2. API Endpoint Protection & Rate Limiting
- **OTP Generation Endpoint (`POST /api/v1/user/send-otp`)**:
  - Bound to 3 requests per 10-minute sliding window per phone hash.
  - Returns `429 Too Many Requests` on violation.
- **OTP Verification Endpoint (`POST /api/v1/user/verify-phone`)**:
  - Bound to 3 attempts maximum before the active OTP is invalidated.
  - Uses `secrets.compare_digest` for constant-time hash comparison to prevent timing attacks.

## 3. Provenance & Audit Logging
Every queued notification includes complete end-to-end provenance:
- `notification_id`
- `alert_id`
- `forecast_run_id`
- `user_region`
- `channel`
- `template_id`
- `data_state`
- `created_at`
