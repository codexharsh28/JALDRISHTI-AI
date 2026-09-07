# Model Card: JALDRISHTI AI Precipitation Nowcasting Suite
## Model IDs: `MOD-NOWCAST-L0-PERSISTENCE`, `MOD-NOWCAST-L1-ADVECTION`, `MOD-NOWCAST-L2-XGBOOST`, `MOD-NOWCAST-L3-CONVLSTM`

---

## 1. Intended Use
- **Primary Function:** High-frequency, multi-horizon (0–6 hours) precipitation forecasting and heavy-rain probability estimation.
- **Intended Users:** State Disaster Management Authorities (OSDMA), Central Water Commission engineers, and municipal emergency responders.
- **Out-of-Scope Uses:** Long-range sub-seasonal forecasting (> 7 days) or direct automated closure of major dam spillway gates without human officer review.

---

## 2. Training & Evaluation Data
- **Training Partition Events:** `EVT-MAHANADI-2020-08`, `EVT-MAHANADI-2023-07` (336 hours of storm sequence records).
- **Validation Split Event:** `EVT-MAHANADI-2021-09` (168 hours).
- **Held-Out Test Partition Events:** `EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08` (384 hours).
- **Inputs:** Recent precipitation sequences (1h, 3h, 6h, 24h), radar dBZ reflectivity, INSAT-3DR HEM rates, CAPE, and Total Precipitable Water (PWAT).

---

## 3. Verified Performance Across Model Hierarchy (60-min lead time)
| Model Level & Architecture | CSI (>35 mm/h) | POD (Recall) | FAR (False Alarm) | RMSE (mm/h) | Operational Status |
|---|---|---|---|---|---|
| **Level 0: Persistence** | `0.38` | `0.52` | `0.41` | `11.4` | Baseline |
| **Level 1: Optical Flow Advection** | `0.54` | `0.68` | `0.29` | `8.2` | Baseline |
| **Level 2: Gradient Boosted Trees (XGBoost)** | `0.72` | `0.82` | `0.18` | `5.1` | Validated Checkpoint |
| **Level 3: Deep Spatiotemporal ConvLSTM** | **`0.76`** | **`0.86`** | **`0.14`** | **`4.8`** | Deployed Prototype |

---

## 4. Known Limitations & Failure Modes
1. **Radar Archive Constraint:** Historical radar validation utilizes standardized event sequences due to non-public IMD multi-year polar volume archives (`RADAR_HISTORY_UNAVAILABLE`).
2. **Convective Initiation past +3 Hours:** New ephemeral cloudbursts initiating spontaneously after +3 hours have lower predictability ($\text{CSI} = 0.58$ at +3h; $\text{CSI} = 0.39$ at +6h).
