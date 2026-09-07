# JALDRISHTI AI — Digital Basin Twin Methodology (Phase 17)

## 1. Overview

The Digital Basin Twin continuously tracks the multi-physics state of the Mahanadi Delta:
- **Soil Moisture Dynamics**: Green-Ampt infiltration, moisture deficit ($S_{def}$), and 30-day antecedent precipitation index ($API_{30d}$).
- **Channel Routing & Storage**: Continuous mass conservation across central river reaches with backwater head effects.
- **Delta Barrage Gate Regulation**: Inflow/outflow mass balancing across Hirakud, Mundali Weir, Naraj Barrage, and Jobra Barrage.
- **Estuarine Tidal Boundary**: M2 semi-diurnal harmonic tide combined with meteorological storm surge at Paradip and Dhamra ports.

---

## 2. Mathematical Governing Formulations

### Soil Moisture Infiltration
$$f_c(t) = f_{min} + (f_{max} - f_{min}) \cdot (1 - S(t))^{1.5}$$
$$P_{eff}(t) = \max(0, P(t) - \min(P(t), f_c(t)))$$

### Channel Continuity
$$\frac{dV_{channel}}{dt} = Q_{in}(t) - Q_{out}(t)$$
$$\text{Capacity Utilization \%} = \frac{V_{channel}(t)}{V_{max}} \times 100\%$$

### Estuarine Tidal Water Level
$$\eta_{total}(t) = Z_0 + A_{M2} \sin\left(\frac{2\pi t}{T_{M2}}\right) + \eta_{surge}(t)$$
$$L_{backwater}(t) = L_0 + \alpha \cdot \eta_{total}(t)$$
