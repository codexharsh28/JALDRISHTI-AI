export type AlertSeverity = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'DATA_DEGRADED';
export type SourceStatus = 'HEALTHY' | 'DEGRADED' | 'STALE' | 'OFFLINE';
export type SystemMode = 'SIMULATION' | 'REPLAY' | 'LIVE_DATA';
export type QualityFlag = 'GOOD' | 'SUSPECT' | 'BAD' | 'MISSING' | 'STALE' | 'ESTIMATED';

export interface ProvenanceMetadata {
  source_id: string;
  provider: string;
  product_name: string;
  observed_at: string;
  received_at: string;
  source_latency_mins: number;
  processing_version: string;
  model_version_id?: string;
  forecast_run_id?: string;
  is_simulation: boolean;
}

export interface DataSourceHealth {
  source_id: string;
  provider: string;
  product_name: string;
  status: SourceStatus;
  last_update: string;
  latency_seconds: number;
  coverage_pct: number;
  missingness_pct: number;
  quality_score: number;
  fallback_active: boolean;
  data_confidence: ConfidenceLevel;
  is_simulation: boolean;
  error_message?: string;
}

export interface RainfallFrame {
  lead_time_minutes: number;
  valid_time: string;
  mean_rainfall_mm_hr: number;
  max_rainfall_mm_hr: number;
  heavy_rain_prob: number;
  extreme_rain_prob: number;
  grid_matrix_sample?: number[][];
  model_level: string;
  uncertainty_std_mm: number;
  model_confidence: ConfidenceLevel;
  data_confidence: ConfidenceLevel;
}

export interface HydrographPoint {
  timestamp: string;
  lead_time_hours: number;
  observed_m?: number;
  forecast_p10_m?: number;
  forecast_p50_m?: number;
  forecast_p90_m?: number;
  discharge_cumec?: number;
  warning_level_m: number;
  danger_level_m: number;
  flood_prob: number;
}

export interface InundationSummary {
  forecast_run_id: string;
  valid_time: string;
  lead_time_hours: number;
  inundated_area_sqkm: number;
  depth_class_0_30cm_sqkm: number;
  depth_class_30_100cm_sqkm: number;
  depth_class_1_2m_sqkm: number;
  depth_class_gt_2m_sqkm: number;
  flood_prob_mean: number;
  flood_polygons_geojson: any;
  depth_grid_sample?: number[][];
  validation_iou: number;
  validation_f1: number;
  provenance: ProvenanceMetadata;
}

export interface ImpactSummary {
  forecast_run_id: string;
  valid_time: string;
  population_exposed: number;
  population_high_risk: number;
  hospitals_affected: number;
  schools_affected: number;
  shelters_available: number;
  shelters_affected: number;
  road_km_flooded: number;
  bridges_critical: number;
  power_substations_at_risk: number;
  total_impact_score: number;
  affected_assets: Array<{
    asset_id: string;
    name: string;
    category: string;
    criticality: string;
    risk_tier: string;
    elevation_m: number;
    subbasin_id: string;
  }>;
  provenance: ProvenanceMetadata;
}

export interface AlertItem {
  alert_id: string;
  forecast_run_id: string;
  severity: AlertSeverity;
  title: string;
  basin_id: string;
  subbasin_id: string;
  location_name: string;
  lead_time_hours: number;
  probability: number;
  model_confidence: ConfidenceLevel;
  data_confidence: ConfidenceLevel;
  trigger_reason: string;
  top_contributors: Array<{
    factor: string;
    contribution_pct: number;
    direction: string;
    value_desc: string;
  }>;
  recommended_action: string;
  requires_human_review: boolean;
  is_acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  created_at: string;
}

export interface ReplayState {
  step_index: number;
  total_steps: number;
  stage_name: string;
  scenario_time: string;
  rainfall_mm_hr: number;
  river_level_m: number;
  inundation_area_sqkm: number;
  active_alert_severity: AlertSeverity;
  data_confidence: ConfidenceLevel;
  synced_narrative: string;
}
