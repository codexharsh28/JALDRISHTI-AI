"""
Feature Engineering Engine for JALDRISHTI AI.
Computes multi-horizon lags, spatial basin statistics, rate-of-rise,
terrain HAND proxies, and meteorological indices for ML models.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import numpy as np

class FeatureStore:
    @staticmethod
    def extract_features(
        current_fused_rain_mm_hr: float,
        rainfall_history_mm: List[float],  # Hourly history (last 72h)
        river_stage_history_m: List[float], # Hourly history (last 24h)
        upstream_discharge_history_cumec: List[float],
        meteo_obs: Dict[str, float],
        terrain_stats: Dict[str, float],
        source_confidence_score: float,
        timestamp: datetime
    ) -> Dict[str, float]:
        """
        Calculates all canonical ML feature inputs for nowcasting, streamflow, and inundation models.
        """
        # 1. Rainfall accumulations
        rain_hist = np.array(rainfall_history_mm if rainfall_history_mm else [current_fused_rain_mm_hr])
        rain_1h = float(rain_hist[-1]) if len(rain_hist) >= 1 else current_fused_rain_mm_hr
        rain_3h = float(np.sum(rain_hist[-3:])) if len(rain_hist) >= 3 else rain_1h * 3.0
        rain_6h = float(np.sum(rain_hist[-6:])) if len(rain_hist) >= 6 else rain_3h * 2.0
        rain_12h = float(np.sum(rain_hist[-12:])) if len(rain_hist) >= 12 else rain_6h * 2.0
        rain_24h = float(np.sum(rain_hist[-24:])) if len(rain_hist) >= 24 else rain_12h * 2.0
        rain_48h = float(np.sum(rain_hist[-48:])) if len(rain_hist) >= 48 else rain_24h * 2.0
        rain_72h = float(np.sum(rain_hist[-72:])) if len(rain_hist) >= 72 else rain_48h * 1.5

        # 2. Rainfall dynamics (deltas and acceleration)
        prev_rain = rain_hist[-2] if len(rain_hist) >= 2 else current_fused_rain_mm_hr
        prev_prev_rain = rain_hist[-3] if len(rain_hist) >= 3 else prev_rain
        delta_1h = float(current_fused_rain_mm_hr - prev_rain)
        acceleration = float(delta_1h - (prev_rain - prev_prev_rain))

        # 3. Hydrological state
        stage_hist = np.array(river_stage_history_m if river_stage_history_m else [22.0])
        current_stage = float(stage_hist[-1])
        stage_lag_1 = float(stage_hist[-2]) if len(stage_hist) >= 2 else current_stage
        stage_lag_3 = float(stage_hist[-4]) if len(stage_hist) >= 4 else current_stage
        stage_lag_6 = float(stage_hist[-7]) if len(stage_hist) >= 7 else current_stage
        rate_of_rise = float(current_stage - stage_lag_1)

        discharge_hist = np.array(upstream_discharge_history_cumec if upstream_discharge_history_cumec else [15000.0])
        current_discharge = float(discharge_hist[-1])
        upstream_discharge_lag_3 = float(discharge_hist[-4]) if len(discharge_hist) >= 4 else current_discharge

        # 4. Meteorology & Seasonality
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        month = timestamp.month
        # Monsoon phase: 1 for peak SW monsoon (Jul-Aug), 0.8 for Sep/Jun, 0.2 otherwise
        monsoon_phase = 1.0 if month in [7, 8] else (0.75 if month in [6, 9, 10] else 0.15)

        # 5. Full feature dictionary
        return {
            "rain_1h": round(rain_1h, 2),
            "rain_3h": round(rain_3h, 2),
            "rain_6h": round(rain_6h, 2),
            "rain_12h": round(rain_12h, 2),
            "rain_24h": round(rain_24h, 2),
            "rain_48h": round(rain_48h, 2),
            "rain_72h": round(rain_72h, 2),
            "delta_1h": round(delta_1h, 2),
            "rain_acceleration": round(acceleration, 2),
            "current_stage_m": round(current_stage, 2),
            "stage_lag_1h_m": round(stage_lag_1, 2),
            "stage_lag_3h_m": round(stage_lag_3, 2),
            "stage_lag_6h_m": round(stage_lag_6, 2),
            "rate_of_rise_m_hr": round(rate_of_rise, 3),
            "current_discharge_cumec": round(current_discharge, 1),
            "upstream_discharge_lag_3_cumec": round(upstream_discharge_lag_3, 1),
            "temperature_c": round(meteo_obs.get("temperature_c", 27.0), 1),
            "relative_humidity_pct": round(meteo_obs.get("relative_humidity_pct", 90.0), 1),
            "wind_speed_kmh": round(meteo_obs.get("wind_speed_kmh", 25.0), 1),
            "surface_pressure_hpa": round(meteo_obs.get("surface_pressure_hpa", 1002.0), 1),
            "elevation_mean_m": round(terrain_stats.get("elevation_mean_m", 38.0), 1),
            "slope_mean_deg": round(terrain_stats.get("slope_mean_deg", 1.8), 2),
            "hand_mean_m": round(terrain_stats.get("hand_mean_m", 4.2), 2),
            "hour": hour,
            "day_of_year": day_of_year,
            "month": month,
            "monsoon_phase": monsoon_phase,
            "source_confidence_score": round(source_confidence_score, 2)
        }
