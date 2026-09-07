"""
Digital Basin State Models & Type Definitions for JALDRISHTI AI (Phase 17).
Represents the real-time physical state of the Mahanadi Delta basin including
soil moisture deficit, channel storage, barrage regulations, and tidal boundary conditions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class SoilMoistureState(BaseModel):
    saturation_index: float = Field(default=0.75, description="Topsoil saturation index (0.0 to 1.0)")
    antecedent_precipitation_index_30d: float = Field(default=180.0, description="30-day API in mm")
    moisture_deficit_mm: float = Field(default=35.0, description="Soil moisture storage deficit in mm")
    infiltration_capacity_mm_hr: float = Field(default=8.5, description="Current Green-Ampt infiltration capacity")
    spatial_saturation_grid_mean: float = Field(default=0.72, description="Catchment-averaged saturation")

class ChannelStorageState(BaseModel):
    reach_id: str = "mahanadi-delta-central"
    reach_name: str = "Barmul to Naraj & Kathajodi Reach"
    current_storage_mcm: float = Field(default=450.0, description="Current channel water volume in Million Cubic Meters (MCM)")
    max_safe_storage_mcm: float = Field(default=600.0, description="Maximum non-damaging channel storage capacity in MCM")
    capacity_utilization_pct: float = Field(default=75.0, description="Channel capacity percentage filled")
    reach_travel_time_hours: float = Field(default=14.5, description="Hydraulic wave travel time through reach")
    backwater_head_m: float = Field(default=0.35, description="Backwater elevation surcharge at confluence")

class BarrageStructure(BaseModel):
    structure_id: str
    name: str
    location_lat: float
    location_lon: float
    total_gates: int
    open_gates: int
    upstream_stage_m: float
    downstream_stage_m: float
    discharge_cumec: float
    status: str = "NORMAL_REGULATION" # "NORMAL_REGULATION", "FLOOD_DISCHARGE", "EMERGENCY_SPILLWAY_ACTIVE"

class BarrageOperationState(BaseModel):
    structures: List[BarrageStructure] = Field(default_factory=list)
    total_delta_inflow_cumec: float = Field(default=18500.0, description="Total inflow at Delta Apex (Mundali/Naraj)")
    total_delta_outflow_cumec: float = Field(default=17800.0, description="Total outflow into distributaries & sea")

class TidalBoundaryState(BaseModel):
    station_id: str = "TIDE-PARADIP-01"
    station_name: str = "Paradip Port Estuary Gauge"
    astronomical_tide_m: float = Field(default=1.85, description="Predicted astronomical tide above MSL in meters")
    storm_surge_residual_m: float = Field(default=0.45, description="Meteorological storm surge residual in meters")
    total_water_level_m: float = Field(default=2.30, description="Total sea surface height at river mouth")
    tidal_phase: str = "FLOOD_TIDE" # "FLOOD_TIDE", "EBB_TIDE", "HIGH_WATER_SLACK", "LOW_WATER_SLACK"
    backwater_propagation_km: float = Field(default=28.5, description="Distance upstream affected by tidal backwater")

class DigitalBasinState(BaseModel):
    state_id: str = Field(default_factory=lambda: f"DBS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:4]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    basin_id: str = "pilot-mahanadi-delta"
    version: int = 1
    soil_moisture: SoilMoistureState = Field(default_factory=SoilMoistureState)
    channel_storage: ChannelStorageState = Field(default_factory=ChannelStorageState)
    barrage_operations: BarrageOperationState = Field(default_factory=BarrageOperationState)
    tidal_boundary: TidalBoundaryState = Field(default_factory=TidalBoundaryState)
    effective_precipitation_mm_hr: float = Field(default=12.5, description="Net excess runoff rate after infiltration")
    basin_hydraulic_risk_index: float = Field(default=68.5, description="Aggregated basin hydraulic state index (0-100)")
