# JALDRISHTI AI — Admin & Security Portal Audit Report

**Date**: 2026-08-31  
**Target System**: Admin, RBAC & Security Operations Console  

---

## 1. Executive Summary

This audit establishes the baseline architectural state of the administrative control plane in JALDRISHTI AI prior to the Phase 22 Operations Portal overhaul.

---

## 2. Authentication & Identity Baseline

- **Token Architecture**: HMAC-SHA256 tokens created via `TokenManager` (`services/notifications/security.py`).
- **Token Claims**: Contains `sub` (User/Operator ID), `role` (`PUBLIC_USER`, `OPERATOR`, `ADMIN`), `exp` (Expiration timestamp), `iat` (Issued at timestamp), `iss` (`jaldrishti.ai`).
- **Secret Key Handling**: Uses `CITIZEN_AUTH_SECRET_KEY` environment variable with secure fallback. Never exposed to frontend or logged in plain text.
- **Current Token Validation**: Handled per-endpoint via `token_manager.verify_access_token(token)`.

---

## 3. RBAC & Roles Matrix

| Role | Scope / Permissions | Permitted Capabilities | Restricted Capabilities |
|---|---|---|---|
| `PUBLIC_USER` | Public Portal & Citizen Inbox | View map, subscribe to locality, receive geofenced notifications | Admin security status, alert human review, provider refresh, audit logs |
| `OPERATOR` | Hydromet Monitoring & Operations | View data health, review alert candidates, acknowledge/downgrade alerts with reason | System mode mutation, provider credentials management, full audit deletion |
| `ADMIN` | Complete System Control Plane | Full operator capabilities + audit log query, rate limit monitoring, model catalog management, security status inspection | N/A (Full Administrative Access) |

---

## 4. Administrative API Endpoints Baseline

- **`GET /api/v1/security/status`**: Returns security audit status, active rate limiters, database engine state, DLT configuration, audit log totals. Requires `Authorization: Bearer <TOKEN>` with role `ADMIN` or `OPERATOR`.
- **`POST /api/v1/live/imd-aws/refresh`**: Triggers manual provider ingestion cycle. Rate-limited by 5s cooldown.
- **`POST /api/v1/live/connect`**: Toggles live mode with required `confirm=true` safety lock parameter.

---

## 5. Security & Privacy Audit Findings

1. **Backend Security Boundary**: Verified that frontend state NEVER dictates security authorization. Requests without valid tokens return `HTTP 401 Unauthorized`; requests with inadequate roles return `HTTP 403 Forbidden`.
2. **Privacy Protection**: Phone numbers are masked via `mask_phone_number()` (e.g. `******3210`). Plaintext OTPs and secrets are strictly excluded from API payloads and error logs.
3. **Database Labeling**: Distinguishes `SQLite / DEVELOPMENT RUNTIME` from `PostgreSQL + PostGIS / ACTIVE` without fabricating production postgis status.

