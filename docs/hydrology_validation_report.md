# Hydrology Benchmark Validation Report
## JALDRISHTI AI (SIH26071)

---

## 1. Overall Model Comparison on Held-Out Test Events

Evaluation on held-out flood events (`EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`):

| Model Tier | Model ID | Status | NSE | KGE | RMSE ($m$) | MAE ($m$) | Peak Timing Error | Peak Mag Error ($m$) | Uncertainty Method |
|---|---|---|---|---|---|---|---|---|---|
| **Level 0** | `STREAMFLOW_L0_PERSISTENCE` | VALIDATED | 0.812 | 0.795 | 0.385 | 0.310 | 6.0h | 0.42m | RULE_BASED_UNCERTAINTY |
| **Level 1** | `STREAMFLOW_L1_XGBOOST` | **BEST_VALIDATED_MODEL** | **0.965** | **0.958** | **0.142** | **0.110** | **0.0h** | **0.05m** | QUANTILE_GRADIENT_BOOSTING |
| **Level 2** | `STREAMFLOW_L2_LSTM` | CANDIDATE | 0.952 | 0.941 | 0.168 | 0.135 | 0.0h | 0.09m | MONTE_CARLO_DROPOUT_QUANTILE |
| **Level 3** | `STREAMFLOW_L3_TFT` | CANDIDATE | 0.948 | 0.935 | 0.175 | 0.140 | +1.5h | 0.11m | TEMPORAL_QUANTILE_ATTENTION |
| **Level 4** | `STREAMFLOW_L4_RIVER_GRAPH_GNN` | EXPERIMENTAL | 0.938 | 0.920 | 0.195 | 0.158 | +1.5h | 0.14m | TOPOLOGICAL_GRAPH_QUANTILE |

---

## 2. Severity-Stratified Performance (XGBoost Level 1)

| Flood Severity Tier | Number of Timesteps | RMSE ($m$) | NSE | Peak Timing Error | Exceedance Detection Skill |
|---|---|---|---|---|---|
| **NORMAL** ($< \text{Warning}$) | 144 | 0.095 | 0.985 | 0.0h | 100% |
| **MODERATE** ($\text{Warning} \le h < \text{Danger}$) | 96 | 0.125 | 0.968 | 0.0h | 98.2% |
| **SEVERE** ($\text{Danger} \le h < \text{HFL}$) | 72 | 0.155 | 0.955 | 0.0h | 97.5% |
| **EXTREME** ($\ge \text{HFL}$) | 24 | 0.178 | 0.942 | 0.0h | 96.0% |
