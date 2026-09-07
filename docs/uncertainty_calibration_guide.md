# JALDRISHTI AI — Uncertainty Calibration & Variance Decomposition Guide (Phase 18)

## 1. Uncertainty Philosophy

JALDRISHTI AI adheres to strict scientific honesty:
- **No false precision**: Weather systems and floodplains are fundamentally stochastic.
- **Explicit variance sources**: Aleatoric (atmospheric chaos) and Epistemic (sparse sensors / model uncertainty) are separately computed and displayed.

---

## 2. Variance Formulations

$$\text{Var}_{total}(t) = \text{Var}_{aleatoric}(t) + \text{Var}_{epistemic}(t)$$

- $\text{Var}_{aleatoric}(t) \propto t^{\gamma}$ ($\gamma \approx 1.15$ diffusion growth).
- $\text{Var}_{epistemic}(t) = \sigma_{prior}^2 \cdot K_{telemetry} \cdot (1 + \beta \sqrt{t})$.

Under degraded telemetry (`DATA_DEGRADED` / GloFAS fallback), $K_{telemetry}$ increases, widening the confidence envelope and appropriately reflecting higher epistemic uncertainty to emergency managers.
