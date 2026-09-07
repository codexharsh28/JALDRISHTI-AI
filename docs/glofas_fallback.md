# JALDRISHTI AI — Hydrology Fallback & GloFAS Integration Protocol

## 1. Executive Summary
This document establishes the scientific rationale, data provenance boundaries, coordinate grid matching, and uncertainty propagation protocols for the **GloFAS Modeled River Discharge Fallback Subsystem**.

When primary Central Water Commission (CWC) telemetry is delayed, rate-limited, or unavailable, JALDRISHTI AI autonomously fails over to the Global Flood Awareness System (GloFAS v4.0) operated by ECMWF and accessed via the Open-Meteo Flood API.

---

## 2. Strict Scientific Distinction: Observed CWC vs Modeled GloFAS

```
┌──────────────────────────────────────────────┬──────────────────────────────────────────────┐
│       PRIMARY: CWC OBSERVED TELEMETRY        │         FALLBACK: MODELED GLOFAS (ECMWF)     │
├──────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ • In-situ physical radar/float/acoustic gauge│ • 2D Gridded Hydrological Model (LISFLOOD)   │
│ • Point measurement at exact river cross-sec │ • 0.05° (~5 km) spatial resolution cell      │
│ • Ground truth hydrometric stage & rating Q  │ • Simulated discharge forced by IFS/ERA5 NWP │
│ • Labeled strictly as: OBSERVED_CWC          │ • Labeled strictly as: MODELED_GLOFAS        │
│ • Data Confidence: HIGH (Score: 0.95)        │ • Data Confidence: MEDIUM (Score: 0.75)      │
│ • Uncertainty: 1.0x (RULE_BASED_ADJUSTMENT)  │ • Uncertainty: 1.8x (RULE_BASED_ADJUSTMENT)  │
└──────────────────────────────────────────────┴──────────────────────────────────────────────┘
```

> [!CAUTION]
> **Scientific Integrity Mandate:**
> GloFAS river discharge represents a numerical model simulation. It must **NEVER** be relabeled as `OBSERVED`, `CENTRAL WATER COMMISSION (CWC)`, or `GROUND TRUTH`.
> Uncertainty multipliers (1.0x CWC, 1.8x GloFAS, 2.5x DEGRADED) are strictly categorized as `RULE_BASED_UNCERTAINTY_ADJUSTMENT` unless empirical calibration evidence exists.

---

## 3. Station-to-Grid Coordinate Matching & Routing Validation

For every CWC station mapped to GloFAS, the system persists:
`cwc_station_id`, `glofas_cell_id`, `station_lat`, `station_lon`, `glofas_lat`, `glofas_lon`, `station_to_cell_distance_km`.

| Hydrological Station (`cwc_station_id`) | GloFAS Cell ID (`glofas_cell_id`) | Station Lat/Lon | GloFAS Cell Lat/Lon | Catchment Area ($\text{km}^2$) | Matching Distance (`station_to_cell_distance_km`) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Mundali Barrage** (`CWC_MUNDALI`) | `GLOFAS_CELL_20.45_85.75` | $20.435^\circ, 85.752^\circ$ | $20.45^\circ, 85.75^\circ$ | $133,000\text{ km}^2$ | $1.7\text{ km}$ |
| **Naraj Weir** (`CWC_NARAJ`) | `GLOFAS_CELL_20.45_85.85` | $20.465^\circ, 85.860^\circ$ | $20.45^\circ, 85.85^\circ$ | $132,500\text{ km}^2$ | $1.9\text{ km}$ |
| **Tikarpara Gorge** (`CWC_TIKERPARA`) | `GLOFAS_CELL_20.6_85.35` | $20.580^\circ, 85.350^\circ$ | $20.60^\circ, 85.35^\circ$ | $124,450\text{ km}^2$ | $2.2\text{ km}$ |
| **Khairmal** (`CWC_KHAIRMAL`) | `GLOFAS_CELL_20.85_84.8` | $20.850^\circ, 84.800^\circ$ | $20.85^\circ, 84.80^\circ$ | $115,000\text{ km}^2$ | $0.0\text{ km}$ |
| **Kanas Bridge** (`CWC_KANAS`) | `GLOFAS_CELL_20.0_85.75` | $20.015^\circ, 85.745^\circ$ | $20.00^\circ, 85.75^\circ$ | $3,200\text{ km}^2$ | $1.8\text{ km}$ |

---

## 4. SAR Validation Tolerance & Inundation Precomputation

### A. Satellite SAR Validation Window
- **Primary Benchmark Window**: $\le 3.0\text{ hours}$ (`SAR_MAX_TEMPORAL_MISMATCH_HOURS = 3.0`). Only observations within this window are eligible for primary benchmark metrics (`PRIMARY_BENCHMARK_ELIGIBLE`).
- **Exploratory Window**: $3.0\text{h} - 6.0\text{h}$ (`EXPLORATORY_ONLY`). Excluded from primary benchmark claims.
- **Rejected Window**: $> 6.0\text{ hours}$ (`REJECTED_TEMPORAL_MISMATCH`).

### B. Inundation Precomputation Horizons
- **Performance-Optimized Precomputed Range**: $+1\text{h}, +3\text{h}, +6\text{h}, +12\text{h}, +24\text{h}$ across quantiles $P10, P50, P90$.
- **Extended Horizons (+48h, +72h)**: Explicitly flagged and returned as `NOT_PRECOMPUTED`.

---

## 4. Fallback Execution Chain & Uncertainty Widening

```
                ┌───────────────────────────────────┐
                │  CWC Ingestion Cycle (Every 15m)  │
                └─────────────────┬─────────────────┘
                                  │
                       Is Telemetry Fresh (<3h)
                       and Schema Valid?
                                  │
                    ┌─────────────┴─────────────┐
                   YES                          NO
                    │                           │
         ┌─────────────────────┐     ┌─────────────────────┐
         │ Source: OBSERVED_CWC│     │ Source: MODELED_GLOFAS│
         │ Quality: 0.95 (HIGH)│     │ Quality: 0.75 (MED) │
         │ Uncertainty: 1.0x   │     │ Uncertainty: 1.8x   │
         └──────────┬──────────┘     └──────────┬──────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │ Downstream ML Hydrology   │
                    │ Inundation & Alert Engine │
                    └───────────────────────────┘
```

### Scientific Uncertainty Response
When GloFAS is activated:
1. **Uncertainty Bounds ($P10 - P90$) Expand**: Hydrological stage quantiles widen by a factor of $1.8\times$, reflecting gridded routing variance.
2. **Alert Gating Restrictions**: Automated alerts generated under `MODELED_GLOFAS` require operator confirmation if severity $\ge \text{DANGER}$.
3. **Data Provenance Flag**: Every output record records `input_hydrology_source: MODELED_GLOFAS`.
