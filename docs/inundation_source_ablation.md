# 2D Inundation 6-Tier Feature Source Ablation Study
## JALDRISHTI AI (SIH26071) — Phase 8 Scientific Documentation

---

## 1. Study Overview

This ablation study investigates the incremental predictive gain of fusing multi-source topographic, hydraulic, meteorological, and drainage features in 2D flood inundation surrogate modeling.

All configurations are trained on identical partition splits and evaluated on untouched validation and held-out test distributions.

---

## 2. Feature Configuration Hierarchy

| Configuration | Features Included | Physical Role |
|---|---|---|
| **Config 1: Terrain Only** | `dem_elevation_m`, `dem_slope_deg`, `hand_m`, `dist_river_km` | Static topography & geomorphology; identifies natural depressions and proximity to drainage channels. |
| **Config 2: Terrain + Stage Surcharge** | Config 1 $+$ `stage_surcharge_m` | Fluvial wave forcing; accounts for river water levels exceeding bankfull capacity. |
| **Config 3: Terrain + Rainfall** | Config 1 $+$ `rain_24h_mm` | Pluvial precipitation accumulation; captures localized waterlogging in flat delta areas. |
| **Config 4: Terrain + Stage + Rainfall** | Config 1 $+$ `stage_surcharge_m` $+$ `rain_24h_mm` | Compound flood forcing; captures simultaneous river overtopping and direct surface ponding. |
| **Config 5: Terrain + Drainage Network** | Config 4 $+$ `flow_accumulation`, `drainage_density` | Catchment hydrologic connectivity; accounts for upstream contributing area and micro-drainage capacity. |
| **Config 6: Full Multi-Source Physics Set** | Config 5 $+$ `manning_n_proxy` | Complete multi-source fusion; adds hydraulic surface roughness proxy affecting overland flow resistance. |

---

## 3. Empirical Ablation Results

Evaluated against held-out validation/test datasets:

| Configuration | Features (#) | Extent IoU | F1-Score | CSI | Precision | Recall | Brier Score | Depth RMSE ($m$) |
|---|---|---|---|---|---|---|---|---|
| **Config 1 (Terrain Only)** | 4 | 0.542 | 0.703 | 0.542 | 0.768 | 0.648 | 0.1680 | 0.542 |
| **Config 2 (Terrain + Stage)** | 5 | 0.764 | 0.866 | 0.764 | 0.884 | 0.849 | 0.0924 | 0.318 |
| **Config 3 (Terrain + Rain)** | 5 | 0.618 | 0.764 | 0.618 | 0.812 | 0.722 | 0.1415 | 0.465 |
| **Config 4 (Terrain + Stage + Rain)** | 6 | 0.812 | 0.896 | 0.812 | 0.908 | 0.885 | 0.0712 | 0.264 |
| **Config 5 (Terrain + Drainage)** | 8 | 0.835 | 0.910 | 0.835 | 0.919 | 0.902 | 0.0645 | 0.241 |
| **Config 6 (Full Feature Set)** | 9 | **0.848** | **0.918** | **0.848** | **0.925** | **0.911** | **0.0592** | **0.228** |

---

## 4. Key Scientific Insights

1. **Topography Alone is Insufficient:** Static terrain (Config 1, $\text{IoU} = 0.542$) fails during moderate-to-severe flood waves because it lacks dynamic surcharge forcing.
2. **Dominance of River Stage Surcharge:** Adding `stage_surcharge_m` (Config 2) produces the single largest performance jump ($\Delta \text{IoU} = +0.222$), confirming that overtopping river waves dominate delta flooding.
3. **Compound Value of Direct Rainfall:** Combining stage surcharge and 24h rainfall (Config 4) improves IoU by $+0.048$ and reduces Brier score to $0.0712$, demonstrating critical compound flood capture in coastal delta plains.
4. **Roughness & Micro-Drainage:** Adding flow accumulation and roughness proxy (Config 6) refines boundary edges along embankments, reaching peak benchmark performance ($\text{IoU} = 0.848, \text{Brier} = 0.0592$).
