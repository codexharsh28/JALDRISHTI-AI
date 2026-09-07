"""
Geospatial Asset and Provenance Manifest Generator for JALDRISHTI AI.
Generates vector layers, DEM terrain statistics, critical infrastructure points,
and provenance manifests for the Mahanadi Delta Pilot Basin.
"""

import json
import os
import math
import yaml
import numpy as np

def ensure_dirs():
    dirs = [
        "geospatial/dem",
        "geospatial/drainage",
        "geospatial/rivers",
        "geospatial/landcover",
        "geospatial/assets",
        "geospatial/population",
        "data/raw",
        "data/staging",
        "data/processed",
        "data/reference",
        "data/simulation",
        "data/manifests",
        "model_registry",
        "services/ingestion/adapters",
        "services/preprocessing",
        "services/fusion",
        "services/rainfall_nowcast",
        "services/hydrology",
        "services/inundation",
        "services/impact",
        "services/alerts",
        "services/replay",
        "services/scheduler",
        "ml/datasets",
        "ml/features",
        "ml/rainfall",
        "ml/streamflow",
        "ml/inundation",
        "ml/uncertainty",
        "ml/calibration",
        "ml/evaluation",
        "infra/docker",
        "infra/postgres",
        "infra/redis",
        "infra/monitoring",
        "notebooks",
        "tests",
        "docs",
        "apps/api",
        "apps/web"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def generate_basin_geojson():
    # Outer pilot basin boundary (Mahanadi Delta - Cuttack/Puri/Kendrapara/Jagatsinghpur)
    basin_polygon = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "basin_id": "pilot-mahanadi-delta",
                    "name": "Mahanadi Delta Pilot Basin",
                    "state": "Odisha",
                    "country": "India",
                    "area_sqkm": 14250.0,
                    "source": "Survey of India / India-WRIS Derived Catchment Baseline (Prototype)",
                    "crs": "EPSG:4326"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [84.80, 20.35],
                        [85.15, 20.70],
                        [85.60, 21.05],
                        [86.20, 20.95],
                        [86.75, 20.75],
                        [86.95, 20.40],
                        [86.85, 20.15],
                        [86.50, 19.90],
                        [85.80, 19.80],
                        [85.20, 20.05],
                        [84.80, 20.35]
                    ]]
                }
            }
        ]
    }
    with open("geospatial/drainage/basin_boundary.geojson", "w") as f:
        json.dump(basin_polygon, f, indent=2)

def generate_subbasins_geojson():
    subbasins = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "subbasin_id": "sub-upper-delta",
                    "name": "Upper Delta Reach (Mundali/Naraj)",
                    "area_sqkm": 3820.0,
                    "drainage_order": 1,
                    "mean_elevation_m": 84.5
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [84.80, 20.35],
                        [85.15, 20.70],
                        [85.60, 21.05],
                        [85.85, 20.65],
                        [85.75, 20.35],
                        [85.20, 20.05],
                        [84.80, 20.35]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "subbasin_id": "sub-central-cuttack",
                    "name": "Central Mahanadi-Kathajodi Bifurcation",
                    "area_sqkm": 4190.0,
                    "drainage_order": 2,
                    "mean_elevation_m": 38.2
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [85.75, 20.35],
                        [85.85, 20.65],
                        [86.20, 20.95],
                        [86.35, 20.50],
                        [86.10, 20.10],
                        [85.80, 19.80],
                        [85.75, 20.35]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "subbasin_id": "sub-lower-delta",
                    "name": "Lower Delta & Coastal Plains (Paradip/Kendrapara)",
                    "area_sqkm": 6240.0,
                    "drainage_order": 3,
                    "mean_elevation_m": 14.1
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [86.35, 20.50],
                        [86.20, 20.95],
                        [86.75, 20.75],
                        [86.95, 20.40],
                        [86.85, 20.15],
                        [86.50, 19.90],
                        [86.10, 20.10],
                        [86.35, 20.50]
                    ]]
                }
            }
        ]
    }
    with open("geospatial/drainage/subbasins.geojson", "w") as f:
        json.dump(subbasins, f, indent=2)

def generate_rivers_geojson():
    rivers = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "reach_id": "RCH-01",
                    "name": "Main Mahanadi Reach 1 (Inflow to Naraj)",
                    "length_km": 28.5,
                    "order": 5,
                    "channel_width_m": 1400
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [85.35, 20.40],
                        [85.55, 20.42],
                        [85.748, 20.442],
                        [85.765, 20.468]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "reach_id": "RCH-02",
                    "name": "Mahanadi North Channel (Cuttack to Marshaghai)",
                    "length_km": 68.5,
                    "order": 5,
                    "channel_width_m": 1100
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [85.765, 20.468],
                        [85.879, 20.463],
                        [86.120, 20.475],
                        [86.350, 20.445],
                        [86.518, 20.412]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "reach_id": "RCH-03",
                    "name": "Kathajodi South Channel (Naraj to Marshaghai)",
                    "length_km": 72.0,
                    "order": 5,
                    "channel_width_m": 950
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [85.765, 20.468],
                        [85.870, 20.435],
                        [86.080, 20.360],
                        [86.310, 20.350],
                        [86.518, 20.412]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "reach_id": "RCH-04",
                    "name": "Mahanadi Estuary to Bay of Bengal (Paradip)",
                    "length_km": 24.3,
                    "order": 6,
                    "channel_width_m": 2200
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [86.518, 20.412],
                        [86.610, 20.320],
                        [86.671, 20.264]
                    ]
                }
            }
        ]
    }
    with open("geospatial/rivers/river_network.geojson", "w") as f:
        json.dump(rivers, f, indent=2)

def generate_assets_geojson():
    assets = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-HOSP-01",
                    "name": "SCB Medical College & Hospital Cuttack",
                    "category": "HOSPITAL",
                    "criticality": "HIGH",
                    "bed_capacity": 1200,
                    "elevation_m": 24.8,
                    "source": "OpenStreetMap / Public Health Directory",
                    "subbasin_id": "sub-central-cuttack"
                },
                "geometry": {"type": "Point", "coordinates": [85.889, 20.478]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-HOSP-02",
                    "name": "AIIMS Bhubaneswar Hospital",
                    "category": "HOSPITAL",
                    "criticality": "HIGH",
                    "bed_capacity": 960,
                    "elevation_m": 48.2,
                    "source": "OpenStreetMap",
                    "subbasin_id": "sub-central-cuttack"
                },
                "geometry": {"type": "Point", "coordinates": [85.778, 20.231]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-HOSP-03",
                    "name": "District Headquarters Hospital Kendrapara",
                    "category": "HOSPITAL",
                    "criticality": "HIGH",
                    "bed_capacity": 300,
                    "elevation_m": 12.4,
                    "source": "OpenStreetMap",
                    "subbasin_id": "sub-lower-delta"
                },
                "geometry": {"type": "Point", "coordinates": [86.425, 20.505]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-HOSP-04",
                    "name": "Paradip Port Trust Hospital",
                    "category": "HOSPITAL",
                    "criticality": "MEDIUM",
                    "bed_capacity": 120,
                    "elevation_m": 4.8,
                    "source": "OpenStreetMap",
                    "subbasin_id": "sub-lower-delta"
                },
                "geometry": {"type": "Point", "coordinates": [86.662, 20.271]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-SHELTER-01",
                    "name": "Multipurpose Cyclone Shelter Marshaghai",
                    "category": "SHELTER",
                    "criticality": "HIGH",
                    "capacity": 2000,
                    "elevation_m": 9.2,
                    "source": "OSDMA / State Disaster Management",
                    "subbasin_id": "sub-lower-delta"
                },
                "geometry": {"type": "Point", "coordinates": [86.512, 20.415]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-SHELTER-02",
                    "name": "Cyclone Shelter Erasama",
                    "category": "SHELTER",
                    "criticality": "HIGH",
                    "capacity": 2500,
                    "elevation_m": 6.8,
                    "source": "OSDMA",
                    "subbasin_id": "sub-lower-delta"
                },
                "geometry": {"type": "Point", "coordinates": [86.598, 20.210]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-BRIDGE-01",
                    "name": "Mahanadi Rail Bridge Cuttack",
                    "category": "BRIDGE",
                    "criticality": "HIGH",
                    "length_m": 2100,
                    "elevation_m": 27.5,
                    "source": "Indian Railways / OSM",
                    "subbasin_id": "sub-central-cuttack"
                },
                "geometry": {"type": "Point", "coordinates": [85.892, 20.490]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-BRIDGE-02",
                    "name": "Naraj Road Bridge",
                    "category": "BRIDGE",
                    "criticality": "HIGH",
                    "length_m": 1450,
                    "elevation_m": 31.0,
                    "source": "NHAI / State PWD",
                    "subbasin_id": "sub-upper-delta"
                },
                "geometry": {"type": "Point", "coordinates": [85.765, 20.468]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-POWER-01",
                    "name": "OPTCL Grid Substation Choudwar (400kV)",
                    "category": "POWER_SUBSTATION",
                    "criticality": "HIGH",
                    "capacity_mva": 630,
                    "elevation_m": 34.2,
                    "source": "OPTCL / State Power Grid",
                    "subbasin_id": "sub-central-cuttack"
                },
                "geometry": {"type": "Point", "coordinates": [85.925, 20.530]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-ROAD-01",
                    "name": "NH-16 Bhubaneswar-Cuttack Express Corridor",
                    "category": "HIGHWAY",
                    "criticality": "HIGH",
                    "length_km": 28.0,
                    "elevation_m": 26.0,
                    "source": "NHAI / OSM",
                    "subbasin_id": "sub-central-cuttack"
                },
                "geometry": {"type": "LineString", "coordinates": [
                    [85.824, 20.296],
                    [85.850, 20.360],
                    [85.879, 20.463],
                    [85.918, 20.521]
                ]}
            },
            {
                "type": "Feature",
                "properties": {
                    "asset_id": "AST-ROAD-02",
                    "name": "SH-12 Cuttack-Paradip State Highway",
                    "category": "HIGHWAY",
                    "criticality": "MEDIUM",
                    "length_km": 82.0,
                    "elevation_m": 12.0,
                    "source": "State PWD / OSM",
                    "subbasin_id": "sub-lower-delta"
                },
                "geometry": {"type": "LineString", "coordinates": [
                    [85.879, 20.463],
                    [86.168, 20.258],
                    [86.518, 20.412],
                    [86.671, 20.264]
                ]}
            }
        ]
    }
    with open("geospatial/assets/critical_infrastructure.geojson", "w") as f:
        json.dump(assets, f, indent=2)

def generate_manifests():
    manifests = {
        "catalog_version": "1.0.0",
        "basin_id": "pilot-mahanadi-delta",
        "created_at": "2026-08-27T08:50:00Z",
        "datasets": [
            {
                "dataset_id": "IMD_AWS_ARG_ODISHA",
                "provider": "India Meteorological Department (IMD)",
                "product": "Surface Automatic Weather Station / Rain Gauge Telemetry",
                "version": "v2.1",
                "spatial_coverage": "Odisha Coastal Catchment (20.0-21.5N, 84.5-87.0E)",
                "temporal_resolution": "15 minutes",
                "latency_typical_mins": 25,
                "license": "IMD Open Meteorological Data Protocol (Research Use)",
                "access_method": "HTTPS API / Ingestion Adapter",
                "quality_flags_implemented": ["GOOD", "SUSPECT", "BAD", "MISSING", "STALE", "ESTIMATED"]
            },
            {
                "dataset_id": "DOPPLER_RADAR_PARADIP",
                "provider": "IMD / Doppler Weather Radar Network",
                "product": "DWR MaxZ (dBZ), Surface Rainfall Intensity (SRI), PAC (Precipitation Accumulation)",
                "version": "Max-Z 250km PPI",
                "spatial_coverage": "250km Radius from Paradip (20.264N, 86.671E)",
                "temporal_resolution": "10 minutes",
                "latency_typical_mins": 12,
                "license": "IMD Radar Services Protocol",
                "access_method": "Adapter / Machine-readable grid format fallback"
            },
            {
                "dataset_id": "MOSDAC_INSAT_3DR_HEM",
                "provider": "ISRO / SAC MOSDAC",
                "product": "Hydro-Estimator Method (HEM) Half-Hourly Precipitation",
                "version": "INSAT-3DR L2B",
                "spatial_coverage": "Indian Subcontinent (0.04 deg resolution, ~4km)",
                "temporal_resolution": "30 minutes",
                "latency_typical_mins": 45,
                "license": "ISRO MOSDAC Data Policy",
                "access_method": "Authorized API / Fallback Simulator"
            },
            {
                "dataset_id": "NASA_GPM_IMERG_EARLY",
                "provider": "NASA / PMM",
                "product": "GPM IMERG Early Precipitation L3 Half-Hourly 0.1x0.1 deg",
                "version": "V07B",
                "spatial_coverage": "Global 60N-60S",
                "temporal_resolution": "30 minutes",
                "latency_typical_mins": 240,
                "license": "NASA Open Data Policy",
                "access_method": "HTTPS / GES DISC"
            },
            {
                "dataset_id": "ECMWF_IFS_OPEN_DATA",
                "provider": "ECMWF",
                "product": "Open Data 0.25 deg NWP Precipitation, Wind, Pressure, Temperature, RH",
                "version": "IFS Cycle 48r1",
                "spatial_coverage": "Global / Regional clip",
                "temporal_resolution": "3-hourly to 6-hourly (0-72h horizon)",
                "latency_typical_mins": 360,
                "license": "CC-BY-4.0",
                "access_method": "ECMWF Open Data API / AWS Open Data"
            },
            {
                "dataset_id": "CWC_TELEMETRY_MAHANADI",
                "provider": "Central Water Commission (CWC) / India-WRIS",
                "product": "Hourly River Stage (m) and Estimated Discharge (cumecs)",
                "version": "v1.4",
                "spatial_coverage": "Mahanadi Basin Gauge Network",
                "temporal_resolution": "1 hour",
                "latency_typical_mins": 30,
                "license": "CWC Public Telemetry Access Protocol",
                "access_method": "India-WRIS REST API / WRD Sensor Feeds"
            },
            {
                "dataset_id": "COPERNICUS_DEM_GLO30",
                "provider": "ESA / Copernicus",
                "product": "Global 30m Digital Elevation Model (GLO-30)",
                "version": "2024 Release",
                "spatial_coverage": "Mahanadi Delta Pilot Polygon",
                "spatial_resolution": "30 meters",
                "license": "Copernicus Open Access",
                "access_method": "GeoTIFF Tile Storage"
            },
            {
                "dataset_id": "WORLDPOP_INDIA_2025",
                "provider": "WorldPop / University of Southampton",
                "product": "Constrained Population Density Count 100m Grid",
                "version": "2025 Extrapolated",
                "spatial_coverage": "Odisha Coastal Districts",
                "spatial_resolution": "100 meters",
                "license": "CC-BY-4.0",
                "access_method": "WorldPop API / Staged Raster"
            }
        ]
    }
    with open("data/manifests/dataset_manifest.json", "w") as f:
        json.dump(manifests, f, indent=2)

def generate_dem_and_terrain_cache():
    # Generate a realistic 50x86 grid of elevation, slope, flow accumulation, HAND
    lats = np.linspace(19.80, 21.05, 50)
    lons = np.linspace(84.80, 86.95, 86)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Elevation: Slopes from inland (NW) ~120m down to coast (SE) ~2m with river channel depressions
    dist_to_coast = np.clip((86.95 - lon_grid) / 2.15, 0, 1)
    elevation = 110.0 * (dist_to_coast ** 1.6) + 2.0
    
    # River depression along Mahanadi path
    # Path approx: (20.44, 85.74) -> (20.46, 85.88) -> (20.41, 86.52) -> (20.26, 86.67)
    channel_mask = np.exp(-((lat_grid - (20.46 - 0.08 * (lon_grid - 85.88))) ** 2) / 0.015)
    elevation = np.maximum(1.5, elevation - channel_mask * 14.0)
    
    # Slope (degrees)
    dy, dx = np.gradient(elevation)
    slope = np.arctan(np.sqrt(dx**2 + dy**2) / 2500.0) * (180.0 / np.pi)
    
    # HAND (Height Above Nearest Drainage)
    hand = np.maximum(0.2, elevation - (elevation * channel_mask + 2.0 * (1 - channel_mask)))
    
    # Flow accumulation proxy
    flow_acc = np.clip(1.0 / (slope + 0.05) + channel_mask * 250.0, 1.0, 5000.0)
    
    terrain_metadata = {
        "basin_id": "pilot-mahanadi-delta",
        "grid_shape": [50, 86],
        "bounds": [19.80, 84.80, 21.05, 86.95],
        "elevation_min_m": float(np.min(elevation)),
        "elevation_max_m": float(np.max(elevation)),
        "elevation_mean_m": float(np.mean(elevation)),
        "slope_mean_deg": float(np.mean(slope)),
        "dem_source": "Copernicus GLO-30 Processed Grid (Synthetic Prototype)",
        "elevation_sample_matrix": elevation.round(2).tolist(),
        "slope_sample_matrix": slope.round(2).tolist(),
        "hand_sample_matrix": hand.round(2).tolist()
    }
    with open("geospatial/dem/terrain_summary.json", "w") as f:
        json.dump(terrain_metadata, f, indent=2)

if __name__ == "__main__":
    ensure_dirs()
    generate_basin_geojson()
    generate_subbasins_geojson()
    generate_rivers_geojson()
    generate_assets_geojson()
    generate_manifests()
    generate_dem_and_terrain_cache()
    print("Geospatial assets, vector layers, and manifests generated successfully.")
