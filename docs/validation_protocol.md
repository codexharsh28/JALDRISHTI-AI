# Scientific Validation Protocol & Event-Based Partitioning
## JALDRISHTI AI (SIH26071)

---

## 1. The Anti-Autocorrelation Principle

> **CRITICAL SCIENTIFIC PRINCIPLE:**  
> **Hydrometeorological time-series exhibit strong temporal autocorrelation.**  
> Randomly shuffling hourly or 15-minute observations into standard $k$-fold cross-validation results in severe data leakage, artificially inflating skill metrics ($\text{NSE} > 0.98$, $\text{CSI} > 0.95$).

To ensure rigorous, scientifically defensible evaluation, **all historical datasets are partitioned at the whole-event level**. No timesteps from an event in the test partition are ever included in model training or hyperparameter calibration.

---

## 2. Event Partitioning Scheme

| Event ID | Flood Event Name | Monsoon Season | Partition | Purpose |
|---|---|---|---|---|
| `EVT-MAHANADI-2020-08` | August 2020 Deep Depression Flood | 2020 | **TRAIN** | Model training and loss optimization |
| `EVT-MAHANADI-2023-07` | July 2023 Upper Catchment Inflow Wave | 2023 | **TRAIN** | Baseline and threshold tuning |
| `EVT-MAHANADI-2021-09` | September 2021 Cyclone Gulab Remnant | 2021 | **VALIDATION** | Hyperparameter selection, quantile calibration, early stopping |
| `EVT-MAHANADI-2022-08` | August 2022 Back-to-Back Depressions | 2022 | **HELD_OUT_TEST** | Final independent benchmark reporting |
| `EVT-MAHANADI-2024-08` | August 2024 Active Monsoon Surge | 2024 | **HELD_OUT_TEST** | Final independent benchmark reporting |

---

## 3. Information Cutoff & Anti-Leakage Rules

For any hindcast simulation executed at forecast issuance time $T$:
1. **Operational Availability Gating:** An observation $O$ with timestamp $t_{\text{obs}}$ is permitted into the feature matrix **if and only if** its operational publication time $t_{\text{pub}} \le T$.
2. **No Lookahead Normalization:** Normalization scalers (min/max, mean/std) must be fitted strictly on the `TRAIN` events partition, never on the combined dataset.
3. **Threshold Calibration Isolation:** Warning and danger flood probability triggers are tuned strictly on `TRAIN` and `VALIDATION` events, never on `HELD_OUT_TEST`.
