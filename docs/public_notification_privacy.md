# JALDRISHTI AI — Public Notification Privacy Architecture

## 1. Principles of Data Minimization
JALDRISHTI AI operates on strict citizen data minimization principles:
- No citizen names, Aadhaar numbers, residential street addresses, or payment details are collected or retained.
- Only the minimum required parameters (`phone_number`, `preferred_language`, `locality_name`, `coordinates` and `radius_km`) are stored.

## 2. Phone Privacy & Cryptographic Hashing
- Incoming mobile numbers are stripped of non-digits and indexed via deterministic SHA-256 phone hashes:
  $$\text{phone\_hash} = \text{SHA-256}(\text{clean\_digits})$$
- Only the last 10 digits are stored for dispatch purposes.
- OTPs are never stored in plaintext: they are combined with a cryptographically secure 16-hex salt and stored as a salted SHA-256 hash.
- OTPs and phone numbers are never logged in system runtime logs.

## 3. Location & Spatial Privacy
- Location subscriptions allow coarse representations (e.g. Locality name, geohash, centroid coordinates with configured safety radius).
- User locations and phone numbers are strictly prohibited from public WebSocket channels and public alert endpoints.

## 4. Public API Isolation
Public alert endpoints (`/api/v1/public-alerts/current` and `/api/v1/public-alerts/{id}`) return only geographical hazard summaries, official emergency instructions, and uncertainty notes without user identities.
