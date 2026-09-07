# JALDRISHTI AI — Inundation Evolution Operations Runbook (Phase 15)

## 1. Overview

This runbook guides hydrologists and incident commanders in monitoring live flood evolution cards and spatial differencing timelines.

---

## 2. Reading the Inundation Evolution Dashboard

1. **Rate of Expansion Meter**:
   - $\ge +15.0\text{ km}^2/\text{hr}$: Rapid flash inundation / embankment breach surge. Immediate emergency response.
   - $0.0\text{ to }+5.0\text{ km}^2/\text{hr}$: Steady baseline accumulation.
   - $< 0.0\text{ km}^2/\text{hr}$: Floodwaters receding / drainage clearing.
2. **Snapshot Comparison Timeline**:
   - Compare `CURRENT` vs `T-1` and `T-2` snapshots to view the before/after trajectory.
3. **Critical Asset Exposure Table**:
   - Filter by `HIGH_RISK` facilities to allocate rescue boats, power generator fuel, and patient transfer assets.

---

## 3. REST API Endpoints

- `GET /api/v1/inundation/current`: Current flood extent snapshot, depth classes, mean probability, confidence, dataset state.
- `GET /api/v1/inundation/history?limit=20`: List of historical inundation snapshots.
- `GET /api/v1/inundation/change`: Latest spatial differencing summary (expansion rate, net delta, cell shifts).
- `GET /api/v1/impact/current`: Current critical asset exposures and population summary.
- `GET /api/v1/impact/change`: Spatial change impact shifts and newly exposed population count.
- `POST /api/v1/inundation/inject-test`: Developer/operator simulation injection endpoint.
