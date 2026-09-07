# JALDRISHTI AI — Real-Time State Management & Versioning

## 1. Monotonic State Versioning Protocol

To prevent state drift between distributed browser clients and backend services, every change to the operational state increments a monotonically increasing integer: `state_version`.

```
[Initial State: v1000]
        ↓
  Source Ingestion (IMD AWS) ──> v1001
        ↓
  Coalesced Forecast Trigger ──> v1002
        ↓
  Hydrology Forecast Updated ──> v1003
        ↓
  Inundation Surface Updated ──> v1004
        ↓
  Alert Safety Gate Trigger  ──> v1005
```

---

## 2. Reconnect & Delta Synchronization

When a client reconnects after network interruption:
1. Client transmits: `{"action": "SYNC_STATE", "last_state_version": 1002}`
2. **Delta Query**: If $(v_{\text{current}} - v_{\text{client}}) \le 50$, the server replays all intermediate events from the `EventStore`.
3. **Full State Fallback**: If the gap exceeds 50 versions, the server transmits `FULL_STATE_REQUIRED` alongside the complete atomic snapshot from `data/state/current_state_snapshot.json`.

---

## 3. Crash Recovery & Snapshot Persistence
- The current state is periodically persisted to `data/state/current_state_snapshot.json`.
- Upon backend startup, the system restores the latest snapshot and replays uncommitted events from `data/events/events_{YYYYMMDD}.jsonl`.
