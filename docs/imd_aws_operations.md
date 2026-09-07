# IMD AWS Operational Runbook & Telemetry Monitoring

## Telemetry Health States

JALDRISHTI AI classifies the IMD AWS telemetry feed into 5 deterministic operational states:

1. **`LIVE_OBSERVED`**:
   - HTTP 200 responses received from `https://city.imd.gov.in/api/aws_data_api.php`.
   - Telemetry age is $\le 60$ minutes.
   - Genuine observation data parsed, QC-screened, and persisted.

2. **`NOT_CONFIGURED`**:
   - The deployment node's IP is not yet whitelisted on the IMD gateway (HTTP 401 / 403).
   - No mock data is presented; source state clearly tagged as `NOT_CONFIGURED`.

3. **`AGING`**:
   - Observations received, but timestamp age is between $60$ and $180$ minutes.

4. **`STALE`**:
   - Observation age exceeds $180$ minutes (3 hours).

5. **`OFFLINE`**:
   - Gateway returns HTTP 5xx errors or network timeout occurs after retries.

---

## Polling Cadence & Rate Limiting

- **Standard Cadence**: Polls every 15 minutes (aligned with IMD AWS batch processing cycles).
- **Minimum Cooldown**: 5 seconds between consecutive HTTP requests.
- **Backoff Strategy**: Exponential backoff upon encountering HTTP 429 or network dropouts.

---

## Operations API Endpoints

### 1. Status Diagnostics
```http
GET /api/v1/live/imd-aws/status
```
Returns real-time gateway status, latency, station count, and last observation timestamp.

### 2. Station Catalog
```http
GET /api/v1/live/imd-aws/stations?inside_basin_only=true
```
Returns discovered stations filtered by Mahanadi basin containment.

### 3. On-Demand Ingestion Refresh
```http
POST /api/v1/live/imd-aws/refresh?force=true
```
Triggers an immediate ingestion poll, bypassing the standard 15-minute scheduler wait.
