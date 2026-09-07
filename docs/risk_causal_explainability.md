# JALDRISHTI AI — Causal Risk Attribution & "Why Risk Changed" Engine (Phase 14)

## 1. Technical Principle

Every change in basin risk $\Delta R$ is derived deterministically from physical changes in:
1. **Precipitation**: Fused rate ($\text{mm/hr}$) and $24\text{h}$ accumulation ($\text{mm}$).
2. **River Hydraulics**: Gauge stage ($H_{stage}$) and discharge ($Q_{cumec}$).
3. **Inundation Extent**: Surface flood extent ($\text{km}^2$) and mean flood probability ($P_{flood}$).
4. **Impact Exposure**: Population at risk ($N_{pop}$) and critical facilities footprint ($N_{assets}$).
5. **Data Confidence**: Sensor health and telemetric degradation adjustments ($\delta_{conf}$).

---

## 2. Causal Attribution vs Heuristics

- **No Hallucinated Explanations**: Explanations are derived directly from input deltas $\Delta X_i = X_i(t) - X_i(t-1)$ and partial subscore differentials $\Delta S_k$.
- **Strict Data Confidence Attribution**: When a risk change is triggered by sensor degradation (e.g. `HIGH` $\to$ `DATA_DEGRADED`), the attribution explicitly notes `Data Confidence & Telemetry Degradation (+4.0 pts)` and **never** falsely blames rainfall or discharge.
- **Decomposition Ordering**: Contributors are sorted in descending order of absolute point impact:
  $$|\Delta S_{(1)}| \ge |\Delta S_{(2)}| \ge \dots \ge |\Delta S_{(n)}|$$

---

## 3. Example Operational Output

```json
{
  "risk_score": 42.5,
  "previous_risk_score": 24.5,
  "risk_change": 18.0,
  "risk_level": "WATCH",
  "is_material_change": true,
  "top_causal_summary": "+10.0 pts from 24h rainfall change (45.0 -> 145.0 mm); +6.0 pts from hydraulic surge (22.50m -> 25.80m)",
  "contributors": [
    {
      "factor_name": "Rainfall Accumulation & Intensity",
      "delta_score": 10.0,
      "direction": "INCREASING_RISK",
      "category": "PRECIPITATION",
      "evidence_value": "145.0 mm/24h (Intensity: 35.0 mm/hr)",
      "baseline_value": "45.0 mm/24h",
      "explanation": "+10.0 pts due to 24h rainfall change (45.0 -> 145.0 mm)"
    },
    {
      "factor_name": "River Stage & Discharge Surge",
      "delta_score": 6.0,
      "direction": "INCREASING_RISK",
      "category": "HYDROLOGY",
      "evidence_value": "25.80 m (16,500 m³/s)",
      "baseline_value": "22.50 m",
      "explanation": "+6.0 pts from hydraulic surge (22.50m -> 25.80m)"
    },
    {
      "factor_name": "Inundation Extent & Floodplain Surcharge",
      "delta_score": 3.5,
      "direction": "INCREASING_RISK",
      "category": "INUNDATION",
      "evidence_value": "285.0 km² (65% mean probability)",
      "baseline_value": "110.0 km²",
      "explanation": "+3.5 pts due to floodplain surcharge expansion (110.0 -> 285.0 km²)"
    },
    {
      "factor_name": "Data Confidence & Telemetry Degradation",
      "delta_score": -1.5,
      "direction": "DECREASING_RISK",
      "category": "CONFIDENCE",
      "evidence_value": "HIGH",
      "baseline_value": "LOW",
      "explanation": "-1.5 pts uncertainty reduction (Telemetry status: LOW -> HIGH)"
    }
  ]
}
```
