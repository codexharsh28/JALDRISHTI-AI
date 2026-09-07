# JALDRISHTI AI — Real-Time Failure Recovery & Resilience

## 1. Failure Modes & Automated Recovery

| Failure Scenario | Detection Mechanism | Automated Recovery Strategy |
| :--- | :--- | :--- |
| **Upstream Telemetry Timeout** | Adapter timeout ($8.0\text{s}$) | Mark source `DEGRADED`, trigger GloFAS modeled fallback, emit `SOURCE_HEALTH_CHANGED`. |
| **Malformed Payload / Checksum Mismatch** | QC validation engine | Reject payload, emit `SOURCE_DATA_REJECTED` with error details, retain previous valid state. |
| **Forecast Worker Crash** | Async task exception handler | Mark job `FAILED`, release running lock, log stack trace, trigger non-overlapping retry. |
| **Event Bus Backpressure** | Bounded queue ($N=1000$) | Shed `LOW` / `NORMAL` telemetry updates; **NEVER** drop `CRITICAL` alert events. |
| **WebSocket Network Severance** | Ping/Pong heartbeat ($5\text{s}$) | Client executes exponential backoff reconnect and requests missing delta via `SYNC_STATE`. |

---

## 2. Deduplication Protocol
Duplicate deliveries from upstream APIs or network retries are filtered at the ingestion boundary using a SHA-256 fingerprint:
$$\text{Fingerprint} = \text{SHA256}(\text{source\_id} \mathbin{\Vert} \text{occurred\_at} \mathbin{\Vert} \text{payload\_hash})$$
Duplicate payloads are acknowledged but safely discarded without triggering downstream duplicate forecasts.
