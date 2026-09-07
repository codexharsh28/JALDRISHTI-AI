# JALDRISHTI AI — Privacy Model, Data Anonymization & Citizen Protection

## 1. Principles of Minimal Exposure & Anonymization
JALDRISHTI AI enforces strict citizen data protection aligned with India's **Digital Personal Data Protection (DPDP) Act**:

1. **Hashed Identification**: Mobile numbers are stored internally as cryptographically salted SHA-256 hashes (`phone_hash`). Plaintext mobile numbers are never saved in database tables.
2. **Masked Public Rendering**: In all UI views, WebSocket packets, API responses, and server logs, mobile numbers are masked (e.g., `******3210`), preserving only the last 4 digits for visual confirmation.
3. **No Continuous GPS Tracking**: The platform does not track real-time citizen movements. Geofenced alerting operates exclusively on explicit, user-subscribed approximate localities and geohashes.
4. **Right to Erasure**: Citizens can delete their registered location subscriptions and account preferences at any time, initiating a cascade delete across all personal tables.
