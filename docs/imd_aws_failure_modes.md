# IMD AWS Failure Modes & Graceful Degradation Matrix

## Failure Matrix

| Failure Mode | HTTP / Code | JALDRISHTI System Response | Fallback Behavior |
|---|---|---|---|
| **Non-Whitelisted IP** | HTTP 401 / 403 | `SourceState.NOT_CONFIGURED` / `ACCESS_DENIED` | Fused rainfall switches to IMERG / GPM / NWP; Hydrology uses CWC telemetry. No fake data synthesized. |
| **Gateway Outage** | HTTP 500 / 502 / 503 | `SourceState.OFFLINE` | System retries with backoff (1s, 2s, 4s). If persistent, raises `IMD_AWS_INGESTION_FAILED` on Event Bus. |
| **Network Timeout** | Timeout > 10s | `SourceState.DEGRADED` | Ingestion cycle terminates cleanly without blocking other live threads. |
| **Malformed JSON** | JSONDecodeError | `SourceState.DEGRADED` | Error logged, raw byte payload preserved for debugging, 0 records accepted. |
| **Missing Rainfall Field** | Key Absent | `rainfall_mm = None` | Displayed as `N/A` in UI; other meteorological fields (temperature, humidity, pressure) preserved. |
| **Out-of-Range Sensor** | E.g. Temp > 60°C | `QualityFlag.SUSPECT` | Flagged in QC engine; excluded from critical hydrological models but retained in audit trail. |

---

## Zero-Fabrication Guarantee

Under no condition will JALDRISHTI AI fallback to random generation or synthetic mock observation when the IMD AWS API is unreachable. System health indicators will transparently reflect the degradation state across all UI consoles.
