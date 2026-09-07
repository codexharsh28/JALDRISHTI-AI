# Spatial & Temporal Rainfall Grid Specification
## JALDRISHTI AI (SIH26071)

---

## 1. Computational Model Grid vs. Native Source Resolution

> **CRITICAL SCIENTIFIC PRINCIPLE:**  
> The computational model grid is a uniform spatial discrete representation required for hydrodynamic surrogate routing and tensor operations. It is **NOT** the native physical resolution of coarse satellite or NWP sensors.

| Ingestion Source | Native Sensor Resolution | Reprojection & Resampling Method | Target Model Grid Resolution | Downscaling / Fusion Classification |
|---|---|---|---|---|
| **IMD Gridded Rainfall** | 0.25° (~28 km) | Bilinear continuous surface interpolation | 2.5 km ($20 \times 20$ grid) | Spatial downscaling via topographic elev gradient |
| **NASA GPM IMERG** | 0.10° (~10 km) | Area-conserving spatial re-gridding | 2.5 km | Resampling with gauge bias adjustment |
| **MOSDAC INSAT-3DR** | 0.04° (~4.0 km) | Nearest neighbor to centroid | 2.5 km | Direct pixel-to-grid aggregation |
| **Doppler Radar (DWR)** | 1.0 km Cartesian | Spatial box-averaging | 2.5 km | Conservative spatial upscaling |
| **Copernicus DEM GLO-30** | 30 meters | Bilinear aggregation for hydrodynamic grid | 2.5 km macro / 30m local | Topographic HAND conditioning |

---

## 2. Computational Grid Parameters (Mahanadi Delta Pilot Area)

- **Coordinate Reference System (CRS):** `EPSG:4326` (WGS84 Geographic)
- **Bounding Box Extent:**
  - Latitude Min: $20.00^\circ\text{ N}$
  - Latitude Max: $21.00^\circ\text{ N}$
  - Longitude Min: $85.00^\circ\text{ E}$
  - Longitude Max: $87.00^\circ\text{ E}$
- **Computational Cell Size:** $0.0225^\circ \times 0.025^\circ$ ($\approx 2.5\text{ km} \times 2.5\text{ km}$)
- **Grid Matrix Dimensions:** $20 \text{ rows} \times 20 \text{ columns} = 400 \text{ spatial nodes}$
- **Temporal Windows Supported:** 5-minute, 15-minute, 30-minute, 1-hour rolling aggregations.
