# JALDRISHTI AI — Multi-Source Dynamic Fusion Architecture (Phase 17)

## 1. Overview

Combines diverse hydrometeorological observations through dynamic reliability weighting.

---

## 2. Dynamic Variance & Penalty Formulation

The effective inverse-variance weight $W_i$ for sensor source $i$ is defined as:

$$W_i = \frac{1}{\sigma_{nominal, i}^2 + \lambda \cdot \Delta t_{latency, i} + \mu \cdot \mathbb{I}_{anomalous, i}}$$

Where:
- $\sigma_{nominal, i}^2$: Sensor nominal measurement error variance.
- $\lambda$: Latency degradation penalty coefficient.
- $\Delta t_{latency, i}$: Observation age in hours.
- $\mu$: Anomaly penalty surcharge.
- $\mathbb{I}_{anomalous, i}$: Binary indicator for flagged anomalies.

### Normalized Fused Estimate:
$$\hat{y} = \frac{\sum_{i=1}^N W_i y_i}{\sum_{i=1}^N W_i}$$

### Fused Uncertainty Standard Deviation:
$$\hat{\sigma} = \sqrt{\frac{1}{\sum_{i=1}^N W_i}}$$
