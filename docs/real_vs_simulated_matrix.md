# JALDRISHTI AI — Authoritative Real vs. Simulated Matrix

This matrix establishes the scientific truth-in-labeling taxonomy across all data layers, models, sensors, and communication channels in JALDRISHTI AI.

---

## Complete Data & Model Truth Matrix

| Subsystem / Layer | Operational Live State | Replay / Historical State | Simulation / Demo State | Unconfigured / Outage State | Scientific Labeling Rule |
|---|---|---|---|---|---|
| **IMD Automatic Weather Station** | `OBSERVED_IMD_AWS` (When IP whitelisted & HTTP 200) | `REAL_HISTORICAL` | `SIMULATION` | `NOT_CONFIGURED` / `ACCESS_DENIED` / `OFFLINE` | Missing rainfall is `None` (`N/A`), NEVER `0.0 mm`. Never claim Live when access is denied. |
| **CWC River Gauge Telemetry** | `OBSERVED_CWC` | `REAL_HISTORICAL` | `SIMULATION` | `DEGRADED` / `OFFLINE` | Real stage heights in meters against official warning/danger marks. |
| **GloFAS Hydrological Fallback**| `MODELED_GLOFAS` | `MODELED_HISTORICAL` | `SIMULATION` | `UNAVAILABLE` | Always labeled `MODELED_GLOFAS`. NEVER reported as observed telemetry. |
| **NASA GPM IMERG Early** | `OBSERVED_SATELLITE_NRT` | `REAL_HISTORICAL` | `SIMULATION` | `STALE` / `UNAVAILABLE` | Half-hourly 0.1° satellite precipitation product with ~4h latency. |
| **ISRO INSAT-3DR HEM QPE** | `OBSERVED_GEOSTATIONARY` | `REAL_HISTORICAL` | `SIMULATION` | `NOT_CONFIGURED` | Geostationary infrared precipitation estimate (HEM L2B). |
| **Paradip Doppler Radar (DWR)** | `OBSERVED_RADAR_PPI` | `REAL_HISTORICAL` | `SIMULATION` | `RADAR_UNAVAILABLE` | Max-Z polar volume reflectivity. Clearly marked `UNAVAILABLE` if feed is inactive. |
| **2.5 km Model Grid Rainfall** | `MODELED_FUSED_GRID` | `MODELED_HISTORICAL` | `SIMULATION` | `FALLBACK_SINGLE_SOURCE` | Computational model grid. NEVER referred to as native sensor resolution. |
| **ConvLSTM Rainfall Nowcaster** | `MODELED_CONVLSTM` | `MODELED_HISTORICAL` | `SIMULATION` | `SURROGATE_HIERARCHY` | Labeled `RAIN_L3_CONVLSTM` ONLY when authentic PyTorch inference executes. |
| **HAND Hydraulic Inundation** | `MODEL_ESTIMATE` | `MODEL_ESTIMATE` | `SIMULATION` | `UNAVAILABLE` | Depth labeled `MODEL_ESTIMATE`; depth validation declared `UNAVAILABLE`. |
| **Sentinel-1 SAR / Bhuvan Flood**| `OBSERVED_SAR_EXTENT` | `REAL_HISTORICAL_SAR` | `N/A` | `NO_OVERPASS` | Validates spatial *extent* only (IoU/CSI/F1). Never claimed to validate depth. |
| **WorldPop Population Exposure** | `ESTIMATED_POPULATION` | `ESTIMATED_POPULATION` | `SIMULATION` | `UNAVAILABLE` | Strictly labeled `ESTIMATED POPULATION EXPOSURE`. |
| **Risk Score & Causal Waterfall**| `COMPUTED_RISK_SCORE` | `COMPUTED_HISTORICAL` | `SIMULATION` | `ATTRIBUTION_UNAVAILABLE` | Attribution weights derived from actual mathematical sensitivity components. |
| **Early Warning Alerts** | `OPERATIONAL_ALERT` | `HISTORICAL_ALERT` | `SIMULATION` | `SUPPRESSED` | RED/CRITICAL alerts safety-gated by human review. |
| **SMS Notification Delivery** | `SMS_LIVE_MSG91` (DLT Verified) | `N/A` | `MOCK_SMS_SINK` | `PRODUCTION_SMS_NOT_CONFIGURED` | Automated tests and demos strictly use `MockSMSSink`. Never fabricate real SMS delivery. |
| **Web Push / In-App Delivery** | `PUSH_DELIVERED` / `IN_APP` | `N/A` | `SIMULATION` | `UNSUBSCRIBED` | Point-in-polygon geofenced delivery (IN_AREA vs OUTSIDE_AREA). |
