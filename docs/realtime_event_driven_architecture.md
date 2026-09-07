# JALDRISHTI AI — Real-Time Event-Driven Architecture

## 1. Executive Summary
Phase 12 transforms JALDRISHTI AI into a genuinely reactive, event-driven operational streaming architecture.

Rather than relying on periodic polling or synthetic timer updates, all downstream hydrologic modeling, inundation mapping, impact assessment, and alerting react dynamically to validated operational events published across an immutable, versioned event bus.

---

## 2. End-to-End Operational Event Pipeline

```
┌────────────────────────────────────────┐
│     EXTERNAL TELEMETRY / SATELLITE     │ (IMD AWS, CWC WRIS, IMERG, GloFAS)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│    INGESTION, VALIDATION & QC GATE     │ (Range checks, checksums, schema)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│    EVENT: SOURCE_DATA_RECEIVED         │ (Logged in EventStore with SHA256)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│   COALESCED FORECAST TRIGGER ENGINE    │ (Debounce window: 2s, min interval: 5s)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│      ASYNC FORECAST JOB QUEUE          │ (Decoupled execution: QUEUED -> RUNNING)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│     SEQUENTIAL MODEL EXECUTION         │
│  • RAINFALL_FUSION_UPDATED             │ (Dynamic fusion)
│  • HYDROLOGY_UPDATED                   │ (XGBoost quantile streamflow)
│  • INUNDATION_UPDATED                  │ (2D hydrodynamic surrogate)
│  • IMPACT_UPDATED                      │ (Critical asset & population risk)
│  • ALERT_STATE_CHANGED                 │ (Safety-gated human review)
│  • FORECAST_COMPLETED                  │ (Causal chain finalized)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│   WEBSOCKET STREAMING BROADCASTER      │ (/ws/v1/live to browser clients)
└────────────────────────────────────────┘
```

---

## 3. Core Architectural Guarantees

1. **Strict Provenance & Causality**: Every event carries a `correlation_id` (tracing the root trigger) and a `causation_id` (linking the direct predecessor).
2. **Monotonic State Versioning**: Every mutation increments `state_version`, allowing clients to perform gap-recovery upon reconnecting.
3. **Priority Protection**: Under high volume, `CRITICAL` (Alerts) and `HIGH` (Forecasts) events are never dropped by backpressure controls.
