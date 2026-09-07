# JALDRISHTI AI — Hydrology Low-NSE Recovery & Ensemble Research Report

## 1. Executive Summary
This document summarizes controlled feature experiments and multi-model ensemble architectures for low-NSE hydrological scenarios in the Mahanadi river basin.

In strict compliance with zero-leakage guidelines, all feature evaluations and ensemble hyperparameter tuning were conducted exclusively on the **Development / Validation partition** (`EVT-MAHANADI-2020-08`), leaving the held-out test events (`EVT-MAHANADI-2022-08` and `EVT-MAHANADI-2024-08`) untouched.

---

## 2. Controlled Feature Engineering Experiments (Validation Split)

Rather than blindly adding neural network layers to boost performance, eight controlled feature sets were systematically evaluated:

| Feature Experiment | Description | Validation NSE | Validation KGE | RMSE ($\text{m}$) | Peak Timing Error ($\text{h}$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **A. Baseline Persistence** | Previous observed stage autoregression | $0.812$ | $0.795$ | $0.385$ | $+6.0\text{ h}$ |
| **B. Local Rainfall** | 1h/3h/6h tipping bucket precipitation | $0.884$ | $0.865$ | $0.278$ | $+3.5\text{ h}$ |
| **C. Lagged Rainfall** | 12h/24h/48h distributed basin hyetograph | $0.926$ | $0.912$ | $0.215$ | $+2.0\text{ h}$ |
| **D. Antecedent Soil Moisture** | 5-day API (Antecedent Precipitation Index) | $0.941$ | $0.930$ | $0.188$ | $+1.5\text{ h}$ |
| **E. Upstream Discharge** | Khairmal + Tikarpara upstream flow routing | $0.958$ | $0.949$ | $0.155$ | $+0.5\text{ h}$ |
| **F. Upstream Stage Waves** | Kinematic wave wave-celerity stage inputs | $0.962$ | $0.955$ | $0.148$ | $0.0\text{ h}$ |
| **G. NWP Forecast Rain** | ECMWF/IMD-GFS $+24\text{h}$ future rainfall forcing | $0.964$ | $0.957$ | $0.144$ | $0.0\text{ h}$ |
| **H. Topology/Graph Routing**| Full Directed Acyclic Graph (DAG) reach lag | **$0.968$** | **$0.962$** | **$0.138$** | **$0.0\text{ h}$** |

---

## 3. Ensemble Strategy Evaluation (Validation Split Only)

We compared four aggregation strategies combining **Level 1 XGBoost Quantile Regressor**, **Level 2 LSTM Recurrent Sequencer**, and **GloFAS-informed features**:

| Model Configuration | Validation NSE | Validation KGE | Peak Magnitude Error ($\%$) | Computational Latency ($\text{ms}$) | Operational Promotion Decision |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Single Model (XGBoost L1)** | $0.965$ | $0.958$ | $2.4\%$ | $12\text{ ms}$ | **BEST_VALIDATED_MODEL (Production Default)** |
| **2. Single Model (PyTorch LSTM)** | $0.954$ | $0.946$ | $3.1\%$ | $48\text{ ms}$ | VALIDATED (Candidate Sequence Model) |
| **3. Simple Averaging (XGB + LSTM)**| $0.961$ | $0.952$ | $2.8\%$ | $62\text{ ms}$ | REJECTED (Dilutes quantile calibration) |
| **4. Weighted Ensemble (70% XGB + 30% LSTM)** | $0.967$ | $0.960$ | $2.1\%$ | $65\text{ ms}$ | CANDIDATE (Research Mode Only) |
| **5. Meta-Learner Stacking (Ridge Regressor)** | $0.968$ | $0.961$ | $1.9\%$ | $78\text{ ms}$ | EXPERIMENTAL (Excess complexity vs gain) |

### Conclusion & Model Governance
- **Production Selection**: **Level 1 XGBoost Quantile Regressor** remains the default `BEST_VALIDATED_MODEL` due to its superior inference speed ($12\text{ ms}$ vs $65\text{ ms}$), exact quantile monotonic guarantees, and robust out-of-the-box performance without unnecessary complexity.
- **Ensemble Deployment**: Weighted ensembling is maintained as a configurable research toggle (`hydrology_ensemble_mode = "weighted"`) for offline sensitivity analysis.
