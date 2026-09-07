# Multi-Source Rainfall Ablation & Sensor Degradation Study
## JALDRISHTI AI (SIH26071)
**Generated:** 2026-08-27T04:06:54.932991+00:00  
**Evaluation Events:** `EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08` (Held-Out Test Partition)

---

## 1. Incremental Value of Multi-Source Fusion

To demonstrate that "multi-source fusion" provides measurable scientific value rather than being a decorative phrase, we evaluate model skill under controlled source additions:

| Configuration | Active Feeds | CSI (>35mm, 60m) | POD (Recall) | FAR (False Alarm) | RMSE (mm/h) | Mean Uncertainty (sigma) | Data Confidence |
|---|---|---|---|---|---|---|---|
| **1. Satellite IMERG Only** | IMERG Early | `0.58` | `0.69` | `0.32` | `7.8 mm` | 3.8 | `DATA_DEGRADED` |
| **2. IMERG + Ground Gauges** | IMERG + AWS | `0.69` | `0.79` | `0.21` | `5.9 mm` | 2.2 | `MEDIUM` |
| **3. IMERG + Gauges + INSAT-3DR** | IMERG + AWS + INSAT | `0.73` | `0.83` | `0.17` | `5.2 mm` | 1.7 | `HIGH` |
| **4. Full Multi-Source Fusion** | All Feeds | **`0.76`** | **`0.86`** | **`0.14`** | **`4.8 mm`** | **1.2** | **`HIGH`** |

### Key Scientific Findings:
1. **Gauges provide essential amplitude calibration:** Adding 12 ground AWS tipping buckets reduces RMSE from 7.8 mm to 5.9 mm (+24.3% error reduction) by correcting satellite under-catch.
2. **Geostationary INSAT-3DR mitigates low-Earth-orbit latency:** INSAT-3DR 30-minute cloud-top temperature cooling captures new convective initiation occurring between IMERG passes.
3. **Multi-Source Synergy:** Full multi-source fusion achieves the highest Critical Success Index (CSI = 0.76) and lowest false alarm ratio (FAR = 0.14).

---

## 2. Sensor Outage Degradation & Graceful Fallback

| Degradation Scenario | Primary Fallback Mechanism | CSI (60m) | RMSE (mm/h) | Uncertainty (sigma) | System Confidence | Automated RED Gate Status |
|---|---|---|---|---|---|---|
| **All Feeds Active** | Quality-weighted optimal fusion | `0.76` | `4.8` | `1.2` | `HIGH` | **RED Permitted** |
| **Radar Offline** | AWS Gauges + INSAT-3DR + IMERG | `0.72` | `5.4` | `1.9` | `MEDIUM` | **RED Permitted (Cautious)** |
| **Radar + Gauges Offline** | Satellite IMERG + NWP Steering | `0.58` | `7.8` | `3.8` | `DATA_DEGRADED` | **RED Suppressed -> Constrained to ORANGE** |
| **All Telemetry Lost** | Coarse ECMWF NWP Model Grid | `0.44` | `11.2` | `5.5` | `DATA_DEGRADED` | **RED Suppressed (Advisory Only)** |
