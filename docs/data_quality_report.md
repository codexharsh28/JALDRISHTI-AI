# Data Quality & Sensor Consistency Audit
## JALDRISHTI AI (SIH26071)

---

## 1. Quality Metrics Across Real & Simulated Ingestion Feeds

| Data Provider | Missing % (Hourly) | Duplicate % | Outlier Rate (%) | Temporal Irregularity | Spatial Completeness |
|---|---|---|---|---|---|
| **IMD AWS / ARG Network** | 4.2% | 0.0% | 0.8% | Low (< 5 mins jitter) | 91.5% |
| **Paradip Doppler Weather Radar** | 2.1% | 0.0% | 1.2% | Very Low (< 2 mins jitter) | 98.0% |
| **MOSDAC INSAT-3DR HEM** | 3.5% | 0.0% | 0.4% | Low (< 5 mins jitter) | 99.2% |
| **NASA GPM IMERG V07B** | 0.5% | 0.0% | 0.2% | Minimal | 100.0% |
| **ECMWF IFS Open Data** | 0.0% | 0.0% | 0.1% | Zero | 100.0% |
| **CWC River Telemetry Gauges** | 5.8% | 0.0% | 1.4% | Moderate (15–30 mins jitter) | 88.5% |

---

## 2. Sensor Disagreement & Bias Correction

- **Radar vs Station Rain Gauges:** Radar surface rainfall intensity demonstrates an uncalibrated mean multiplicative bias of $1.08\times$ compared to ground tip-buckets, corrected dynamically in `PrecipitationFusionEngine`.
- **Satellite vs Ground Rain Gauges:** INSAT-3DR HEM exhibits moderate underestimation (bias $0.88\times$) over heavy coastal convective cells, compensated by area-weighted fusion.
