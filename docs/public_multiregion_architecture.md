# JALDRISHTI AI — Reusable Multi-Region Architecture & Pilot Isolation

## 1. Architectural Principle: No Hardcoded Basins
While the initial production pilot is deployed for the **Mahanadi Delta (Odisha, India)**, all core engines, notification queues, DLT message templates, and API endpoints are built to be 100% configuration-driven and reusable across any river basin or coastal delta worldwide.

---

## 2. Regional Deployment Configuration Schema

```yaml
basin:
  id: "pilot-mahanadi-delta"
  name: "Mahanadi Delta Pilot Basin"
  code: "MD-01"
  state: "Odisha"
  country: "India"
  crs: "EPSG:4326"
  bounds:
    min_lat: 19.80
    max_lat: 21.05
    min_lon: 84.80
    max_lon: 86.95
  center:
    lat: 20.46
    lon: 85.88
  area_sqkm: 14250.0
```

---

## 3. Dynamic Region Metadata Endpoint
The public frontend and client SDKs query `GET /api/v1/notifications/region` on startup to dynamically bind the regional context:

```json
{
  "region_id": "PILOT_MAHANADI_DELTA",
  "region_name": "Mahanadi Delta",
  "state": "Odisha",
  "country": "India",
  "authority_guidance_entity": "OSDMA / DDMA",
  "is_pilot_deployment": true
}
```

---

## 4. Multi-Region Deployment Lifecycle
To deploy JALDRISHTI AI to a new basin (e.g. Brahmaputra, Godavari, or Mekong):
1. Create `basin_config_<region_name>.yaml` with the basin boundary, subbasins, rating curves, and gauge stations.
2. Set environment variable `BASIN_CONFIG_PATH=basin_config_<region_name>.yaml`.
3. Register DLT template variants with the regional State Disaster Management Authority (SDMA) identifier.
4. Launch backend instance — all geofencing, multi-language routing, and citizen notifications automatically bind to the specified region.
