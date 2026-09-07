# Map Provider Configuration & Credential Guide
## JALDRISHTI AI (SIH26071)

---

## 1. Map Provider Policy & Authentication Model

JALDRISHTI AI supports multiple basemap providers with clear credential separation:

1. **OpenStreetMap Public (`VITE_MAP_PROVIDER=osm` - Default):**
   - Tile URL: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`
   - Authentication: **None required** (Public open-access with standard attribution).
   - Attribution: `© OpenStreetMap contributors`
2. **MapTiler (`VITE_MAP_PROVIDER=maptiler`):**
   - Tile URL: `https://api.maptiler.com/maps/{style}/256/{z}/{x}/{y}.png?key={VITE_MAP_API_KEY}`
   - Authentication: **Requires Public Client API Key** (`VITE_MAP_API_KEY`).
   - Attribution: `© MapTiler © OpenStreetMap contributors`
3. **Mapbox (`VITE_MAP_PROVIDER=mapbox`):**
   - Tile URL: `https://api.mapbox.com/styles/v1/mapbox/{style}/tiles/{z}/{x}/{y}?access_token={VITE_MAP_API_KEY}`
   - Authentication: **Requires Public Access Token** (`VITE_MAP_API_KEY`).
   - Attribution: `© Mapbox © OpenStreetMap`
4. **CARTO (`VITE_MAP_PROVIDER=carto`):**
   - Tile URL: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
   - Attribution: `© OpenStreetMap contributors © CARTO`
5. **Local Vector Geometry (`VITE_MAP_PROVIDER=offline`):**
   - Zero network requests. Renders cached Mahanadi Basin boundary, subbasins, river channels, and flood contours directly in HTML5 Canvas.

---

## 2. Environment Configuration

Set in `.env` or `.env.local`:

```env
VITE_MAP_PROVIDER=osm
VITE_MAP_STYLE_URL=
VITE_MAP_API_KEY=
```

---

## 3. Graceful Failure & Zero Broken Tiles

If a commercial provider (e.g. MapTiler or Mapbox) is selected but `VITE_MAP_API_KEY` is not provided:
- The system **will not request unauthenticated tiles** that produce repeating "API KEY REQUIRED" error images.
- A diagnostic status banner appears: `LIVE MAP PROVIDER NOT CONFIGURED (VITE_MAP_API_KEY MISSING)`.
- The system automatically engages **`OfflineMapProvider`** while preserving 100% of the Phase 4 rainfall nowcast, river telemetry, and inundation layers.
