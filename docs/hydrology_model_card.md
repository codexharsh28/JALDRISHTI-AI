# Hydrology Model Card: Multi-Horizon Streamflow Intelligence
## JALDRISHTI AI (SIH26071)

---

## 1. Model Overview

- **Model Hierarchy:**
  - `STREAMFLOW_L0_PERSISTENCE` (Persistence Baseline)
  - `STREAMFLOW_L1_XGBOOST` (**Best Validated Model**)
  - `STREAMFLOW_L2_LSTM` (Sequence Candidate)
  - `STREAMFLOW_L3_TFT` (Temporal Attention Candidate)
  - `STREAMFLOW_L4_RIVER_GRAPH_GNN` (Topological Graph Candidate)
- **Target Basin:** Mahanadi River Basin & Delta (Odisha, India)
- **Verified Stations:** `CWC_MUNDALI`, `CWC_NARAJ`, `CWC_TIKERPARA`, `CWC_KHAIRMAL`, `CWC_KANAS`
- **Forecast Horizons:** $1\text{h}, 3\text{h}, 6\text{h}, 12\text{h}, 24\text{h}, 48\text{h}, 72\text{h}$
- **Target Outputs:** Stage ($m$), Discharge ($\text{m}^3/\text{s}$), Rate of Rise ($\text{m}/\text{hr}$), Warning/Danger Exceedance Probabilities, P10/P50/P90 Uncertainty Bounds.

---

## 2. Training & Split Policy

- **Partition Strategy:** Whole-event partitioning ([data/manifests/hydrology_split_manifest.yaml](file:///c:/Users/DevbratY/Desktop/JALDRISHTI%20AI/data/manifests/hydrology_split_manifest.yaml))
- **Train Events:** `EVT-MAHANADI-2020-08`, `EVT-MAHANADI-2023-07`
- **Validation Event:** `EVT-MAHANADI-2021-09`
- **Held-Out Test Events:** `EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`
- **Anti-Leakage Enforcement:** Automated verification in [tests/test_hydrology_leakage.py](file:///c:/Users/DevbratY/Desktop/JALDRISHTI%20AI/tests/test_hydrology_leakage.py).
