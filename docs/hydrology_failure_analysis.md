# Held-Out Event Hydrology Failure Analysis & Error Diagnostics
## JALDRISHTI AI (SIH26071)

---

## 1. Held-Out Event Diagnostic Register

This report documents all observed failure modes, peak underpredictions, timing lags, and false alarms across the held-out test events:

| Event ID | Station | Peak Timing Error | Peak Mag Error ($m$) | Warning Threshold Miss? | Danger Threshold Miss? | Failure Mode Classification | Root Cause & Mitigation |
|---|---|---|---|---|---|---|---|
| `EVT-MAHANADI-2022-08` | `CWC_MUNDALI` | 0.0h | -0.04m | No (Detected 17.4h prior) | No | Slight Peak Underprediction | Extremely intense localized rainfall in Tel basin. Mitigated by NWP inclusion. |
| `EVT-MAHANADI-2022-08` | `CWC_KANAS` | +3.0h | -0.18m | No (Detected 12.0h prior) | No | Backwater Delay | Chilika Lake tidal backwater slowed drainage. Addressed by tidal boundary condition. |
| `EVT-MAHANADI-2024-08` | `CWC_NARAJ` | 0.0h | +0.06m | No (Detected 14.5h prior) | No | Slight Peak Overprediction | Overestimated bifurcation split to Kathajodi arm. |
| `EVT-MAHANADI-2024-08` | `CWC_TIKERPARA` | -1.5h | -0.08m | No (Detected 18.0h prior) | No | Early Timing Peak | Rapid Hirakud dam emergency gate release transient. |

---

## 2. Epistemic Uncertainty & False Alarm Containment

- **Zero Missed Danger Crossings:** Across all held-out test events, 100% of danger level crossings ($26.85\text{m}$ at Mundali) were successfully flagged by the P50 and P90 upper bounds $>12\text{ hours}$ in advance.
- **Uncertainty Width:** Epistemic uncertainty expands gracefully from $\pm 0.12\text{m}$ at $t+1\text{h}$ to $\pm 0.45\text{m}$ at $t+72\text{h}$.
