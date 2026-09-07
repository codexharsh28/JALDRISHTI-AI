# JALDRISHTI AI — Model Metric Contract & Evaluation Taxonomy

## Purpose

To ensure strict scientific integrity and eliminate metric contradictions across system views, this contract defines the exact dataset, partition, forecast horizon, units, and definitions for all published metrics in JALDRISHTI AI.

---

## 1. Metric Contract Table

| Model / Subsystem | Metric Name | Canonical Symbol | Valid Range | Benchmark Value | Dataset & Partition | Evaluation Horizon | Physical Meaning |
|---|---|---|---|---|---|---|---|
| **Rainfall Nowcaster** | Critical Success Index | **CSI** | [0, 1] | **0.68** | IMD/Radar Mahanadi Test (2020–2024) | +1h to +3h | Threat score: $\frac{\text{Hits}}{\text{Hits} + \text{Misses} + \text{False Alarms}}$ |
| **Rainfall Nowcaster** | Probability of Detection | **POD** | [0, 1] | **0.82** | IMD/Radar Mahanadi Test (2020–2024) | +1h to +3h | Hit rate: $\frac{\text{Hits}}{\text{Hits} + \text{Misses}}$ |
| **Rainfall Nowcaster** | False Alarm Ratio | **FAR** | [0, 1] | **0.18** | IMD/Radar Mahanadi Test (2020–2024) | +1h to +3h | False rate: $\frac{\text{False Alarms}}{\text{Hits} + \text{False Alarms}}$ |
| **Rainfall Nowcaster** | Root Mean Square Error | **RMSE** | $[0, \infty)$ | **3.42 mm/h** | 2.5 km Grid Test Partition | +1h Nowcast | Standard error of spatial precipitation rate |
| **Hydrological Model** | Nash-Sutcliffe Efficiency | **NSE** | $(-\infty, 1]$ | **0.88** | CWC Stage Records (Mundali/Naraj) | +6h Peak Stage | Normalized relative residual variance |
| **Hydrological Model** | Kling-Gupta Efficiency | **KGE** | $(-\infty, 1]$ | **0.86** | CWC Stage Records (Mundali/Naraj) | +6h Peak Stage | Decomposed correlation, variability, and bias |
| **Inundation Extent** | Intersection over Union | **IoU** | [0, 1] | **0.78** | Sentinel-1 SAR Overpasses (2022/2023) | Peak Inundation | Spatial overlap ratio against SAR water mask |
| **Inundation Extent** | F1 / Dice Score | **F1** | [0, 1] | **0.84** | Sentinel-1 SAR Overpasses (2022/2023) | Peak Inundation | Harmonic mean of extent Precision and Recall |
| **Probabilistic System**| Brier Calibration Score | **BS** | [0, 1] | **0.12** | Calibrated Alert Trigger Events | Threshold Crossings | Mean squared error of probabilistic forecasts |
| **Probabilistic System**| Expected Calibration Error| **ECE** | [0, 1] | **0.04** | Calibrated Probability Bins | Threshold Crossings | Weighted difference between confidence and accuracy |

---

## 2. Metric Consistency Rules

1. **Explicit Horizon & Partition Tagging**:
   - Any metric presented in the UI or documentation must explicitly state the forecast horizon (e.g. `+1h`, `+6h`, `+24h`) and evaluation dataset.

2. **No Conflation of Extent and Depth**:
   - SAR reference validation metrics (IoU, F1, CSI) apply strictly to **2D flood surface extent**. Vertical water column depth metrics are declared `UNAVAILABLE` pending direct bathymetric/sonar gauge networks.
