"""
Data Contracts and Schema Definitions for JALDRISHTI AI.
Strict Pydantic v2 schemas preserving provenance, quality flags, and confidence indicators.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class QualityFlag(str, Enum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    BAD = "BAD"
    MISSING = "MISSING"
    STALE = "STALE"
    ESTIMATED = "ESTIMATED"

class SourceStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    OFFLINE = "OFFLINE"

class AlertSeverity(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    DATA_DEGRADED = "DATA_DEGRADED"

class SystemMode(str, Enum):
    SIMULATION = "SIMULATION"
    REPLAY = "REPLAY"
    LIVE_DATA = "LIVE_DATA"

class ProvenanceMetadata(BaseModel):
    source_id: str
    provider: str
    product_name: str
    observed_at: datetime
    received_at: datetime
    source_latency_mins: float
    processing_version: str = "v1.0.0"
    model_version_id: Optional[str] = None
    forecast_run_id: Optional[str] = None
    is_simulation: bool = True
    checksum: Optional[str] = None

class StationObservation(BaseModel):
    id: str
    station_id: str
    station_name: str
    subbasin_id: str
    lat: float
    lon: float
    timestamp: datetime
    rainfall_15m_mm: Optional[float] = None
    rainfall_1h_mm: Optional[float] = None
    rainfall_24h_mm: Optional[float] = None
    temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    surface_pressure_hpa: Optional[float] = None
    river_stage_m: Optional[float] = None
    river_discharge_cumec: Optional[float] = None
    warning_level_m: Optional[float] = None
    danger_level_m: Optional[float] = None
    quality_flag: QualityFlag = QualityFlag.GOOD
    provenance: ProvenanceMetadata

class DataSourceHealth(BaseModel):
    source_id: str
    provider: str
    product_name: str
    status: SourceStatus
    last_update: datetime
    latency_seconds: float
    coverage_pct: float
    missingness_pct: float
    quality_score: float  # 0.0 - 1.0
    fallback_active: bool
    data_confidence: ConfidenceLevel
    is_simulation: bool = True
    error_message: Optional[str] = None

class RainfallNowcastFrame(BaseModel):
    lead_time_minutes: int
    valid_time: datetime
    mean_rainfall_mm_hr: float
    max_rainfall_mm_hr: float
    heavy_rain_prob: float
    extreme_rain_prob: float
    grid_matrix_sample: List[List[float]] = Field(default_factory=list) # 2D sample grid
    model_level: str
    uncertainty_std_mm: float
    model_confidence: ConfidenceLevel
    data_confidence: ConfidenceLevel

class RainfallNowcastResponse(BaseModel):
    forecast_run_id: str
    issued_at: datetime
    basin_id: str
    current_fused_rainfall_mm_hr: float
    accumulation_6h_mm: float
    frames: List[RainfallNowcastFrame]
    model_comparison: Dict[str, Any]
    provenance: ProvenanceMetadata

class HydrographPoint(BaseModel):
    timestamp: datetime
    lead_time_hours: float
    observed_m: Optional[float] = None
    forecast_p10_m: Optional[float] = None
    forecast_p50_m: Optional[float] = None
    forecast_p90_m: Optional[float] = None
    discharge_cumec: Optional[float] = None
    warning_level_m: float
    danger_level_m: float
    flood_prob: float

class RiverForecastResponse(BaseModel):
    forecast_run_id: str
    station_id: str
    station_name: str
    subbasin_id: str
    issued_at: datetime
    current_level_m: float
    warning_level_m: float
    danger_level_m: float
    peak_predicted_level_m: float
    peak_predicted_time: datetime
    peak_exceeds_danger: bool
    model_nse: float
    model_kge: float
    upstream_contributions: List[Dict[str, Any]]
    hydrograph: List[HydrographPoint]
    provenance: ProvenanceMetadata

class ModelStatus(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    BEST_VALIDATED_MODEL = "BEST_VALIDATED_MODEL"
    BASELINE = "BASELINE"
    DEPLOYED = "DEPLOYED"

class DepthStatus(str, Enum):
    MODEL_ESTIMATE = "MODEL_ESTIMATE"
    MEASURED_GAUGE = "MEASURED_GAUGE"
    UNAVAILABLE = "UNAVAILABLE"

class DepthValidationStatus(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    VALIDATED = "VALIDATED"
    NOT_EVALUATED = "NOT_EVALUATED"

class TemporalMatchStatus(str, Enum):
    MATCHED = "MATCHED"
    MISMATCH_TOLERANCE_EXCEEDED = "MISMATCH_TOLERANCE_EXCEEDED"
    REJECTED = "REJECTED"
    UNMATCHED = "UNMATCHED"

class SARReferenceComparison(BaseModel):
    event_id: str
    forecast_valid_time: datetime
    sar_acquisition_time: datetime
    time_difference_hours: float
    temporal_match_status: TemporalMatchStatus = TemporalMatchStatus.MATCHED
    observed_extent_sqkm: float
    predicted_extent_sqkm: float
    iou: float
    f1: float
    csi: float
    precision: float
    recall: float
    depth_status: DepthStatus = DepthStatus.MODEL_ESTIMATE
    depth_validation: DepthValidationStatus = DepthValidationStatus.UNAVAILABLE
    notes: Optional[str] = None

class InundationProvenance(BaseModel):
    rainfall_run_id: Optional[str] = None
    hydrology_run_id: Optional[str] = None
    inundation_run_id: str
    model_version: str
    model_status: ModelStatus = ModelStatus.CANDIDATE
    feature_version: str = "v1.0.0"
    dem_version: str = "FABDEM_v1.2"
    reference_version: str = "Sentinel-1_GRD_IW_v2.0"
    forecast_valid_time: datetime
    dataset_state: str = "REAL_HISTORICAL_HINDCAST"
    depth_status: DepthStatus = DepthStatus.MODEL_ESTIMATE
    depth_validation: DepthValidationStatus = DepthValidationStatus.UNAVAILABLE
    sar_reference: Optional[SARReferenceComparison] = None

class InundationTileSummary(BaseModel):
    forecast_run_id: str
    valid_time: datetime
    lead_time_hours: float
    inundated_area_sqkm: float
    depth_class_0_30cm_sqkm: float
    depth_class_30_100cm_sqkm: float
    depth_class_1_2m_sqkm: float
    depth_class_gt_2m_sqkm: float
    flood_prob_mean: float
    flood_polygons_geojson: Dict[str, Any]
    depth_grid_sample: List[List[float]] = Field(default_factory=list)
    validation_iou: float
    validation_f1: float
    model_status: ModelStatus = ModelStatus.CANDIDATE
    depth_status: DepthStatus = DepthStatus.MODEL_ESTIMATE
    depth_validation: DepthValidationStatus = DepthValidationStatus.UNAVAILABLE
    sar_flood_reference: Optional[SARReferenceComparison] = None
    inundation_provenance: Optional[InundationProvenance] = None
    provenance: ProvenanceMetadata

class ImpactSummary(BaseModel):
    forecast_run_id: str
    valid_time: datetime
    population_exposed: int
    population_high_risk: int
    hospitals_affected: int
    schools_affected: int
    shelters_available: int
    shelters_affected: int
    road_km_flooded: float
    bridges_critical: int
    power_substations_at_risk: int
    total_impact_score: float  # 0 to 100 explainable scale
    affected_assets: List[Dict[str, Any]]
    provenance: ProvenanceMetadata

class AlertItem(BaseModel):
    alert_id: str
    forecast_run_id: str
    severity: AlertSeverity
    title: str
    basin_id: str
    subbasin_id: str
    location_name: str
    lead_time_hours: float
    probability: float
    model_confidence: ConfidenceLevel
    data_confidence: ConfidenceLevel
    trigger_reason: str
    top_contributors: List[Dict[str, Any]]  # explainability factors
    recommended_action: str
    requires_human_review: bool
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

class ReplayStepState(BaseModel):
    step_index: int
    total_steps: int
    stage_name: str  # NORMAL, HEAVY_RAIN, PEAK, RECOVERY etc.
    scenario_time: datetime
    rainfall_mm_hr: float
    river_level_m: float
    inundation_area_sqkm: float
    active_alert_severity: AlertSeverity
    data_confidence: ConfidenceLevel
    synced_narrative: str
