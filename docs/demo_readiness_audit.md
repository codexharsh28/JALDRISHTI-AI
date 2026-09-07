# JALDRISHTI AI — Demo Readiness, End-to-End Scenario & Scientific Audit

## 1. Executive Audit Summary
This audit inspects the current repository state across Dashboard, Rainfall Nowcast, River Forecast, Inundation, Impact, Risk, Alerts, Public Portal, Event Bus, Simulation Engine, Model APIs, and Notification APIs to identify gaps preventing a cohesive, scientifically honest, judge-ready demonstration.

---

## 2. Comprehensive Findings & Classification

### A. Rainfall Nowcast Visualization Gaps
- **Current Issue**: Six-hour rainfall values barely changed because static sensor values (28.5 mm/hr) were hard-coded in the default observation generator.
- **Remediation**: Connect rainfall nowcasting to a deterministic, physically coherent storm trajectory (`DEMO-MAHANADI-STORM-01`) moving through: Baseline ($2.0\text{ mm/h}$) $\to$ Rainfall Onset ($12.0\text{ mm/h}$) $\to$ Convective Surge ($38.5\text{ mm/h}$) $\to$ Heavy Peak ($48.0\text{ mm/h}$) $\to$ Gradual Decay ($18.0 \to 0.5\text{ mm/h}$).

### B. Risk Delta & Attribution Gaps
- **Current Issue**: The dashboard previously showed `Material Risk Delta: 0.0` with `Sub-threshold variation` when no change was registered, appearing broken.
- **Remediation**: Dynamically compute risk delta from the active scenario and display `NO MATERIAL CHANGE` when sub-threshold, and transparent mathematical causal waterfall attribution when material risk shifts occur.

### C. Hydrograph & River Chart Clarity
- **Current Issue**: Hydrograph tooltips and threshold lines lacked explicit units and could overlap during extreme surge visualization.
- **Remediation**: Standardize X/Y axes with explicit units ($m$ for Stage, $m^3/s$ for Discharge), enforce $P10 \le P50 \le P90$ ordering, and clearly label `WARNING LEVEL` and `DANGER LEVEL`.

### D. Model Output & Framework Transparency
- **Current Issue**: UI must clearly distinguish between genuine PyTorch ConvLSTM deep inference outputs and analytical baseline models.
- **Remediation**: Strictly label `RAIN_L3_CONVLSTM` only when genuine ConvLSTM inference executed; otherwise display `SIMULATION SCENARIO OUTPUT` or `MODEL OUTPUT UNAVAILABLE`.

### E. Unified End-to-End Demo Orchestrator
- **Current Issue**: Replay was separated from the realtime event bus, meaning stepping through replay didn't trigger the complete downstream causal pipeline (Event Bus $\to$ Forecast Trigger $\to$ River $\to$ Inundation $\to$ Impact $\to$ Risk $\to$ Alert $\to$ Geofenced Public Notification).
- **Remediation**: Build `services/demo/` (`demo_scenario.py`, `demo_orchestrator.py`, `demo_state.py`, `demo_timeline.py`) that synchronously drives the entire event chain across all endpoints with play, pause, step, speed (0.5x, 1x, 2x, 5x, 10x), and reset controls.

### F. Geofencing Demonstration & Mock SMS
- **Current Issue**: Public citizen geofencing demo needs clear side-by-side verification showing that an affected user receives mock notifications while an outside user is excluded.
- **Remediation**: Create deterministic test citizens (`DEMO USER` in Cuttack/Mahanadi flood zone vs `OUTSIDE AREA USER` in Rourkela/Sundargarh).
