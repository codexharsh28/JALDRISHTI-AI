# JALDRISHTI AI — Secret Management, Key Rotation & Environment Hygiene

## 1. Zero-Secret In-Source Code Policy
- Hardcoding API tokens, private keys, database passwords, or SMS gateway credentials in source control or documentation is strictly prohibited.
- All secrets are injected dynamically via environment variables (`MSG91_AUTH_KEY`, `FIREBASE_CREDENTIALS_PATH`, `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`).

---

## 2. Key Rotation Protocol
- **JWT Signing Keys**: Rotated every 90 days. The token verification subsystem supports dual key verification during transition grace windows.
- **Provider Gateway Keys**: If an external provider key is rotated, zero restart is required when utilizing container secret orchestration or KMS injection.
- **Development Mock Fallback**: In local test environments without production credentials, the system automatically falls back to safe in-memory mock sinks (`MockSMSSink`, `MockPushSink`), avoiding any accidental external transmission.
