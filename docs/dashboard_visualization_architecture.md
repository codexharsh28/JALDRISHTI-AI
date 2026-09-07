# JALDRISHTI AI — Dashboard & Map Visualization Architecture

## 1. Executive Summary
This document establishes the visualization principles, layer hierarchies, geographic basemap protocols, and UI progressive disclosure architecture for the JALDRISHTI AI Operations Command Center.

The visual system couples a dark, low-fatigue operations room design with real-time geospatial rendering powered by Leaflet, OpenStreetMap, and custom vector fallback layers.

---

## 2. Core Map Principles

### A. Real Geography First
Every main map panel renders an authoritative geographic basemap. Abstract gradients, schematic bounding boxes, and non-geographic shapes are strictly prohibited as primary representations.

- **Primary Provider**: OpenStreetMap online tile service (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`).
- **Offline Fallback**: Resilient, dark-themed vector canvas (`OfflineMapProvider`) that activates automatically when network tiles fail or are blocked.
- **Geographic Coverage**: Odisha state and the Mahanadi Delta river basin ($19.5^\circ\text{N} - 21.0^\circ\text{N}$, $84.5^\circ\text{E} - 87.0^\circ\text{E}$).

### B. Scientific Layer Composition & Stacking Order
Map layers follow a strict z-index stacking hierarchy to guarantee that geographic features remain visible beneath scientific overlays:

```
[UI Controls & Legends]       (z-index: 400-500)
       ↓
[Active Alerts & Warnings]     (z-index: 300)
       ↓
[Critical Assets & Infra]      (z-index: 250)
       ↓
[Hydromet Gauge Stations]      (z-index: 200)
       ↓
[Inundation Depth Surfaces]    (z-index: 150, opacity: 0.45 - 0.85)
       ↓
[2.5km Rainfall Model Grid]    (z-index: 100, opacity: 0.15 - 0.65)
       ↓
[River Channels & Reaches]     (z-index: 50,  stroke: #38bdf8)
       ↓
[Basin & Subbasin Boundaries]  (z-index: 25,  stroke: #06b6d4)
       ↓
[Geographic Basemap Tiles]     (z-index: 0)
```

---

## 3. Dedicated Dashboard Map Panels

### 1. Live Rainfall Map (`mode="rainfall"`)
- **Basemap**: OpenStreetMap tile layer.
- **Overlays**: Mahanadi basin boundary + river channels + Phase 4 fused/nowcast precipitation grid.
- **Model Grid Resolution**: Discrete 2.5 km computational grid (`MODEL GRID: 2.5 km`).
- **Radar Honesty**: If Doppler Weather Radar is unavailable, the panel explicitly displays `RADAR UNAVAILABLE (FUSED SATELLITE/AWS)` rather than misleading live indicators.
- **Color Scale**: Standard WMO meteorological precipitation ramp ($0$ to $>100\text{ mm/hr}$).

### 2. River Basin Overview (`mode="river"`)
- **Basemap**: OpenStreetMap tile layer with subbasin dividers.
- **Overlays**: River channels with directed reach flow vectors.
- **Telemetry Stations**: Positioned by authoritative WGS-84 coordinates from `/api/v1/stations` (e.g. CWC Mundali `[20.435, 85.752]`, CWC Naraj `[20.465, 85.860]`).
- **Standardized Symbology**:
  - `GREEN` = Normal ($Stage < Warning - 5\%$)
  - `YELLOW` = Warning ($Stage \ge Warning - 5\%$)
  - `ORANGE` = Alert ($Stage \ge Warning$)
  - `RED` = Danger ($Stage \ge Danger$)
  - `GREY` = No Telemetry / Offline
- **Status Tally Footer**: Real-time counter of stations by severity state (`Normal 98 | Warning 32 | Alert 18 | Danger 4`).

### 3. Inundation Map (Nowcast) (`mode="inundation"`)
- **Basemap**: OpenStreetMap tile layer.
- **Overlays**: River reaches + Phase 8 2D hydrodynamic flood depth polygons.
- **Hydraulic Depth Classes**:
  - `0.0 – 0.3 m`: Shallow surface water ($35\%$ opacity, `#bae6fd`)
  - `0.3 – 1.0 m`: Moderate floodplain inundation ($55\%$ opacity, `#38bdf8`)
  - `1.0 – 2.0 m`: Deep flood water ($70\%$ opacity, `#0284c7`)
  - `> 2.0 m`: Critical overbank channel surge ($85\%$ opacity, `#1d4ed8`)
- **Summary Stat Box**: Live computed flooded area ($\text{km}^2$) and peak water depth ($\text{m}$).

---

## 4. Full GIS Mode & Progressive Disclosure
In dedicated full-screen views (or upon expanding a panel), users gain access to:
1. **Layer Control System**: Organized into 6 functional categories (*Meteorology*, *Hydrology*, *Inundation*, *Critical Assets*, *Alerts*, *Scientific*).
2. **Search Bar**: Real-time fuzzy search across stations, river reaches, hospitals, bridges, and shelters with automatic map `flyTo`.
3. **Timeline Scrubber**: $-60\text{ min}$ to $+6\text{ hours}$ horizon scrub with synchronized temporal updates across all active layers.
4. **Feature Inspector**: Side drawer rendering comprehensive attributes, source provenance, confidence flags, and forecast valid times upon clicking any map element.
