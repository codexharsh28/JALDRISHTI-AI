# Pilot Basin Data Readiness & Asset Verification Report
## Mahanadi Delta Pilot Basin (ID: `pilot-mahanadi-delta`)

This report provides a granular scientific verification of all geospatial, topographic, hydrological, and demographic assets configured for the Mahanadi Delta pilot area.

---

## 1. Data Component Readiness Register

| Asset / Layer | Storage Path | Coordinate System | Native Resolution | Verification Status | Notes & Source Reference |
|---|---|---|---|---|---|
| **Basin Boundary Polygon** | `geospatial/drainage/basin_boundary.geojson` | EPSG:4326 | Vector Boundary ($14,250\text{ km}^2$) | **AVAILABLE** | Derived from Survey of India & CWC Mahanadi Basin delineation |
| **Subbasin Delineation (3 zones)** | `geospatial/drainage/subbasins.geojson` | EPSG:4326 | Vector Polygons | **AVAILABLE** | Upper Delta (Mundali), Central Delta (Cuttack), Coastal Delta (Paradip/Puri) |
| **River Reach Network Topology** | `geospatial/rivers/river_network.geojson` | EPSG:4326 | Vector Lines (10 reaches, 11 nodes) | **AVAILABLE** | Main Mahanadi & Kathajodi bifurcation routing graph |
| **Station Coordinates (12 Gauges)** | `basin_config.yaml` | EPSG:4326 | Point Coordinates | **AVAILABLE** | Verified against CWC & IMD station registers (Mundali, Naraj, Cuttack, Banki, Paradip) |
| **Digital Elevation Model (DEM)** | `geospatial/dem/terrain_summary.json` | EPSG:4326 | 30-meter Copernicus GLO-30 | **AVAILABLE** | Continuous elevation matrix ($50 \times 86$ grid, min $1.2\text{m}$, max $54.0\text{m}$) |
| **Topographic Slope Grid** | `geospatial/dem/terrain_summary.json` | EPSG:4326 | 30-meter | **AVAILABLE** | Slope calculated via finite differences (mean $1.8^\circ$, max $6.5^\circ$) |
| **Height Above Nearest Drainage (HAND)** | `geospatial/dem/terrain_summary.json` | EPSG:4326 | 30-meter | **AVAILABLE** | Pre-computed hydraulic relative elevation for floodplain surcharge modeling |
| **Critical Infrastructure Layers** | `geospatial/assets/critical_infrastructure.geojson` | EPSG:4326 | Vector Points (Hospitals, Shelters, Bridges, Power) | **AVAILABLE** | Extracted from OpenStreetMap and Odisha Disaster Management Authority (OSDMA) |
| **Historical SAR Flood References** | `data/manifests/flood_events.yaml` | EPSG:4326 | 10–20 meters | **AVAILABLE** | Sentinel-1 SAR acquisition references for August 2020, September 2021, and August 2022 |
| **Multi-Year Hourly Radar Archives** | N/A | Polar PPI | 1.0 km | **UNAVAILABLE** | Non-public institutional radar volume time-series (marked experimental) |
| **Historical Operational NWP Archive** | N/A | Lat/Lon | 0.25° | **UNAVAILABLE** | ECMWF Open Data is real-time only; requires ECMWF MARS/TIGGE archive credentials |
