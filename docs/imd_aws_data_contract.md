# IMD AWS Data Contract & Normalization Specification

## Normalized Schema Definition

Every raw IMD AWS record is parsed into the canonical `IMDAWSObservation` schema:

| Field Name | Type | Nullable | Source Field | Description |
|------------|------|----------|--------------|-------------|
| `observation_id` | `string` | No | Deterministic Hash | `OBS-{sha256(IMD_AWS_{call_sign}_{obs_time})[:16]}` |
| `call_sign` | `string` | No | `CALL_SIGN` | 5-digit WMO/IMD Station Identifier (e.g. `42971`) |
| `station_id` | `string` | No | Derived | Canonical ID format: `IMD_AWS_{call_sign}` |
| `station_name` | `string` | No | `STATION` | Official Station Name (e.g. `BHUBANESWAR`) |
| `district` | `string` | Yes | `DISTRICT` | Administrative District |
| `state` | `string` | Yes | `STATE` | State Name (`Odisha`) |
| `latitude` | `float` | No | `Latitude` | WGS84 Latitude Decimal Degrees |
| `longitude` | `float` | No | `Longitude` | WGS84 Longitude Decimal Degrees |
| `observation_time`| `datetime`| No | `DATE` + `TIME` | UTC timestamp of observation |
| `retrieved_at` | `datetime`| No | System Clock | UTC timestamp when ingested by JALDRISHTI |
| `air_temperature_c`| `float` | Yes | `CURR_TEMP` | Dry bulb air temperature (°C) |
| `dew_point_c` | `float` | Yes | `DEW_POINT_TEMP`| Dew point temperature (°C) |
| `relative_humidity_pct`| `float`| Yes| `RH` | Relative humidity (0 - 100%) |
| `pressure_hpa` | `float` | Yes | `MSLP` / `PRESSURE` | Mean sea level atmospheric pressure (hPa) |
| `wind_direction_deg` | `float` | Yes | `WIND_DIRECTION` | Wind vector bearing (0 - 360°) |
| `wind_speed_mps`| `float` | Yes | `WIND_SPEED` | Wind speed converted to m/s |
| `rainfall_mm` | `float` | Yes | `RAIN_1H` / `RF_1H` | Measured 1h rainfall accumulation (mm) |
| `quality_state`| `string` | No | Quality Control | `GOOD`, `SUSPECT`, `BAD`, `STALE`, `MISSING` |
| `data_state` | `string` | No | Lineage Tag | `OBSERVED_IMD_AWS` |
| `raw_payload_hash` | `string` | No | Cryptographic | SHA-256 hash of unparsed API response string |

---

## Absence vs. Zero Contract

In adherence to hydrological integrity standards:
- **`rainfall_mm = None`**: The station did not measure rainfall during this hour (e.g. standard temperature-only AWS). Displayed in UI as `N/A`.
- **`rainfall_mm = 0.0`**: The rain gauge explicitly reported a 0.0 mm dry period.
- **Never Synthesize**: Under no circumstances does the adapter map missing values to 0.0 mm.
