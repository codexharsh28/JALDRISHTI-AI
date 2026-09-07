# JALDRISHTI AI — Hydrometeorological Anomaly Detection Methodology (Phase 13)

## 1. Executive Overview

The JALDRISHTI AI Anomaly Detection Engine operates in real time across incoming hydrometeorological streams (rainfall, river stage, discharge, temperature, relative humidity, atmospheric pressure, wind speed, source latency, and missingness). 

The primary operational mandate is **to detect unusual rainfall, river, and sensor behavior in real time without mistaking legitimate extreme meteorological phenomena (such as tropical cyclones, depressions, and cloudbursts) for sensor hardware failure.**

---

## 2. 5-Layer Screening Architecture

```
Incoming Telemetry Observation
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 0: Physical Plausibility & Missingness Bounds         │
│ (Hard range clipping, NaN/dropout detection)                │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 1: Temporal Continuity & Sensor Freeze Detection      │
│ (1-hour jump rate limits, consecutive flatline checks)      │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 2: Robust Z-Score (Median Absolute Deviation)         │
│ (0.6745 * |x - Med| / MAD; outlier rejection)               │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 3: Online EWMA Dynamic Volatility Band                │
│ (Adaptive mean & variance tracking: μ ± 3.5σ)               │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 4: Rolling Percentile Baseline                        │
│ (Sensor-specific seasonal P10 - P90 envelope)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ SPATIAL CROSS-CORROBORATION GATEWAY                         │
│ - Gauge Consensus: Inverse Distance Weighting (IDW)         │
│ - Satellite QPE: NASA GPM IMERG Early / INSAT-3DR HEM       │
│ - Numerical Weather Prediction: ECMWF / NCMRWF IFS          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ CLASSIFICATION & SAFETY GATE                                │
│ • VALID_EXTREME       → Discounted score, WATCH/NORMAL state│
│ • LIKELY_SENSOR_ERROR → High score, provider flagged        │
│ • POSSIBLE_ANOMALY    → Moderate score, WATCH state         │
│ • INSUFFICIENT_CONTEXT→ Baseline fallback                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Mathematical Formulations

### Level 0: Hard Physical Limits
For each variable $v \in V$, observation $x_t$ must satisfy:
$$x_{min}(v) \le x_t \le x_{max}(v)$$

| Domain Variable | Physical Min | Physical Max | Unit |
|---|---|---|---|
| Rainfall ($1\text{h}$) | $0.0$ | $300.0$ | $\text{mm/hr}$ |
| Rainfall ($24\text{h}$) | $0.0$ | $1200.0$ | $\text{mm/day}$ |
| River Stage | $0.0$ | $60.0$ | $\text{m}$ |
| Discharge | $0.0$ | $80,000.0$ | $\text{m}^3/\text{s}$ |
| Temperature | $-5.0$ | $55.0$ | $^\circ\text{C}$ |
| Relative Humidity | $5.0$ | $100.0$ | $\%$ |
| Surface Pressure | $850.0$ | $1060.0$ | $\text{hPa}$ |
| Wind Speed | $0.0$ | $350.0$ | $\text{km/h}$ |
| Source Latency | $0.0$ | $1440.0$ | $\text{minutes}$ |
| Missingness Ratio | $0.0$ | $1.0$ | ratio |

### Level 1: Temporal Jump Rate & Flatline Freeze
1. **Jump Rate**:
   $$\Delta x_t = |x_t - x_{t-1}| \le \Delta x_{max}(v)$$
2. **Sensor Freeze / Flatline**:
   $$\sum_{k=0}^{K-1} \mathbb{I}(|x_{t-k} - x_{t-k-1}| < \epsilon) \ge K_{freeze} \quad (K_{freeze} = 5)$$

### Level 2: Robust Z-Score (MAD)
Because standard mean and standard deviation are heavily corrupted by extreme outliers, JALDRISHTI AI uses the Median Absolute Deviation (MAD):
$$\text{MAD} = \text{median}(|x_i - \text{median}(X)|)$$
$$Z_{robust} = 0.6745 \cdot \frac{|x_t - \text{median}(X)|}{\text{MAD}}$$
Threshold: $Z_{robust} > 4.5$ flags a candidate statistical outlier.

### Level 3: Online Exponentially Weighted Moving Average (EWMA)
Online updating without storing infinite history:
$$\mu_t = \mu_{t-1} + \alpha (x_t - \mu_{t-1})$$
$$\sigma_t^2 = (1 - \alpha)(\sigma_{t-1}^2 + \alpha (x_t - \mu_{t-1})^2)$$
$$\text{Volatility Band} = [\mu_t - 3.5 \sigma_t, \; \mu_t + 3.5 \sigma_t]$$

### Level 4: Sensor-Specific & Seasonal Baselines
Baselines are never computed globally across all sensors. Each station maintains distinct climatological priors indexed by season ($\text{MONSOON}$ vs $\text{NON\_MONSOON}$) and diurnal sinusoidal shifts for thermodynamic variables.

---

## 4. Spatial Consistency & Extreme Weather Corroboration

An extreme observation (e.g. $75\text{ mm/hr}$ rainfall) is cross-evaluated against 3 independent external signals:
1. **Neighboring Gauges** within $75\text{ km}$ via Inverse Distance Weighting:
   $$\bar{x}_{neighbor} = \frac{\sum_{i} w_i x_i}{\sum_i w_i}, \quad w_i = \frac{1}{\max(d_i, 1.0)}$$
2. **NASA GPM IMERG Early Satellite QPE** ($0.1^\circ$ half-hourly).
3. **NWP Atmospheric Forcing** (ECMWF / NCMRWF IFS).

### Classification Matrix
- **$\ge 40\%$ Agreement**: Classified as `VALID_EXTREME`. Anomaly score is discounted ($\le 0.40$), state set to `WATCH` or `NORMAL`. Sensor health is **not** penalized.
- **$0\%$ Agreement + High Surge**: Classified as `LIKELY_SENSOR_ERROR`. Anomaly score $\ge 0.85$.
- **Partial Agreement**: Classified as `POSSIBLE_ANOMALY`. Anomaly score $0.40 - 0.70$.

---

## 5. Alert Safety Invariant

**Under no circumstances will a sensor anomaly directly generate a RED emergency alert.**
- A degraded or failing sensor reduces Data Confidence to `DATA_DEGRADED`.
- In accordance with the Alert Safety Invariant, `DATA_DEGRADED` caps alert severity at `ORANGE` and mandates human-in-the-loop duty officer review.
