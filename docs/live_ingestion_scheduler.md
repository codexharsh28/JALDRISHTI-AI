# Live Ingestion Scheduler & Provider Cadence Specification
## JALDRISHTI AI (SIH26071)

---

## 1. Provider Ingestion Modes & Cadence Matrix

The live scheduler enforces provider-specific ingestion mechanisms and cadences. Providers are never polled faster than their configured minimum intervals.

| Provider ID | Ingestion Mode | Refresh Cadence | Min Interval | Timeout | Retry Policy | Fallback Behavior |
|---|---|---|---|---|---|---|
| `IMD_ODISHA_AWS` | `POLL` | 900s (15m) | 300s (5m) | 8.0s | Exponential ($3\times$, $1.5\times$) | Use last valid AWS observation; lower confidence |
| `NASA_GPM_IMERG_EARLY` | `SCHEDULED` | 1800s (30m) | 900s (15m) | 15.0s | Exponential ($3\times$, $2.0\times$) | Recalculate fusion weights without IMERG Early |
| `ISRO_MOSDAC_INSAT3DR` | `POLL` | 1800s (30m) | 900s (15m) | 10.0s | Exponential ($2\times$, $1.5\times$) | Mark `NOT_CONFIGURED` if credentials absent |
| `ECMWF_OPEN_DATA_NWP` | `SCHEDULED` | 10800s (3h) | 3600s (1h) | 20.0s | Exponential ($3\times$, $2.0\times$) | Retain previous valid NWP cycle forecast |
| `CWC_WRIS_TELEMETRY` | `POLL` | 3600s (1h) | 1800s (30m) | 10.0s | Exponential ($3\times$, $1.5\times$) | Retain last river stage height; flag sensor |
| `IMD_DWR_PARADIP` | `POLL` | 600s (10m) | 300s (5m) | 8.0s | Exponential ($2\times$, $1.5\times$) | Explicitly `UNAVAILABLE` (`RADAR_HISTORY_UNAVAILABLE`) |
| `MOCK_LIVE_SIMULATOR` | `MANUAL` | 60s | 10s | 2.0s | Direct | **Opt-in only** (`ENABLE_MOCK_LIVE=true`) |

---

## 2. Raw Live Cache Storage

Every live ingestion attempt persists an immutable raw payload record in `data/raw/live/{ingestion_run_id}.json` containing:
- `ingestion_run_id`: Unique trace identifier (e.g. `ING-IMD-20260827-XXXXXX`)
- `source_id` & `provider`
- `started_at` & `completed_at` timestamps
- `latency_ms`
- `payload_hash`: SHA256 integrity checksum
- `raw_payload`: Unmodified response content
