# JALDRISHTI AI — Public Notification Database Schema & Architecture

## 1. Overview
The Public Notification database subsystem is designed with enterprise-grade relational guarantees, supporting High Availability (HA), WAL journaling, strict foreign-key integrity cascades, salted OTP hashes, and immutable audit trails.

---

## 2. Schema Architecture

```
+--------------------+        1:N        +-------------------------+
|       users        | ----------------< | location_subscriptions  |
+--------------------+                   +-------------------------+
          | 1:N
          |
          +-----------------------------< +-------------------------+
          |                               |   device_push_tokens    |
          | 1:N                           +-------------------------+
          |
          +-----------------------------< +-------------------------+
          |                               |  user_verifications     |
          | 1:N                           +-------------------------+
          |
          +-----------------------------< +-------------------------+
                                          |   notification_inbox    |
                                          +-------------------------+
```

### Table Definitions

1. **`users`**
   - `user_id` (TEXT, PK): Unique prefixed identifier (`USR-...`).
   - `phone_hash` (TEXT, UNIQUE): SHA-256 deterministic hash of normalized MSISDN.
   - `phone_masked` (TEXT): Display string masking all but last 4 digits (`******3210`).
   - `phone_verified` (BOOLEAN): Strict gating flag for emergency SMS broadcasts.
   - `preferred_language` (TEXT): BCP-47 / ISO code (`en`, `hi`, `or`).
   - `status` (TEXT): User state (`ACTIVE`, `SUSPENDED`).

2. **`user_verifications`**
   - `verification_id` (TEXT, PK)
   - `phone_hash` (TEXT)
   - `salt` (TEXT): 8-byte hex cryptographic salt.
   - `hashed_otp` (TEXT): SHA-256 hash of `salt:plaintext_otp`.
   - `attempts` (INTEGER): Brute force counter (lockout triggered at >3).
   - `expires_at` (TIMESTAMP): Strict 10-minute expiry window.

3. **`location_subscriptions`**
   - `subscription_id` (TEXT, PK): Prefixed identifier (`SUB-...`).
   - `user_id` (TEXT, FK -> users.user_id ON DELETE CASCADE)
   - `label` (TEXT): User-defined category (`HOME`, `WORK`, `FAMILY`, `FARMLAND`).
   - `locality_name` (TEXT): Human-readable settlement or administrative division.
   - `latitude`, `longitude` (REAL): WGS-84 coordinates.
   - `radius_km` (REAL): Spatial geofence safety radius (default: 10.0 km).

4. **`notifications` & `notification_deliveries`**
   - Stores dispatched citizen notifications with cryptographic provenance, template ID, delivery status (`QUEUED`, `SENT`, `DELIVERED`, `FAILED`, `SUPPRESSED`), latency in ms, and provider message IDs.

5. **`audit_logs`**
   - Immutable audit trail recording user registrations, OTP requests, verification events, rate limit breaches, and subscription lifecycle changes with actor ID and IP addresses.

---

## 3. Database Invariants
- `PRAGMA foreign_keys = ON;` is enforced unconditionally on every connection.
- WAL (Write-Ahead Logging) journaling mode is active for high-throughput concurrency.
- Plaintext phone numbers and plaintext OTPs are strictly prohibited from disk persistence.
