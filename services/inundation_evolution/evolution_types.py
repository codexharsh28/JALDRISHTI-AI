"""
Core Inundation Evolution & Spatial Differencing Types for JALDRISHTI AI (Phase 15).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class InundationDepthDistribution(BaseModel):
    depth_0_to_0_3m_sqkm: float = 0.0
    depth_0_3_to_1m_sqkm: float = 0.0
    depth_1_to_2m_sqkm: float = 0.0
    depth_gt_2m_sqkm: float = 0.0
    dataset_state: str = "MODEL_ESTIMATE"

    def __init__(self, **data):
        if "depth_lt_0_3m_sqkm" in data and "depth_0_to_0_3m_sqkm" not in data:
            data["depth_0_to_0_3m_sqkm"] = data["depth_lt_0_3m_sqkm"]
        super().__init__(**data)

    @property
    def depth_lt_0_3m_sqkm(self) -> float:
        return self.depth_0_to_0_3m_sqkm

DepthClassBreakdown = InundationDepthDistribution

class InundationSnapshot(BaseModel):
    inundation_snapshot_id: str = Field(default_factory=lambda: f"INUN-SNAP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}")
    snapshot_id: str = ""
    forecast_run_id: str = "FR-LIVE-01"
    valid_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scenario: str = "P50"
    model_version: str = "SpatialSurrogate_v3.1"
    inundated_area_sqkm: float = 0.0
    mean_flood_probability: float = 0.0
    peak_depth_m: float = 0.0
    depth_classes: InundationDepthDistribution = Field(default_factory=InundationDepthDistribution)
    dataset_state: str = "MODELED_SURROGATE"
    confidence: str = "HIGH"
    hydrology_source: str = "OBSERVED_CWC"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __init__(self, **data):
        super().__init__(**data)
        if not self.snapshot_id:
            self.snapshot_id = self.inundation_snapshot_id
        if not self.inundation_snapshot_id and self.snapshot_id:
            self.inundation_snapshot_id = self.snapshot_id

class SpatialChangeSummary(BaseModel):
    change_id: str = Field(default_factory=lambda: f"CHG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}")
    current_snapshot_id: str = "SNAP-CURR"
    previous_snapshot_id: str = "SNAP-PREV"
    expansion_sqkm: float = 0.0
    contraction_sqkm: float = 0.0
    net_delta_sqkm: float = 0.0
    percentage_change: float = 0.0
    inundation_expansion_rate_km2_per_hour: float = 0.0
    new_cells_count: int = 0
    receded_cells_count: int = 0
    unchanged_cells_count: int = 0
    is_material_change: bool = False
    spatial_trend: str = "STABLE"
    rate_of_expansion_sqkm_per_hr: float = 0.0
    net_change_sqkm: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __init__(self, **data):
        super().__init__(**data)
        if self.rate_of_expansion_sqkm_per_hr == 0.0 and self.inundation_expansion_rate_km2_per_hour != 0.0:
            self.rate_of_expansion_sqkm_per_hr = self.inundation_expansion_rate_km2_per_hour
        if self.inundation_expansion_rate_km2_per_hour == 0.0 and self.rate_of_expansion_sqkm_per_hr != 0.0:
            self.inundation_expansion_rate_km2_per_hour = self.rate_of_expansion_sqkm_per_hr
        if self.net_change_sqkm == 0.0 and self.net_delta_sqkm != 0.0:
            self.net_change_sqkm = self.net_delta_sqkm

class AssetExposureItem(BaseModel):
    asset_id: str
    name: str = ""
    asset_name: str = ""
    asset_type: str = "CRITICAL_FACILITY"
    lat: float = 0.0
    lon: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    flood_probability: float = 0.0
    depth_class: str = "<0.3m"
    distance_to_flood_m: float = 0.0
    risk_state: str = "SAFE"
    confidence: str = "HIGH"
    source_label: str = "OBSERVED_CWC"
    dataset_state: str = "OBSERVED_CWC"
    mitigation_protocol: str = "Routine floodplain monitoring"

    def __init__(self, **data):
        if "asset_name" in data and "name" not in data:
            data["name"] = data["asset_name"]
        elif "name" in data and "asset_name" not in data:
            data["asset_name"] = data["name"]
        if "latitude" in data and "lat" not in data:
            data["lat"] = data["latitude"]
        elif "lat" in data and "latitude" not in data:
            data["latitude"] = data["lat"]
        if "longitude" in data and "lon" not in data:
            data["lon"] = data["longitude"]
        elif "lon" in data and "longitude" not in data:
            data["longitude"] = data["lon"]
        super().__init__(**data)

class PopulationExposureSummary(BaseModel):
    population_exposed_now: int = 0
    population_exposed_forecast: int = 0
    newly_exposed_population: int = 0
    severely_affected_population_gt_1m: int = 0
    data_source: str = "WorldPop High-Resolution Population Grid (100m)"
    dataset_state: str = "OBSERVED_CWC"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
