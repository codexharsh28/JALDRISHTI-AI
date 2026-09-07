# Coalesced Forecast Triggering & Concurrency Control
## JALDRISHTI AI (SIH26071)

---

## 1. Coalescing Window & Aggregation

When multiple asynchronous external sources deliver observations within a brief time window (e.g. IMD AWS, IMERG Early, and CWC gauges arriving within seconds of each other), JALDRISHTI AI does not launch separate overlapping forecast runs.

```mermaid
sequenceDiagram
    participant IMD as IMD AWS Update
    participant IMERG as IMERG Early Update
    participant CWC as CWC Gauge Update
    participant StateMgr as CurrentStateManager
    participant ML as Model Hierarchy (L0-L3)

    IMD->>StateMgr: notify_source_update("IMD_ODISHA_AWS")
    IMERG->>StateMgr: notify_source_update("NASA_GPM_IMERG_EARLY")
    CWC->>StateMgr: notify_source_update("CWC_WRIS_TELEMETRY")
    Note over StateMgr: Coalescing / Debounce Window (2.5s)
    StateMgr->>ML: trigger_coalesced_forecast() [Single forecast_run_id]
    ML-->>StateMgr: Forecast Output & Inundation Map
    StateMgr->>StateMgr: Persist Provenance Chain (ingestion_run_ids -> forecast_run_id)
```

---

## 2. Concurrency Safety & Running-State Locks

1. **Running-State Lock:** If a forecast computation is currently executing, incoming updates are queued and coalesced into the subsequent run cycle.
2. **Minimum Forecast Throttling:** Ensures the deep model pipeline is not triggered more frequently than the configured minimum forecast interval ($5.0\text{ seconds}$).
3. **Atomic Run Identification:** Every forecast run generates an immutable `forecast_run_id` (e.g. `FR-LIVE-20260827-XXXXXX`).
