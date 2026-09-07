# JALDRISHTI AI — Live Risk Evolution & Causal Explainability Methodology (Phase 14)

## 1. Executive Overview

The JALDRISHTI AI Risk Engine calculates the live, composite basin risk state and quantifies **"Why did risk change?"** whenever new hydrometeorological observations, forecasts, or inundation surfaces arrive.

Risk calculation operates on actual backend outputs rather than duplicating forecast simulations, and maintains strict versioning, noise-suppression gating, and temporal causality.

---

## 2. Risk State Architecture & Levels

The normalized basin risk score ranges from $0.0$ to $100.0$:

| Risk Level | Score Range | Operational Meaning | Action Policy |
|---|---|---|---|
| **NORMAL** | $0.0 - 24.9$ | Standard monsoon baseflow / routine conditions. | Routine telemetry monitoring. |
| **WATCH** | $25.0 - 44.9$ | Moderate rainfall or elevated river levels. | Enhanced sensor polling; early warning watch. |
| **WARNING** | $45.0 - 64.9$ | High rainfall intensity and stage approaching danger mark. | Incident command activation; floodplain vigilance. |
| **ALERT** | $65.0 - 79.9$ | Imminent inundation across lowlands, critical infrastructure at risk. | Targeted evacuation advisory; sluice gate control. |
| **CRITICAL** | $80.0 - 100.0$ | Severe catastrophic flooding threatening human life & major assets. | Emergency evacuation; red alert gating applied. |

---

## 3. Risk Composition Formulation

Risk score $R_t \in [0, 100]$ is synthesized additively across 4 physical domain components plus data quality uncertainty:

$$R_t = \text{clamp}\Big(S_{met}(t) + S_{hydro}(t) + S_{inun}(t) + S_{exp}(t) + \delta_{conf}(t), \; 0, \; 100\Big)$$

### 1. Meteorological Component ($S_{met} \in [0, 25]$)
$$S_{met} = \min\left(15.0, \; \frac{I_{rain}}{65.0} \times 15.0\right) + \min\left(10.0, \; \frac{A_{24h}}{200.0} \times 10.0\right)$$

### 2. Hydrological Component ($S_{hydro} \in [0, 30]$)
$$S_{hydro} = \min\left(20.0, \; \frac{H_{stage} - 20.0}{H_{danger} - 20.0} \times 18.0\right) + \min\left(10.0, \; \frac{Q_{discharge}}{25,000.0} \times 10.0\right)$$

### 3. Inundation Extent Component ($S_{inun} \in [0, 25]$)
$$S_{inun} = \min(15.0, \; P_{flood} \times 15.0) + \min\left(10.0, \; \frac{\text{Area}_{sqkm}}{500.0} \times 10.0\right)$$

### 4. Exposure & Vulnerability Component ($S_{exp} \in [0, 20]$)
$$S_{exp} = \min\left(10.0, \; \frac{Pop_{exp}}{200,000} \times 10.0\right) + \min\left(10.0, \; \frac{Assets_{exp}}{40} \times 10.0\right)$$

### 5. Data Quality & Uncertainty Penalty ($\delta_{conf}$)
$$\delta_{conf} = \begin{cases} 4.0 & \text{if } \text{Confidence} = \text{DATA\_DEGRADED} \\ 2.0 & \text{if } \text{Confidence} = \text{LOW} \\ 0.0 & \text{if } \text{Confidence} = \text{HIGH} \end{cases}$$

---

## 4. Material Change Gating

To suppress numerical noise and telemetry jitter, updates are only marked as material if at least one threshold is breached:
- $\Delta R \ge 3.0\text{ pts}$
- $\Delta P_{flood} \ge 0.04$
- $\Delta \text{Area} \ge 5.0\text{ km}^2$
- $\Delta H_{stage} \ge 0.15\text{ m}$

---

## 5. Causal Explainability & "Why Did Risk Change?"

Every material change $\Delta R = R_t - R_{t-1}$ is decomposed additively into exact constituent factors:

$$\Delta R = \sum_{k} \Delta S_k$$

Each contributor provides:
1. `factor_name`: Human-readable identifier.
2. `delta_score`: Exact points added or subtracted.
3. `direction`: `INCREASING_RISK` or `DECREASING_RISK`.
4. `evidence_value`: Physical observation (e.g. $142.0\text{ mm/24h}$).
5. `explanation`: Plain-language explanation for operations commanders.
