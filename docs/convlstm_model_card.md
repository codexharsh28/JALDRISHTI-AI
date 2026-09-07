# Model Card: PyTorch Spatiotemporal ConvLSTM Nowcaster (`RAIN_L3_CONVLSTM`)

## Model Details
- **Developer:** JALDRISHTI AI Core Team (SIH26071)
- **Model Date:** August 2026 (Phase 10)
- **Model Version:** `v1.0-PyTorch`
- **Model Type:** 2D Convolutional Long Short-Term Memory (ConvLSTM) Encoder-Decoder
- **License:** Open Source (Academic / Operational Early Warning Pilot)

---

## Intended Use
- **Primary Use Case:** 0–6 hour precipitation nowcasting over river delta basins to drive downstream hydrological rainfall-runoff and hydrodynamic flood inundation surrogates.
- **Operational Lead Times:** +30 min, +1 hour, +2 hours, +3 hours, +4 hours, +5 hours, +6 hours.
- **Target Spatial Domain:** Mahanadi River Delta computational grid ($16 \times 24$ cells at 2.5 km resolution).

## Out-of-Scope & Unintended Uses
- Long-range synoptic weather forecasting ($> 6$ hours; Numerical Weather Prediction systems such as ECMWF IFS / NCMRWF Unified Model must be used for $> 6$h).
- Sub-kilometer urban street drainage modeling without local radar volume scan assimilation.

---

## Factors & Subbasin Disaggregation
- **Evaluation Partition:** `HELD_OUT_TEST` (`EVT-MAHANADI-2022-08`, `EVT-MAHANADI-2024-08`).
- **Input Channels:** Fused multi-source precipitation rate ($C_{in} = 1$).
- **Output Channels:** Continuous predicted surface precipitation rate ($C_{out} = 1$).

---

## Limitations & Failure Modes
1. **Convective Initiation:** As an empirical sequence-to-sequence nowcaster without full thermodynamic sounding profile inputs, the model may underestimate sudden storm cell initiation occurring within $< 30$ minutes.
2. **Dissipation Velocity:** Rapid dry-air entrainment and topography-induced convective collapse can cause positive precipitation bias at lead times $\ge 4$ hours.
3. **Data Availability Dependency:** Accuracy degrades if upstream IMERG / radar telemetry becomes unavailable or stale ($> 2$ hours latency).
