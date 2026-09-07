# JALDRISHTI AI — Public Geofencing & Spatial Zone Matching

## 1. Spatial Matching Principles
Citizens subscribe to specific locations (e.g. `HOME`, `WORK`, `FAMILY`, `FARMLAND`) with a user-configured or default safety radius (default: 10.0 km).

When an operational hazard alert is confirmed by the intelligence engine:
1. The hazard centroid and spatial polygon/extent are extracted.
2. Great-circle spherical distance is calculated using the **Haversine formula**:

$$d = 2r \arcsin \left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$

Where $r = 6371.0\text{ km}$ (Earth radius).

---

## 2. Zone Classifications

```
+-------------------------------------------------------------+
| OUTSIDE_AREA (Distance > Subscription + Hazard Buffer)       |
|                                                             |
|       +---------------------------------------------+       |
|       | NEAR_AREA (Safety Buffer Match: Warning)   |       |
|       |                                             |       |
|       |       +-----------------------------+       |       |
|       |       | IN_AREA (Direct Impact Zone)|       |       |
|       |       | Critical / High Priority    |       |       |
|       |       +-----------------------------+       |       |
|       +---------------------------------------------+       |
+-------------------------------------------------------------+
```

- **`IN_AREA`**: Distance $\le \min(\text{radius}_{\text{sub}}, \text{radius}_{\text{hazard}})$. Citizen receives high-priority direct impact evacuation or flood advisory.
- **`NEAR_AREA`**: Distance $\le (\text{radius}_{\text{sub}} + \text{radius}_{\text{hazard}} + 5.0\text{ km})$. Citizen receives contextual upstream/downstream safety advisory.
- **`OUTSIDE_AREA`**: Distance exceeds all safety envelopes. The message is suppressed to prevent notification fatigue.
