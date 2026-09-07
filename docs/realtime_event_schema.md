# JALDRISHTI AI — Operational Event Schema Specification

## 1. Schema Definition

All events emitted across the system adhere to the immutable `OperationalEvent` contract:

```json
{
  "event_id": "EVT-20260827120000-a1b2c3",
  "event_type": "HYDROLOGY_UPDATED",
  "event_version": "1.0.0",
  "created_at": "2026-08-27T12:00:00.123456Z",
  "occurred_at": "2026-08-27T11:58:30.000000Z",
  "source_id": "HYDRO_CWC_MUNDALI",
  "provider": "XGBoost Quantile Streamflow Model",
  "mode": "LIVE",
  "data_state": "LIVE",
  "correlation_id": "CORR-FR-LIVE-20260827120000-d4e5f6",
  "causation_id": "EVT-20260827115959-987654",
  "priority": "HIGH",
  "state_version": 1042,
  "station_id": "CWC_MUNDALI",
  "basin_id": "pilot-mahanadi-delta",
  "payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "data": {
    "predicted_stage_m": 26.85,
    "predicted_discharge_cumec": 18560.0,
    "input_hydrology_source": "OBSERVED_CWC"
  }
}
```

---

## 2. Event Types & Classification

| Event Type | Priority Tier | Emitted By | Description |
| :--- | :---: | :--- | :--- |
| `SOURCE_DATA_RECEIVED` | `NORMAL` | Ingestion Adapters | Raw telemetry received, validated, and normalized |
| `SOURCE_DATA_REJECTED` | `HIGH` | QC Engine | Malformed or out-of-range observation rejected |
| `SOURCE_HEALTH_CHANGED`| `HIGH` | Scheduler / QC | Provider status changed (e.g. HEALTHY $\rightarrow$ DEGRADED) |
| `RAINFALL_FUSION_UPDATED`| `NORMAL` | Fusion Engine | Multi-source fused precipitation grid updated |
| `FORECAST_TRIGGERED` | `HIGH` | Trigger Engine | Debounce window elapsed, new run enqueued |
| `FORECAST_STARTED` | `HIGH` | Job Queue | Worker dequeued forecast job and began model sequence |
| `HYDROLOGY_UPDATED` | `HIGH` | Streamflow Suite | Gauge stage & discharge forecast generated |
| `INUNDATION_UPDATED` | `HIGH` | Inundation Model | 2D hydraulic depth surfaces and extent calculated |
| `IMPACT_UPDATED` | `HIGH` | Impact Engine | Population and critical infrastructure risk evaluated |
| `HUMAN_REVIEW_REQUIRED`| `CRITICAL` | Alert Safety Gate | Critical RED alert condition detected; awaiting review |
| `ALERT_STATE_CHANGED` | `CRITICAL` | Alert Engine | Alert transitioned through lifecycle state machine |
| `FORECAST_COMPLETED` | `HIGH` | Forecast Runner | End-to-end forecasting pipeline successfully finalized |
