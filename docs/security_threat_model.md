# JALDRISHTI AI — Security Threat Model (STRIDE Framework)

## 1. STRIDE Analysis Matrix

| Category | Threat Description | Attacker Objective | Mitigating Control in JALDRISHTI |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Forged citizen tokens or identity | Impersonate another citizen to access private alerts/subscriptions | HMAC-SHA256 token verification, cryptographic signature checks, expiry validation. |
| **Tampering** | Parameter tampering / SQL Injection | Modify hazard polygons or inject malicious database queries | 100% Parameterized queries, Pydantic type validation, database check constraints. |
| **Repudiation** | Operator denying acknowledged alerts | Claim an emergency action was not authorized | Immutable append-only `audit_logs` recording actor ID, role, action, and timestamp. |
| **Information Disclosure** | Plaintext OTP leakage / Full phone exposure | Intercept verification codes or harvest citizen mobile numbers | Salted SHA-256 OTP hashes, global phone masking (`******3210`), sanitized API responses. |
| **Denial of Service** | SMS pumping / WebSocket connection flood | Exhaust carrier credits or crash real-time WebSocket server | Sliding-window rate limiters, 20 connection limit per IP, 2 MB request payload cap (HTTP 413). |
| **Elevation of Privilege** | Citizen executing operator alert actions | Trigger emergency sirens or change river thresholds without approval | Server-side role enforcement (`verify_user_access`), operator token gating on decision actions. |
