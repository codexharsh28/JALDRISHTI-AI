# JALDRISHTI AI — Security Architecture & Hardening Guide

## 1. Multi-Layer Defense-in-Depth Architecture

```
[ Client / Browser / Public User ]
               |
               v   (HTTPS / TLS 1.3)
+-----------------------------------------------------------+
| REVERSE PROXY / INGRESS                                   |
| - Security Headers (CSP, HSTS, X-Frame-Options)           |
| - 2 MB Payload Size Guard (HTTP 413)                      |
| - CORS Whitelist                                          |
+-----------------------------------------------------------+
               |
               v
+-----------------------------------------------------------+
| FASTAPI APPLICATION SECURITY LAYER                        |
| - Multi-Dimensional Sliding Window Rate Limiter          |
| - HMAC-SHA256 Token Verification & IDOR Enforcement       |
| - Role-Based Access Control (PUBLIC_USER, OPERATOR, ADMIN)|
| - Input Sanitization & Parameterized Queries              |
+-----------------------------------------------------------+
               |
               v
+-----------------------------------------------------------+
| RELATIONAL DATABASE PERSISTENCE LAYER                     |
| - PostgreSQL / PostGIS (WAL Mode, Spatial GIST Indexes)   |
| - Foreign Key Cascades & Strict Domain Constraints        |
| - Salted Hashes Only (Zero Plaintext OTP / Passwords)     |
| - Append-Only Cryptographic Audit Logging                 |
+-----------------------------------------------------------+
```

---

## 2. Core Security Principles
1. **Zero Plaintext Credentials**: Plaintext OTPs, tokens, and credentials are never persisted to disk, logged in console/files, or transmitted in public API responses.
2. **Strict Object-Level Authorization (IDOR Protection)**: Every resource query verifies subject ownership against the cryptographically signed Bearer token.
3. **Defense Against Denial-of-Wallet**: Multi-dimensional rate limiters throttle IP, hashed phone numbers, and user tokens to block automated SMS fraud and enumeration attacks.
4. **Least-Privilege Database Role**: Application database users operate under restricted DML privileges without superuser or destructive DDL capabilities.
