# JALDRISHTI AI — Master API Security Matrix

## Comprehensive Endpoint Security Catalog

| HTTP Method | Path Pattern | Authentication | Authorization (RBAC) | Rate Limiting Policy | Input Validation & Sanitization | Sensitive Data Treatment |
|---|---|---|---|---|---|---|
| `POST` | `/api/v1/public/auth/send-otp` | Public | None | 3 req / 60s per IP/Phone | E.164 phone regex, length bounded | OTP hashed with salt; never returned in API |
| `POST` | `/api/v1/public/auth/verify-otp` | Public | None | 5 attempts / 5 mins | Strict 6-digit numeric | Returns short-lived bearer JWT |
| `GET` | `/api/v1/public/users/me` | Bearer JWT | Authenticated User | 60 req / min | None | Phone number masked (`******3210`) |
| `GET` | `/api/v1/public/subscriptions` | Bearer JWT | User Isolation (`user_id = JWT.sub`) | 60 req / min | IDOR/BOLA blocked | Restricts output strictly to caller's records |
| `POST` | `/api/v1/public/subscriptions` | Bearer JWT | Authenticated User | 10 req / min | Latitude/Longitude bounds, alias enum | Coordinates validated within pilot polygon |
| `DELETE` | `/api/v1/public/subscriptions/{id}`| Bearer JWT | Subscription Owner (`IDOR checked`) | 30 req / min | UUID path format | Prevents cross-user deletion |
| `GET` | `/api/v1/public/notifications` | Bearer JWT | User Isolation (`user_id = JWT.sub`) | 60 req / min | Limit/offset bounds | Prevents cross-user inbox reading |
| `GET` | `/api/v1/live/imd-aws/status` | Public / Operator | None | 60 req / min | None | Credentials/tokens stripped from endpoint |
| `GET` | `/api/v1/live/imd-aws/stations` | Public / Operator | None | 60 req / min | Query params sanitized | Station coordinates & metadata |
| `POST` | `/api/v1/live/imd-aws/refresh` | Operator Key | Operator / Admin | 5 req / min (5s cooldown) | Query flag `force=true` | Triggers background ingestion |
| `GET` | `/api/v1/alerts/current` | Public / Operator | None | 120 req / min | None | Sanitized alert payloads |
| `POST` | `/api/v1/alerts/{id}/review` | Bearer JWT | Operator / Admin | 30 req / min | Decision enum (`ACK`, `ESCALATE`, `DISMISS`) | Audit logged with operator user ID |
| `POST` | `/api/v1/demo/start` | Operator Key | Operator / Admin | 5 req / min | Scenario ID enum | Sandboxed simulation; does not touch live state |
| `POST` | `/api/v1/demo/reset` | Operator Key | Operator / Admin | 5 req / min | None | Clears demo state cleanly |
| `WS` | `/ws/events` | Optional Token | Read-Only Event Stream | Max 20 connections per IP | Protocol ping-pong heartbeat | Emits sanitized operational deltas |
| `GET` | `/api/v1/security/status` | Bearer JWT | Admin Only | 20 req / min | None | RBAC blocked for standard public users |
