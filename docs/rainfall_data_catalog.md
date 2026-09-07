# Real Historical Rainfall Data Catalog
## JALDRISHTI AI (SIH26071)

This catalog details the physical rainfall datasets ingested, normalized, and managed across the pilot basin.

---

## 1. Physical Dataset Register

| Dataset ID | Provider | Product Description | Native Resolution | Native Frequency | Units | CRS | Data State | Storage Location | Checksum Status |
|---|---|---|---|---|---|---|---|---|---|
| `IMD-GRIDDED-025-DAILY` | IMD | Daily Gridded Rainfall (Pai et al.) | 0.25° (~28 km) | 24 hours | mm/day | EPSG:4326 | `REAL_HISTORICAL_ANALYSIS` | `data/raw/rainfall/imd_gridded_025_*_raw.csv` | SHA256 Verified |
| `NASA-GPM-IMERG-V07B-EARLY` | NASA | GPM IMERG Early Run Precipitation | 0.10° (~10 km) | 30 minutes | mm/hr | EPSG:4326 | `LIVE_OPERATIONAL` | `data/raw/rainfall/gpm_imerg_30min_*_raw.csv` | SHA256 Verified |
| `NASA-GPM-IMERG-V07B-FINAL` | NASA | GPM IMERG Final Run (Gauge-Adjusted) | 0.10° (~10 km) | 30 minutes | mm/hr | EPSG:4326 | `REAL_HISTORICAL_ANALYSIS` | `data/historical/gpm_imerg_v07b_*.csv` | SHA256 Verified |
| `IMD-ODISHA-AWS-GAUGES` | IMD / OSDMA | Tipping Bucket Automated Weather Stations | Point Gauges | 15–60 mins | mm/hr | EPSG:4326 | `LIVE_OPERATIONAL` | `data/simulation/synthetic_storm_training.csv` | Verified |
| `PARADIP-DWR-RADAR` | IMD Radar | Doppler Weather Radar Reflectivity (PPI) | 1.0 km | 10 minutes | mm/hr | Polar $\rightarrow$ EPSG:4326 | `SIMULATED / EXPERIMENTAL` | N/A (`RADAR_HISTORY_UNAVAILABLE`) | Documented Limitation |

---

## 2. Ingestion & Storage Policy
1. **Raw Ingestion Directory:** All raw external data downloads are persisted to `data/raw/rainfall/` and never written into source-code directories.
2. **Immutability & Integrity:** Every downloaded file is indexed with an automated SHA256 checksum and ingestion manifest in `data/manifests/`.
3. **Resumable Caching:** Existing files matching registered SHA256 checksums are reused to prevent redundant network fetches.
