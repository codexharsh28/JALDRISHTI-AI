# GIS Operations Map Data Layers Register
## JALDRISHTI AI (SIH26071)

This register documents all 25 independent map layers available in the JALDRISHTI AI Operations Command Map.

---

## 1. Map Layer Inventory

| Layer ID | Layer Display Name | Category | Primary Data Source | Scientific Units | Default Enabled | Opacity Control | Click Inspection Output |
|---|---|---|---|---|---|---|---|
| `BASEMAP` | OpenStreetMap / Carto Dark | Base | CartoCDN / OpenStreetMap | Tile Imagery | Yes | Yes | Coordinate Inspector |
| `BASIN` | Basin Boundary | Base | Survey of India / CWC Boundary | Vector Polygon | Yes | Yes | Basin ID, Area ($14,250\text{ km}^2$) |
| `SUBBASINS` | Subbasins Delineation | Base | CWC Subbasin GeoJSON | Vector Polygons | Yes | Yes | Subbasin Name, Zone ID |
| `RIVERS` | River Channels & Reaches | Hydrology | CWC Mahanadi Network | Vector Lines | Yes | Yes | Reach ID, Upstream/Downstream |
| `RIVER_FLOW` | Directed River Flow Vector | Hydrology | River Topology Graph | Directional Polyline | Yes | Yes | Flow Velocity & Routing |
| `WEATHER_STATIONS` | IMD AWS Weather Stations | Meteorology | IMD Odisha AWS Network | Point Markers | Yes | Yes | Station ID, Rain, Temp, QC Flag |
| `RAIN_GAUGES` | Rainfall Tipping Buckets | Meteorology | OSDMA Hydromet Telemetry | Point Markers | Yes | Yes | Hourly Accumulation (mm) |
| `RIVER_STATIONS` | CWC Telemetry Gauges | Hydrology | CWC Flood Telemetry | Point Markers | Yes | Yes | Current Stage, Warning, Danger |
| `RAINFALL_FUSED` | 2.5km Model Grid (Fused Rain) | Meteorology | Multi-Source Fusion Engine | mm/h | Yes | Yes | Rain Rate, Accum, Heavy Prob |
| `RAINFALL_NOWCAST` | 0–6h ConvLSTM Nowcast Grid | Meteorology | Spatiotemporal Nowcaster | mm/h, P10/P50/P90 | Yes | Yes | Quantile Spreads, Uncertainty |
| `HEAVY_RAIN_PROBABILITY`| Heavy Rain (>35mm) Contours | Meteorology | XGBoost Classifier | Probability % | No | Yes | Probability Exceedance |
| `RADAR` | Paradip Doppler Radar PPI | Meteorology | IMD Paradip DWR | dBZ / mm/h | No | Yes | **Marked UNAVAILABLE** |
| `NWP` | ECMWF IFS 0.25° NWP Rain | Meteorology | ECMWF Open Data | mm/3h | No | Yes | NWP Steering Flow |
| `RIVER_LEVEL` | Current River Stage Heights | Hydrology | CWC Telemetry | meters | Yes | Yes | Stage vs Warning Level |
| `RIVER_FORECAST` | Predicted Peak Stage (24h) | Hydrology | Sequence LSTM + Routing | meters | Yes | Yes | Peak Stage, Peak Timing, Lead |
| `INUNDATION_PROBABILITY`| 2D Flood Probability Mask | Inundation | 2D Hydrodynamic Surrogate | Probability % | Yes | Yes | Surcharge Area ($\text{km}^2$) |
| `FLOOD_DEPTH` | HAND Hydraulic Depth Classes | Inundation | Copernicus DEM GLO-30 | 0-0.3m, 0.3-1m, 1-2m, >2m | Yes | Yes | Depth Class & Velocity |
| `POPULATION` | WorldPop 100m Exposure | Assets | WorldPop Constrained Grid | Persons / 100m | No | Yes | Population Exposed |
| `ROADS` | National & State Highways | Assets | OpenStreetMap Highways | Vector Lines | Yes | Yes | Highway Number, Flood Cutoff |
| `HOSPITALS` | Hospitals & Medical Centres | Assets | OSDMA Health Assets | Point Markers | Yes | Yes | Hospital Name, Beds, Risk |
| `SCHOOLS` | Schools & Relief Hubs | Assets | Odisha Education GIS | Point Markers | No | Yes | Relief Capacity |
| `SHELTERS` | OSDMA Cyclone Shelters | Assets | OSDMA Disaster Shelters | Point Markers | Yes | Yes | Shelter Capacity, Distance |
| `BRIDGES` | Mahanadi Bridges & Weirs | Assets | PWD Odisha Bridge Registry | Point Markers | Yes | Yes | Clearance to Peak Stage |
| `POWER_INFRASTRUCTURE` | Grid Substations (400kV/220kV)| Assets | OPTCL Grid GIS | Point Markers | Yes | Yes | Substation Voltage, Flood Risk |
| `ALERT_ZONES` | Early Warning Alert Zones | Alerts | Alert Decision Engine | Alert Severity (RED, etc.) | Yes | Yes | Severity, Cause, Lead, Sign-off |
