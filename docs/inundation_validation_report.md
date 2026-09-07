# 2D Inundation Extent & Sentinel-1 SAR Flood Reference Report
## JALDRISHTI AI (SIH26071) — Phase 8 Scientific Validation (Partition-Corrected)

---

## 1. Executive Summary

This report evaluates 2D hydrodynamic surrogate flood extent predictions against historical **Copernicus Sentinel-1 Synthetic Aperture Radar (SAR) Flood Reference** masks over the Mahanadi Delta floodplains.

> [!IMPORTANT]
> **PRIMARY BENCHMARK PARTITION INTEGRITY RULE:**  
> 1. **Pure Held-Out Testing:** The primary scientific benchmark is calculated **EXCLUSIVELY** from untouched `HELD_OUT_TEST` events (`EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`).
> 2. **Explicit Partition Separation:** `TRAIN` and `VALIDATION` events are evaluated and reported separately as development/tuning evidence and are **STRICTLY EXCLUDED** from primary benchmark means, model promotion decisions, and held-out validation claims.
> 3. **Sample Size & Generalization Transparency:** **`HELD_OUT_TEST EVENTS = 2`**. Do not imply broad generalization from only two held-out events. Wider regional validation across additional catchments is required before operational deployment.
> 4. **Extent vs Depth Decoupling:** Satellite SAR only validates 2D surface water extent. Depth is classified **`MODEL_ESTIMATE`** with **`DEPTH_VALIDATION = UNAVAILABLE`**.

---

## 2. Primary Benchmark: Held-Out Test Performance

*Evaluated strictly on held-out test events that were never exposed during model training or hyperparameter tuning:*

**HELD_OUT_TEST EVENTS = 2**

| Event ID | Partition | Forecast Valid Time | SAR Acquisition Time | Time Diff ($\Delta t$) | Match Status | Observed Extent ($\text{km}^2$) | Predicted Extent ($\text{km}^2$) | Extent IoU | F1-Score | CSI | Precision | Recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `EVT-MAHANADI-2022-08` | `HELD_OUT_TEST` | 2022-08-17 18:00Z | 2022-08-17 18:04Z | $0.07\text{ h}$ | `MATCHED` | 184.6 | 191.2 | 0.792 | 0.884 | 0.792 | 0.869 | 0.900 |
| `EVT-MAHANADI-2024-08` | `HELD_OUT_TEST` | 2024-08-05 06:00Z | 2024-08-05 06:15Z | $0.25\text{ h}$ | `MATCHED` | 112.0 | 114.8 | 0.800 | 0.889 | 0.800 | 0.878 | 0.900 |
| **Primary Held-Out Mean** | — | — | — | — | — | — | — | **0.796** | **0.887** | **0.796** | **0.873** | **0.900** |

*Probabilistic Calibration on Held-Out Test Distribution:*
- **Expected Calibration Error (ECE):** $0.0435$
- **Brier Score:** $0.0685$

---

## 3. Development & Validation Performance (Reported Separately)

*These events were used during model development and hyperparameter tuning; they are excluded from the primary validation benchmark above:*

### A. Training / Development Performance
| Event ID | Partition | Forecast Valid Time | SAR Acquisition Time | Time Diff ($\Delta t$) | Observed Extent ($\text{km}^2$) | Predicted Extent ($\text{km}^2$) | IoU | F1-Score |
|---|---|---|---|---|---|---|---|---|
| `EVT-MAHANADI-2020-08` | `TRAIN` | 2020-08-29 06:00Z | 2020-08-29 06:12Z | $0.20\text{ h}$ | 215.4 | 219.2 | 0.805 | 0.892 |

### B. Validation / Tuning Performance
| Event ID | Partition | Forecast Valid Time | SAR Acquisition Time | Time Diff ($\Delta t$) | Observed Extent ($\text{km}^2$) | Predicted Extent ($\text{km}^2$) | IoU | F1-Score |
|---|---|---|---|---|---|---|---|---|
| `EVT-MAHANADI-2021-09` | `VALIDATION` | 2021-09-28 18:00Z | 2021-09-28 17:45Z | $0.25\text{ h}$ | 98.2 | 99.0 | 0.812 | 0.896 |

---

## 4. Multi-Model Benchmark Comparison (Held-Out Test Set Only)

| Model Architecture | Model Status | Held-Out Test IoU | Held-Out Test F1 | Held-Out Test CSI | Precision | Recall |
|---|---|---|---|---|---|---|
| **Terrain Threshold Baseline** | `BASELINE` | 0.800 | 0.889 | 0.800 | 0.883 | 0.894 |
| **Physics-Informed Planar Baseline** | `BASELINE` | 0.795 | 0.886 | 0.795 | 0.871 | 0.900 |
| **Random Forest Surrogate** | `CANDIDATE` | 0.796 | 0.886 | 0.796 | 0.872 | 0.900 |
| **Analytical Spatial Surrogate** | `CANDIDATE` | **0.796** | **0.887** | **0.796** | **0.873** | **0.900** |

---

## 5. Depth Estimation Declaration

| Depth Category | Estimated Inundated Area ($\text{km}^2$) | Depth Status | Gauge Validation Status |
|---|---|---|---|
| **Class 1 (0.0 – 0.3m)** | $42.5\text{ km}^2$ | `MODEL_ESTIMATE` | `UNAVAILABLE` |
| **Class 2 (0.3 – 1.0m)** | $68.4\text{ km}^2$ | `MODEL_ESTIMATE` | `UNAVAILABLE` |
| **Class 3 (1.0 – 2.0m)** | $74.2\text{ km}^2$ | `MODEL_ESTIMATE` | `UNAVAILABLE` |
| **Class 4 (> 2.0m)** | $30.3\text{ km}^2$ | `MODEL_ESTIMATE` | `UNAVAILABLE` |

*Note: In the absence of high-density automated river floodplain depth sensors, depth values are generated as hydrodynamic model estimates based on stage surcharge and HAND mass conservation, and must not be presented as empirically validated gauge measurements.*
