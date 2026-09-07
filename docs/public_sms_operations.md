# JALDRISHTI AI — Public SMS Operations & DLT Compliance

## 1. Regulatory Context (Telecom Regulatory Authority of India - TRAI)
Under TRAI Distributed Ledger Technology (DLT) regulations, bulk emergency SMS traffic in India must comply with strict registration protocols:
- **Principal Entity Registration**: JALDRISHTI AI / Disaster Management Agency registered entity identifier (`DLT_ENTITY_ID`).
- **Sender ID / Header**: Pre-registered 6-character alphabetic header (`DLT_SENDER_ID`, e.g., `JLDRST`).
- **Approved Message Templates**: Pre-approved template hash (`DLT_TEMPLATE_ID`) with strict parameter placeholders `{1}`, `{2}`.

## 2. Configuration & Credentials Policy
SMS dispatches require environment variables to be explicitly set in the backend environment:
```env
MSG91_AUTH_KEY=...
DLT_ENTITY_ID=...
DLT_SENDER_ID=...
DLT_TEMPLATE_ID=...
```

If any required DLT variable is missing:
- Production SMS status is reported as `NOT_CONFIGURED`.
- Attempts to dispatch production SMS fail cleanly with audit records.
- In local development and automated testing, `MockSMSSink` is automatically utilized.

## 3. Mock SMS Sink Isolation
`MockSMSSink` captures all outbound payloads (recipient, template_id, title, body, timestamp) in memory and logs them safely without interacting with public telecommunication carriers.

## 4. Delivery State Machine
The delivery tracker recognizes 7 distinct states:
1. `QUEUED`: Enqueued in memory awaiting worker pick-up.
2. `PROCESSING`: Provider API call initiated.
3. `SENT`: Provider accepted message for transmission.
4. `DELIVERED`: Provider confirmed delivery via delivery receipt.
5. `RETRYING`: Transient error (429/timeout); retrying with exponential backoff.
6. `FAILED`: Terminal failure (invalid number, exhausted retries, unconfigured gateway).
7. `EXPIRED`: Alert valid horizon elapsed before dispatch.

> **CRITICAL RULE**: `SENT` is NEVER equated to `DELIVERED`.
