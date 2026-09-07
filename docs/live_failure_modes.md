# Live Ingestion Failure Modes & Graceful Degradation
## JALDRISHTI AI (SIH26071)

---

## 1. Provider Outage Degradation Matrix

| Failure Scenario | Immediate Detection | System Reaction | Displayed Data State | Data Confidence |
|---|---|---|---|---|
| **IMERG Satellite Outage** | HTTP 503 / Timeout | Fusion engine drops IMERG weight, renormalizes AWS + INSAT | `DEGRADED` | `LOW` |
| **AWS Telemetry Outage** | Missing AWS updates (>1h) | Reverts to satellite QPE without gauge amplitude correction | `DEGRADED` | `DATA_DEGRADED` |
| **Complete Internet Loss** | Network unreachable | Offline fallback activated; last observations kept timestamped | `OFFLINE` | `DATA_DEGRADED` |
| **Radar Unavailable** | No polar volume feed | Radar layer marked `RADAR_UNAVAILABLE`; 0 fake images | `UNAVAILABLE` | Retains optical flow / NWP |
| **NWP Model Delay** | Stale NWP guidance (>6h) | Extends persistence / advection weighting in nowcast | `STALE` | `MEDIUM` |
