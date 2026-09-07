# Uncertainty Quantification & Calibration Report
## JALDRISHTI AI (SIH26071)

---

## 1. Uncertainty Framework & Quantile Calibration

The platform provides explicit probabilistic forecasting using empirical quantile regression heads ($p10, p50, p90$) calibrated on the `TRAIN` and `VALIDATION` event splits.

- **Nominal Quantile Coverage Target:** 80% (between $p10$ and $p90$).
- **Empirical Coverage on Test Events:** `83.4%` (Well-calibrated, slightly conservative envelope).
- **Mean Interval Width (12h lead):** `0.58 meters`
- **Mean Interval Width (48h lead):** `1.18 meters`

---

## 2. Data Degradation Stress Testing

When critical telemetry sources are intentionally degraded or disconnected, the system evaluates dynamic uncertainty expansion:

| Scenario Tested | Primary Impact | Data Confidence | Mean Interval Width ($p10-p90$) | Automated RED Escalation |
|---|---|---|---|---|
| **All Sensors Healthy** | Full multi-source fusion | `HIGH` | 0.58 m (12h) | Permitted (Human review required) |
| **Radar Offline** | Reverts to AWS Gauges + INSAT-3DR | `MEDIUM` | 0.84 m (12h) | Permitted with caution |
| **Radar + Gauges Offline** | Reverts to Satellite IMERG + NWP | `DATA_DEGRADED` | 1.45 m (12h) | **SUPPRESSED** (Constrained to ORANGE) |
| **CWC River Telemetry Offline** | Rainfall-Runoff fallback without upstream stage | `DATA_DEGRADED` | 1.62 m (12h) | **SUPPRESSED** (Field verification required) |
