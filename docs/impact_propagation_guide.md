# JALDRISHTI AI — Critical Infrastructure & Population Impact Propagation Guide (Phase 15)

## 1. Scope & Capabilities

The Impact Propagation Engine maps evolving 2D inundation depth and extent grids into exposure metrics across:
- **Public Healthcare & Hospitals** (e.g. SCB Medical College Cuttack, Kendrapara DHH)
- **Multi-Purpose Cyclone & Flood Shelters** (e.g. Marshaghai, Nimapara hubs)
- **Bridges & Embankments** (e.g. NH-16 Mahanadi bridge, Kathajodi sluices)
- **Power Grid Substations** (e.g. Choudwar 220kV grid)
- **Strategic Highway Corridors** (e.g. NH-53 Cuttack-Paradip Port expressway)
- **Demographic Cohorts** (WorldPop 100m population grid integration)

---

## 2. Critical Asset Risk Tiers

| Risk Tier | Criteria | Operational Protocol |
|---|---|---|
| **SAFE** | Distance $> 500\text{m}$, ground elevation above flood crest. | Normal facility operation. |
| **MODERATE_RISK** | Distance $< 300\text{m}$ or shallow perimeter inundation ($<0.3\text{m}$). | Alert facility disaster management committee; deploy mobile dewatering pumps. |
| **HIGH_RISK** | Water ingress on premises or depth $>0.3\text{m}$; isolation risk. | Priority emergency evacuation / generator elevate / barricade access routes. |

---

## 3. GloFAS Source Degradation Handling

When upstream streamflow telemetry defaults from CWC observed gauges to GloFAS fallback:
1. Asset & population records are tagged with `dataset_state: "MODELED_GLOFAS"`.
2. Overall confidence drops to `DATA_DEGRADED`.
3. The UI highlights **"Impact based on MODELED_GLOFAS"** to prevent overconfidence during degraded satellite telemetry states.
