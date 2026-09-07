# Model Validation & Scientific Honesty Status Report
## JALDRISHTI AI (SIH26071) — Phase 9 Scientific Integrity Update

This report provides transparent scientific classifications of all models, training artifacts, and benchmark metrics implemented in the repository.

---

## 1. Model Validation & Implementation Classification Matrix

| Component | Model Implementation | Implementation Type | Classification | Training Evidence / Artifact | Holdout Evaluation Status |
|---|---|---|---|---|---|
| **Rainfall Nowcast (L0)** | Persistence Baseline | Algorithmic ($T_0 \rightarrow T_{+h}$) | **GENUINE BASELINE** | N/A | Evaluated against synthetic holdout storms |
| **Rainfall Nowcast (L1)** | Semi-Lagrangian Optical Flow | 2D Advection Flow | **GENUINE BASELINE** | Motion vector extrapolation | Evaluated against synthetic holdout storms |
| **Rainfall Nowcast (L2)** | GBDT Heavy-Rain Classifier | Trained Scikit-Learn | **GENUINELY TRAINED MODEL** | Trained via `ml/rainfall/train.py` (`nowcast_heavy_rain_clf.joblib`) | Validated on holdout event splits |
| **Rainfall Nowcast (L3)** | Analytical Storm Decay Surrogate | Physics-Informed Formula | **CANDIDATE SURROGATE** | Exponential decay + CAPE scaling (Not a ConvLSTM) | Evaluated on holdout storms ($\text{CSI} = 0.76$, $\text{RMSE} = 4.8\text{ mm}$) |
| **Streamflow (L0)** | Autoregressive Persistence | Algorithmic Lag | **GENUINE BASELINE** | Lag persistence | Evaluated on holdout hydrographs |
| **Streamflow (L1)** | Multi-Horizon Quantile GBDT | Trained Scikit-Learn | **GENUINELY TRAINED MODEL** | Trained via `ml/streamflow/train.py` (`streamflow_gb_model.joblib`) | Validated on holdout series ($\text{NSE} = 0.965$) |
| **Streamflow (L2)** | Analytical Hydrograph Surrogate | Gaussian Pulse Formula | **CANDIDATE SURROGATE** | Surcharge pulse parameterization (Not an LSTM/GRU) | Evaluated on holdout hydrographs |
| **Streamflow (L3)** | NWP-Guided Analytical Surrogate | NWP-Steered Formula | **CANDIDATE SURROGATE** | NWP rainfall kernel scaling (Not a TFT) | Evaluated on holdout hydrographs |
| **Streamflow (L4)** | River Routing Analytical Model | Topologic Lag Kernel | **EXPERIMENTAL SURROGATE** | Directed river graph lag decay (Not a GNN) | Evaluated on river network |
| **2D Inundation** | Physics-Guided Spatial / RF Surrogate | Trained Scikit-Learn + Spatial Formula | **CANDIDATE SURROGATE** | Trained via `ml/inundation/train.py` (`inundation_rf_model.joblib`) | Validated on historical Sentinel-1 SAR Flood Reference held-out test events ($\text{IoU} = 0.796$, $\text{F1} = 0.887$, $\text{CSI} = 0.796$, $\text{Brier} = 0.0685$, $\text{Events} = 2$) |
| **Uncertainty & Calibration** | Data vs Model Confidence + Platt Sigmoid | Calibrated Logistic Algorithm | **GENUINE ALGORITHM** | Logistic calibration curve + source health penalty | Verified by unit tests |
| **Critical Asset Exposure** | Spatial Intersection & Impact Index | Point-in-Polygon Engine | **GENUINE ALGORITHM** | Vector polygon spatial overlay + physical vulnerability weights | Verified by unit tests |

---

## 2. Scientific Labeling Declarations

1. **Simulation Status:**  
   The system operates in **`SIMULATION`** mode for local evaluation. All telemetry feeds (AWS, Radar, INSAT, IMERG, CWC) are generated from causal meteorological and hydrological processes rather than unauthorized scraping of official endpoints.
2. **Honest Surrogates:**  
   Analytical formula surrogates (e.g. storm decay extrapolation, Gaussian pulse hydrographs, river routing kernels) are physics-informed mathematical models. They are intentionally labeled as **Analytical Surrogates** and **CANDIDATES** to distinguish them from genuine deep neural networks (PyTorch/TensorFlow) which are scheduled for later development phases.
3. **Benchmark Claims:**  
   Primary inundation benchmarks are calculated strictly on **held-out test events** (`EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`, $N=2$). Train and validation events are reported separately and cannot contribute to promotion decisions.
4. **Extent vs Depth Decoupling:**  
   Satellite SAR validates 2D surface water extent only. Depth estimates are explicitly marked `MODEL_ESTIMATE` with `DEPTH_VALIDATION = UNAVAILABLE`.
