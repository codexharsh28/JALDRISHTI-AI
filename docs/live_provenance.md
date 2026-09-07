# End-to-End Live Provenance Tracing & Queryability
## JALDRISHTI AI (SIH26071)

---

## 1. Complete Ingestion-to-Alert Lineage

Every forecast produced by JALDRISHTI AI maintains an unbroken, queryable provenance chain:

```
ingestion_run_id (e.g. ING-IMD-20260827-01, ING-IMERG-20260827-01)
      ↓
source_snapshot (Raw observation matrices & checksums)
      ↓
deterministic_qc (Flags: GOOD, SUSPECT, BAD)
      ↓
multi_source_fusion (Calibrated weights & variance)
      ↓
feature_snapshot (Input tensor parameters)
      ↓
forecast_run_id (e.g. FR-LIVE-20260827-XXXXXX)
      ↓
model_version_registry (L0 Persistence, L1 Advection, L2 XGBoost, L3 ConvLSTM)
      ↓
hydrograph_forecast (Stage, Discharge, Peak Timing)
      ↓
inundation_surrogate (2D Depth Classes & Flood Polygons)
      ↓
impact_assessment (Exposed Population, Hospitals, Roads)
      ↓
alert_decision_engine (RED/ORANGE/YELLOW/GREEN + Officer Sign-off)
```

---

## 2. Querying Live Provenance

The complete graph can be queried via the backend API:

```http
GET /api/v1/live/provenance/{forecast_run_id}
```

Response contains all contributing `ingestion_run_id`s, source checksums, model checkpoints, and execution timestamps.
