# JALDRISHTI AI — Live Inundation Evolution & Spatial Differencing Methodology (Phase 15)

## 1. Executive Summary

Phase 15 delivers reactive flood surface differencing and critical impact propagation for the Mahanadi delta. As new hydrometric observations and streamflow nowcasts arrive, JALDRISHTI AI computes not only where flooding is currently occurring, but:
- **Where flood extent is expanding or receding**
- **How fast the inundated boundary is moving ($\text{km}^2/\text{hr}$)**
- **What critical public facilities and population cohorts are becoming exposed**

---

## 2. Inundation Snapshot Schema

Each prediction or observation generates an immutable, versioned `InundationSnapshot`:
- `inundation_snapshot_id`: Unique identifier (e.g. `INUN-SNAP-20260827-01`)
- `forecast_run_id`: Provenance run ID
- `valid_time`: ISO 8601 evaluation timestamp
- `scenario`: Forecast ensemble percentile (`P10`, `P50`, `P90`)
- `inundated_area_sqkm`: Total surface extent ($\text{km}^2$)
- `mean_flood_probability`: Mean pixel probability across wet cells
- `peak_depth_m`: Maximum estimated water depth
- `depth_classes`: Breakdown across 4 depth classes with `MODEL_ESTIMATE` tagging
- `dataset_state`: `MODELED_SURROGATE` or `MODELED_GLOFAS`
- `confidence`: `HIGH`, `MEDIUM`, `LOW`, or `DATA_DEGRADED`

---

## 3. Spatial Differencing & Expansion Velocity

Spatial shifts between sequential snapshots $S_t$ and $S_{t-1}$ are calculated as:

$$\Delta \text{Area} = \text{Area}(S_t) - \text{Area}(S_{t-1})$$

$$\text{Expansion Rate} = \frac{\Delta \text{Area}}{\Delta t} \quad (\text{km}^2/\text{hr})$$

### Material Change Gating
To suppress computation thrashing caused by small numerical jitter, impact recalculations are only triggered when:
- $|\Delta \text{Area}| \ge 2.0\text{ km}^2$, OR
- $|\Delta \text{Probability}| \ge 0.03$

---

## 4. Depth Evolution & Scientific Honesty

Depth classifications are partitioned into 4 standard flood engineering tiers:
1. **$0.0 - 0.3\text{m}$ (Shallow)**: Localized sheet flow, minor road disruption.
2. **$0.3 - 1.0\text{m}$ (Moderate)**: Vehicular access impassable, ground-floor ingress.
3. **$1.0 - 2.0\text{m}$ (Severe)**: High hazard, structural risk, evacuation required.
4. **$>2.0\text{m}$ (Extreme)**: Life-threatening floodplain submergence.

All depth outputs retain the **`MODEL_ESTIMATE`** metadata label to avoid conflation with physically surveyed watermarks.
