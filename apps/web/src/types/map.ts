import { ConfidenceLevel, AlertSeverity, QualityFlag, ProvenanceMetadata } from '../types';

export type MapMode = 'LIVE' | 'REPLAY' | 'OFFLINE';
export type MapProviderType = 'live' | 'replay' | 'offline';

export interface MapLayerConfig {
  id: string;
  name: string;
  category: 'base' | 'hydrology' | 'meteorology' | 'inundation' | 'assets' | 'alerts';
  enabled: boolean;
  opacity: number;
  available: boolean;
  statusText?: string;
}

export interface RainfallGridCell {
  id: string;
  bounds: [[number, number], [number, number]]; // [[latMin, lonMin], [latMax, lonMax]]
  center: [number, number];
  rainfall_mm_hr: number;
  accumulation_6h_mm: number;
  heavy_rain_prob: number;
  uncertainty_std: number;
  data_confidence: ConfidenceLevel;
  model_confidence: ConfidenceLevel;
  valid_time: string;
  forecast_run_id: string;
}

export interface MapStationFeature {
  id: string;
  name: string;
  type: 'river' | 'weather' | 'barrage' | 'weir';
  coordinates: [number, number]; // [lat, lon]
  current_stage_m?: number;
  warning_level_m?: number;
  danger_level_m?: number;
  forecast_peak_stage_m?: number;
  rainfall_1h_mm?: number;
  quality_flag: QualityFlag;
  data_confidence: ConfidenceLevel;
  source: string;
  last_updated: string;
}

export interface MapCriticalAsset {
  id: string;
  name: string;
  type: 'hospital' | 'shelter' | 'school' | 'bridge' | 'power_substation' | 'highway';
  coordinates: [number, number];
  flood_risk: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  estimated_depth_m: number;
  distance_to_flood_m: number;
  population_served?: number;
}

export interface MapAlertZone {
  id: string;
  name: string;
  severity: AlertSeverity;
  coordinates: [number, number][];
  lead_time_hours: number;
  trigger_cause: string;
  human_review_required: boolean;
  probability: number;
}

export interface InundationPolygonFeature {
  id: string;
  depthClass: '0_0.3m' | '0.3_1m' | '1_2m' | 'gt_2m';
  depthRangeLabel: string;
  depth_m: number;
  probability: number;
  coordinates: [number, number][];
}

export interface SelectedFeatureDetail {
  type: 'grid_cell' | 'station' | 'asset' | 'alert' | 'reach' | 'inundation';
  title: string;
  subtitle: string;
  data: Record<string, any>;
  provenance?: ProvenanceMetadata;
}
