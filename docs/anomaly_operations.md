# JALDRISHTI AI — Hydrometeorological Anomaly Operations Runbook (Phase 13)

## 1. Purpose & Target Audience

This runbook guides Emergency Operations Center (DEOC / SEOC) duty officers, hydrologists, and meteorological analysts in monitoring, interpreting, and managing real-time hydrometeorological anomaly detections in JALDRISHTI AI.

---

## 2. Real-Time Anomaly Dashboard & States

The **Data Health & Anomaly Stream** view provides a consolidated feed of real-time multi-source telemetry screenings categorized into four operating states:

| Anomaly State | UI Badge Color | Interpretation | Recommended Operator Action |
|---|---|---|---|
| **NORMAL** | Emerald Green | Telemetry within expected physical bounds and baseline envelope. | Routine monitoring. Observation ingested into forecasting models at full weight. |
| **WATCH** | Amber Yellow | Elevated reading or corroborated meteorological extreme event. | Review spatial consistency map. If confirmed `VALID_EXTREME`, note event progression. Model weighting remains normal. |
| **ANOMALOUS** | Orange | Statistically significant departure from EWMA/robust bounds without physical bounds breach. | Inspect time series trend. Verify whether local micro-convection is occurring. |
| **LIKELY_SENSOR_ERROR** | Rose Red | Physical bounds violation, stuck flatline, or isolated spike without external corroboration. | Review evidence modal. Dispatch field inspection or contact AWS maintenance division. |

---

## 3. Investigating an Anomaly Event

When an anomaly notification or badge appears:
1. **Click the Anomaly Card** in the Data Health view to open the **Evidence & Spatial Corroboration Modal**.
2. **Review Evidence Fields**:
   - **Observed Value**: Raw numerical telemetry value.
   - **Baseline Median / MAD**: Historical climatological reference for current season.
   - **Triggered Layers**: `LEVEL_0_PHYSICAL_BOUNDS`, `LEVEL_1_TEMPORAL_JUMP`, `LEVEL_1_FROZEN_SENSOR`, `LEVEL_2_ROBUST_ZSCORE`, `LEVEL_3_EWMA_DEVIATION`.
   - **Spatial Agreement**: Agreement ratio with neighboring ground gauges, NASA GPM IMERG satellite rainfall, and NWP forecasts.
3. **Determine Event Authenticity**:
   - If `Classification == VALID_EXTREME`: **DO NOT DISMISS**. Legitimate cyclone or cloudburst activity is underway.
   - If `Classification == LIKELY_SENSOR_ERROR`: Verify sensor flatline count or unphysical range breach.

---

## 4. Controlled Developer Test Injections

For training, audit simulations, and frontend verification, operators and engineers can inject synthetic test anomalies using the dedicated harness:

```http
POST /api/v1/anomalies/inject-test
Content-Type: application/json

{
  "station_id": "IMD_AWS_BHUBANESWAR",
  "variable": "rainfall_1h_mm",
  "value": 245.0,
  "test_case_name": "SYNTHETIC_CLOUD_BURST_SPIKE"
}
```

> [!IMPORTANT]
> All injected test events are strictly tagged with data state `SYNTHETIC_TEST`. They will update the UI and stream via WebSocket for testing, but **never contaminate operational live historical baselines or trigger public alarms.**

---

## 5. API Reference

- `GET /api/v1/anomalies`: List recent anomalies with filters (`station`, `variable`, `state`, `source`, `since`, `limit`).
- `GET /api/v1/anomalies/summary`: Aggregate distribution by state, station, and classification.
- `GET /api/v1/anomalies/{anomaly_id}`: Retrieve full forensic evidence and spatial neighbor data.
- `POST /api/v1/anomalies/inject-test`: Trigger test injection.
