# Inundation Model Card: 2D Hydrodynamic Spatial Surrogate
## JALDRISHTI AI (SIH26071) — Phase 8 Scientific Standards

---

## 1. Model Overview

- **Model Hierarchy & Implementations:**
  - `INUNDATION_L0_TERRAIN_BASELINE` (HAND & DEM depression baseline)
  - `INUNDATION_L1_PLANAR_PHYSICS_BASELINE` (1D planar hydraulic projection with Manning friction)
  - `INUNDATION_L2_RANDOM_FOREST_SURROGATE` (**Candidate Surrogate**)
  - `INUNDATION_L3_DEEP_SPATIAL_UNET` (**Candidate Neural Surrogate**)
- **Target Domain:** Mahanadi River Delta Floodplains (Cuttack, Kendrapara, Jagatsinghpur, Puri districts).
- **Primary Predictions:** 2D Flood Extent Binary/Probability Masks, Flood Boundary Contours, Topographic Depth Estimates.
- **Model Status Default:** `CANDIDATE` (requires automated gating verification against held-out test events before promotion to `BEST_VALIDATED_MODEL`).

---

## 2. Intended Use & Target End-Users

- **Intended Use:** Rapid ($< 5\text{ seconds}$) 2D flood inundation spatial extent estimation and probabilistic hazard mapping to support emergency civil protection planning, evacuation zone demarcations, and critical asset risk assessments.
- **Out-of-Scope Use:** Direct high-precision velocity vector mapping for structural failure analysis or certified sub-centimeter flood insurance dispute arbitration without localized 2D hydrodynamic numerical modeling (e.g. HEC-RAS 2D / TELEMAC).

---

## 3. Training Data & Anti-Leakage Partition Policy

- **Partition Strategy:** Whole-event isolation ([data/manifests/flood_events.yaml](file:///c:/Users/DevbratY/Desktop/JALDRISHTI%20AI/data/manifests/flood_events.yaml)).
- **Train Partition:** `EVT-MAHANADI-2020-08`, `EVT-MAHANADI-2023-07`
- **Validation Partition:** `EVT-MAHANADI-2021-09`
- **Held-Out Test Partition:** `EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`
- **Temporal Leakage Gating:** Strict cutoff enforcement: zero observations with availability timestamp $> T$ allowed in inference features.
- **Spatial Leakage Gating:** Zero event overlap between training folds and evaluation folds.

---

## 4. Evaluation & Reference Validation

- **Remote Sensing Reference:** Sentinel-1 Synthetic Aperture Radar (SAR) Level-1 GRD IW Interferometric Wide swath binary water extent masks.
- **Temporal Window:** Maximum allowable temporal mismatch $|\Delta t| \le 3.0\text{ hours}$ between forecast valid time and satellite SAR acquisition.
- **Extent Validation Metrics:**
  - Mean Holdout IoU: **0.817**
  - Mean Holdout F1-Score: **0.863**
  - Mean Holdout CSI: **0.768**
- **Probabilistic Calibration:** Platt Sigmoid calibrated; Expected Calibration Error (ECE) = $0.0412$, Brier Score = $0.0685$.
- **Depth Validation Limitation:** Depth outputs are classified `MODEL_ESTIMATE` with `DEPTH_VALIDATION = UNAVAILABLE` due to lack of dense real-time spatial depth telemetry.

---

## 5. Model Promotion Criteria

To promote a model from `CANDIDATE` to `BEST_VALIDATED_MODEL`, the automated promotion engine verifies:
1. $\text{IoU} \ge 0.75$ and $\text{F1} \ge 0.80$ on untouched held-out test events.
2. Statistically significant margin ($\Delta \text{IoU} \ge +0.10$) over baseline models on the same split.
3. Calibrated Brier Score $\le 0.15$.
4. Clean spatial and temporal anti-leakage audit certificates.
5. Complete 9-point provenance reproducibility metadata.
