# JALDRISHTI AI — Probabilistic Forecasting Methodology (Phase 18)

## 1. Overview

Phase 18 implements genuine probabilistic forecasting across JALDRISHTI AI:
- **Precipitation Ensemble**: 20 stochastic perturbation members simulating convective advection velocity, cell growth/decay, and turbulence.
- **Streamflow Conformal Quantiles**: Non-crossing 7-quantile fan distributions ($p_{05}, p_{10}, p_{25}, p_{50}, p_{75}, p_{90}, p_{95}$) with empirical split-conformal calibration.
- **Hydraulic Inundation Exceedance**: Continuous probability surfaces for depth exceedance ($P(h > 0.5\text{m}), P(h > 1.0\text{m}), P(h > 2.0\text{m})$).
- **Uncertainty Decomposition**: Explicit attribution into Aleatoric vs Epistemic predictive variance.

---

## 2. Mathematical Formulations

### Quantile Monotonicity
$$\forall t \in \text{Horizons}: p_{05}(t) \le p_{10}(t) \le p_{25}(t) \le p_{50}(t) \le p_{75}(t) \le p_{90}(t) \le p_{95}(t)$$

### Split-Conformal Calibration
$$C_{1-\alpha}(X_{n+1}) = [\hat{q}_{\alpha/2}(X_{n+1}) - \hat{s}_{1-\alpha/2}, \; \hat{q}_{1-\alpha/2}(X_{n+1}) + \hat{s}_{1-\alpha/2}]$$
Where $\hat{s}$ is the $\lceil (n+1)(1-\alpha) \rceil / n$ empirical quantile of calibration residuals.

### Continuous Ranked Probability Score (CRPS)
$$\text{CRPS}(F, y) = \int_{-\infty}^\infty (F(x) - \mathbb{I}(x \ge y))^2 \, dx$$
