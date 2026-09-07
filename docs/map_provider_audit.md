# Forensic Audit: Geospatial Map Provider & Basemap Authentication
## JALDRISHTI AI (SIH26071)

---

## 1. Executive Summary

This forensic audit investigates the runtime map provider configuration, style/tile endpoints, and authentication requirements for JALDRISHTI AI to resolve the root cause of the "API KEY REQUIRED" watermark issue on live basemaps.

---

## 2. Technical Provider Audit & Investigation

| Attribute | Audited Detail |
|---|---|
| **Map Engine / Library** | Leaflet (`react-leaflet` v4.2.1, `leaflet` v1.9.4) |
| **Initial Default Provider** | CARTO Dark Matter (`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`) |
| **Alternative Configured Providers** | OpenStreetMap (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`), MapTiler (`https://api.maptiler.com/maps/...`), Mapbox (`https://api.mapbox.com/...`), Offline Vector Fallback |
| **Root Cause of "API KEY REQUIRED"** | In recent commercial policy updates, CartoCDN and commercial tile proxies began enforcing origin validation / API keys on basemap tile requests from localhost/arbitrary referrers, and MapTiler/Mapbox raster services watermark tiles with "API KEY REQUIRED" when requested with missing or invalid tokens. |
| **Authentication Requirement** | • **OpenStreetMap (`osm`):** Anonymous public access (No API key required; requires compliant attribution).<br/>• **MapTiler (`maptiler`):** Requires public client API key (`VITE_MAP_API_KEY`).<br/>• **Mapbox (`mapbox`):** Requires public client access token (`VITE_MAP_API_KEY`).<br/>• **CARTO (`carto`):** Free anonymous tier subject to domain policy / optional Carto token.<br/>• **Offline Fallback (`offline`):** Zero external requests; renders cached vector boundaries in Canvas. |
| **Local Credential Check** | `MAP API KEY: NOT CONFIGURED` (No local credentials detected in `.env` / system env). |
| **Default Safe Strategy** | Standardize default runtime configuration to **OpenStreetMap (`osm`)** for keyless public operation, with clean automatic fallback to **Offline Vector Fallback (`offline`)** if tile requests fail or if a commercial provider is selected without `VITE_MAP_API_KEY`. |

---

## 3. Environment Variable Specification

To configure commercial map providers without committing secrets to source control:

```bash
# In .env or .env.local:
VITE_MAP_PROVIDER=osm           # Options: osm | carto | maptiler | mapbox | offline
VITE_MAP_STYLE_URL=             # Optional custom style URL (e.g. streets-v2-dark)
VITE_MAP_API_KEY=               # Required ONLY for MapTiler / Mapbox (public client token)
```

---

## 4. Diagnostic State & Degradation Guarantee

When a provider requiring authentication (e.g., MapTiler or Mapbox) is selected without a valid key:
1. **Zero Watermarked Tiles:** The map engine detects missing credentials before issuing tile network requests.
2. **Diagnostic State Banner:** The map renders:
   ```
   LIVE MAP PROVIDER NOT CONFIGURED (VITE_MAP_API_KEY missing for MapTiler) — Offline Fallback Active
   ```
3. **Preservation of Hydromet Data:** All Phase 4 rainfall grids, river gauges, inundation contours, critical assets, and alert zones remain 100% active and rendered on the offline vector canvas.
