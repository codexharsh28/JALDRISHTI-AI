# JALDRISHTI AI — Security Baseline Audit & Vulnerability Assessment

## 1. Executive Summary
This document establishes the comprehensive security baseline audit for the **JALDRISHTI AI Platform** following the integration of the Public Citizen Safety & Alert subsystems.

The system was evaluated against the **OWASP Top 10 API Security Risks (2023)**, **NIST SP 800-53**, and India DLT/TRAI telecommunication regulations.

---

## 2. Vulnerability Findings & Classification Matrix

| Finding ID | Vulnerability Title | Category | Severity | Initial Status | Hardened Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | Plaintext Development OTP in Public API Response | Information Disclosure | **CRITICAL** | Remediated | Removed `dev_otp_preview` from all JSON responses. Isolated to internal server-side test sink. |
| **SEC-002** | Broken Object Level Authorization (IDOR) on Subscriptions | Authorization | **HIGH** | Remediated | Added `verify_user_access` token subject checks enforcing strict ownership on all `/api/v1/user/*` routes. |
| **SEC-003** | Missing Rate Limiting on Public OTP Generation | Abuse / Denial of Wallet | **HIGH** | Remediated | Enforced 3-tier sliding window limiter (10 req/hr per IP, 3 req/10min per phone hash) returning `429 Retry-After`. |
| **SEC-004** | Plaintext OTP Brute-Forcing Risk | Authentication | **HIGH** | Remediated | Stored only salted SHA-256 OTP hashes. Implemented strict 3-attempt lockout with 15-minute freeze. |
| **SEC-005** | Overly Permissive CORS Policy (`allow_origins=["*"]`) | Network Security | **MEDIUM** | Remediated | Replaced with explicit allowed origin whitelist derived from `config/security.yaml`. |
| **SEC-006** | Missing HTTP Request Size Limitation (DoS via Memory Inflation) | Denial of Service | **MEDIUM** | Remediated | Added middleware restricting max request body size to 2 MB (`413 Payload Too Large`). |
| **SEC-007** | WebSocket Flooding & Unbounded Connections | Connection Exhaustion | **MEDIUM** | Remediated | Enforced 20 connection limit per IP and 60 msg/min throttling on `/ws/v1/live`. |
| **SEC-008** | Full Phone Number Exposure in UI State | User Privacy | **MEDIUM** | Remediated | Masked phone numbers globally (`******3210`) across all responses, frontend state, and logs. |
| **SEC-009** | Missing Standard Security Headers | Header Hardening | **LOW** | Remediated | Injected `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and CSP. |
| **SEC-010** | Database Dialect Portability to PostgreSQL / PostGIS | Persistence Architecture | **INFO** | Documented | Created production PostgreSQL DDL with PostGIS geometries and spatial GIST indexing. |

---

## 3. Severity Breakdown
- **CRITICAL**: 1 (Fixed)
- **HIGH**: 3 (Fixed)
- **MEDIUM**: 4 (Fixed)
- **LOW**: 1 (Fixed)
- **INFO**: 1 (Standardized)
- **UNRESOLVED VULNERABILITIES**: 0
