# JALDRISHTI AI — Hydrometeorological Sensor Failure Modes & Anomaly Taxonomy (Phase 13)

## 1. Scope & Objective

This document catalogs known physical, electrical, and telemetric failure modes observed in surface Automatic Weather Stations (AWS), Doppler Weather Radars (DWR), automatic river water level gauges (AWLR), and acoustic discharge meters in the Mahanadi Delta basin.

The primary objective is to differentiate true sensor malfunctions from legitimate extreme hydro-meteorological events.

---

## 2. Failure Modes Taxonomy

| Failure Mode | Physical / Technical Cause | Telemetry Signature | Detection Level | System Response |
|---|---|---|---|---|
| **Unphysical Out-of-Bounds** | Optical / sensor circuit short, gauge cable grounding | Values outside $[-5^\circ\text{C}, 55^\circ\text{C}]$, rainfall $< 0$ or $> 300\text{ mm/hr}$, stage $> 60\text{m}$ | **Level 0: Physical Bounds** | Anomaly Score $1.0$, `LIKELY_SENSOR_ERROR`, `OUT_OF_BOUNDS`. Value discarded from fusion. |
| **Telemetry Dropout / Missingness** | GPRS modem failure, solar battery depletion during prolonged overcast | `NaN`, `null`, missing payload packet | **Level 0: Missingness** | Anomaly Score $0.85$, `LIKELY_SENSOR_ERROR`. Fallback to GPM/NWP or neighboring station. |
| **Instantaneous Impulse Spike** | Lightning discharge, mechanical tipping bucket bounce, ADC voltage transient | Extreme $1\text{h}$ jump rate exceeding physical flash limits ($> 180\text{ mm/hr}$, $> 4.5\text{m/hr}$) | **Level 1: Temporal Jump** & **Spatial Cross-Corroboration** | If isolated (zero satellite/neighbor corroboration): `LIKELY_SENSOR_ERROR`. If corroborated by GPM IMERG: `VALID_EXTREME`. |
| **Sensor Freeze / Flatline** | Float gauge siltation, submerged encoder jam, stuck analog potentiometer | Exactly identical numerical value across $\ge 5$ consecutive timesteps | **Level 1: Sensor Flatline** | Anomaly Score $0.85$, `LIKELY_SENSOR_ERROR`. Gauge flagged as `FROZEN`, excluded from routing. |
| **Calibration Drift** | Temperature sensor aging, ultrasonic transducer algae buildup | Value systematically departs from seasonal median without sudden jump | **Level 2: Robust Z-Score** & **Level 3: EWMA** | $Z_{robust} > 4.5$, `POSSIBLE_ANOMALY`. Flagged for scheduled maintenance. |
| **Extreme Cloudburst / Cyclone Surge (NOT A SENSOR FAILURE)** | Mesoscale convective cloudburst, tropical cyclonic depression landfall | Intense precipitation ($> 50 - 150\text{ mm/hr}$), rapid stage rise | **Spatial Cross-Corroboration Gate** | **`VALID_EXTREME`**: Corroborated by NASA GPM IMERG satellite QPE, NWP, and nearby AWS stations. Anomaly score discounted ($\le 0.40$). Alert engine processes observation with full confidence. |

---

## 3. Operational Distinction Rules

```
Is Value Within Physical Bounds [min, max]?
  ├── NO  ──► Immediate Level 0 Error (LIKELY_SENSOR_ERROR)
  └── YES ──► Check Temporal Jump Rate & Flatline
                ├── Flatline >= 5 steps ──► LIKELY_SENSOR_ERROR
                └── Rate of Change Check
                      ├── Normal Rate ──► Check Spatial Consistency
                      └── High Jump Rate ──► Query Spatial Cross-Corroboration:
                                              ├── Neighbor Agreement >= 40% ──► VALID_EXTREME (Preserve event)
                                              ├── Satellite QPE Corroboration ──► VALID_EXTREME (Preserve event)
                                              └── Zero External Corroboration ──► LIKELY_SENSOR_ERROR
```

---

## 4. Mitigation & Data Quality Propagation

1. **Transient vs Persistent Failures**:
   - A single transient spike increments the station's consecutive anomaly counter.
   - Provider health is only downgraded from `HEALTHY` to `DEGRADED` if anomalies persist for $\ge 3$ consecutive reporting cycles.
2. **Quality Control (QC) Flagging**:
   - Observations classified as `LIKELY_SENSOR_ERROR` or `OUT_OF_BOUNDS` are tagged with QC flag `SUSPECT` or `BAD`.
   - Precipitation and discharge fusion algorithms automatically set station fusion weights to $0.0$ for `BAD` records, preserving basin-wide hydrological continuity.
