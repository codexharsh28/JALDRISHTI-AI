"""
Sensor-Specific, Seasonal, and Diurnal Baseline Provider for JALDRISHTI AI Hydromet Anomaly Detection.
Maintains robust statistical estimators (Median, MAD, EWMA volatility band, rolling P10/P90) per station and variable.
"""

from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque
import numpy as np
import math
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Level 0: Hard Physical Plausibility Limits across all required domains & aliases
PHYSICAL_BOUNDS: Dict[str, Tuple[float, float]] = {
    # 1. Rainfall (mm/hr or interval accumulation)
    "rainfall": (0.0, 300.0),            # mm/hr (300mm/hr cloudburst extreme physical limit)
    "rainfall_15m_mm": (0.0, 150.0),
    "rainfall_1h_mm": (0.0, 300.0),
    "rainfall_24h_mm": (0.0, 1200.0),
    "rain_mm": (0.0, 300.0),
    
    # 2. River Stage (meters)
    "river_stage": (0.0, 60.0),          # meters gauge height
    "river_stage_m": (0.0, 60.0),
    "water_level": (0.0, 60.0),
    "stage_m": (0.0, 60.0),

    # 3. Discharge (cumec - cubic meters per second)
    "discharge": (0.0, 80000.0),         # cumec (Mahanadi historical peak ~44,000 cumec at Mundali)
    "river_discharge_cumec": (0.0, 80000.0),
    "discharge_cumec": (0.0, 80000.0),

    # 4. Temperature (°C)
    "temperature": (-5.0, 55.0),         # Celsius
    "temperature_c": (-5.0, 55.0),
    "temp_c": (-5.0, 55.0),

    # 5. Humidity (%)
    "humidity": (5.0, 100.0),            # % Relative Humidity
    "relative_humidity_pct": (5.0, 100.0),
    "rh_pct": (5.0, 100.0),

    # 6. Pressure (hPa)
    "pressure": (850.0, 1060.0),         # hPa (Extreme cyclone central pressure ~880hPa)
    "surface_pressure_hpa": (850.0, 1060.0),
    "pressure_hpa": (850.0, 1060.0),

    # 7. Wind (km/h)
    "wind": (0.0, 350.0),                # km/h (Super cyclone gust limit ~300+ km/h)
    "wind_speed_kmh": (0.0, 350.0),
    "wind_kmh": (0.0, 350.0),

    # 8. Source Latency (minutes)
    "source_latency": (0.0, 1440.0),     # minutes (up to 24h)
    "latency_seconds": (0.0, 86400.0),

    # 9. Missingness (fraction 0.0 to 1.0)
    "missingness": (0.0, 1.0)            # ratio 0-1
}

# Level 1: Maximum Plausible 1-Hour Rate-of-Change Jump Rates
MAX_JUMP_RATES_1H: Dict[str, float] = {
    "rainfall": 180.0,                   # mm/hr max jump
    "rainfall_1h_mm": 180.0,
    "rainfall_15m_mm": 80.0,
    "rain_mm": 180.0,
    "river_stage": 4.5,                  # 4.5m/hr maximum flash surge rise
    "river_stage_m": 4.5,
    "water_level": 4.5,
    "stage_m": 4.5,
    "discharge": 25000.0,                # cumec/hr max rate
    "river_discharge_cumec": 25000.0,
    "discharge_cumec": 25000.0,
    "temperature": 15.0,                 # °C/hr
    "temperature_c": 15.0,
    "temp_c": 15.0,
    "humidity": 45.0,                    # %/hr
    "relative_humidity_pct": 45.0,
    "rh_pct": 45.0,
    "pressure": 25.0,                    # hPa/hr
    "surface_pressure_hpa": 25.0,
    "pressure_hpa": 25.0,
    "wind": 120.0,                       # km/h per hr
    "wind_speed_kmh": 120.0,
    "wind_kmh": 120.0,
    "source_latency": 360.0
}

# Seasonal definitions for Mahanadi Basin:
# MONSOON (Jun-Sep), POST_MONSOON (Oct-Nov), WINTER (Dec-Feb), PRE_MONSOON (Mar-May)
def get_current_season(dt: Optional[datetime] = None) -> str:
    now = dt or datetime.now(timezone.utc)
    m = now.month
    if 6 <= m <= 9:
        return "MONSOON"
    elif 10 <= m <= 11:
        return "POST_MONSOON"
    elif m == 12 or m <= 2:
        return "WINTER"
    else:
        return "PRE_MONSOON"

# Climatological station baseline priors for Mahanadi basin by season
DEFAULT_STATION_PRIORS: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {
    "CWC_MUNDALI": {
        "MONSOON": {
            "river_stage_m": {"median": 24.5, "mad": 1.2, "p10": 20.0, "p90": 27.5},
            "discharge": {"median": 8500.0, "mad": 3200.0, "p10": 1500.0, "p90": 25000.0},
            "river_discharge_cumec": {"median": 8500.0, "mad": 3200.0, "p10": 1500.0, "p90": 25000.0}
        },
        "NON_MONSOON": {
            "river_stage_m": {"median": 18.2, "mad": 0.8, "p10": 16.5, "p90": 20.1},
            "discharge": {"median": 450.0, "mad": 150.0, "p10": 200.0, "p90": 1200.0}
        }
    },
    "CWC_NARAJ": {
        "MONSOON": {
            "river_stage_m": {"median": 25.2, "mad": 1.1, "p10": 21.0, "p90": 28.0}
        },
        "NON_MONSOON": {
            "river_stage_m": {"median": 19.0, "mad": 0.7, "p10": 17.5, "p90": 21.0}
        }
    },
    "CWC_TIKRAPARA": {
        "MONSOON": {
            "river_stage_m": {"median": 58.5, "mad": 3.0, "p10": 52.0, "p90": 65.0}
        },
        "NON_MONSOON": {
            "river_stage_m": {"median": 48.0, "mad": 1.5, "p10": 45.0, "p90": 51.5}
        }
    },
    "IMD_AWS_BHUBANESWAR": {
        "MONSOON": {
            "rainfall_1h_mm": {"median": 2.5, "mad": 4.0, "p10": 0.0, "p90": 35.0},
            "rainfall": {"median": 2.5, "mad": 4.0, "p10": 0.0, "p90": 35.0},
            "temperature_c": {"median": 29.5, "mad": 2.5, "p10": 25.0, "p90": 35.0},
            "temperature": {"median": 29.5, "mad": 2.5, "p10": 25.0, "p90": 35.0},
            "relative_humidity_pct": {"median": 85.0, "mad": 8.0, "p10": 65.0, "p90": 98.0},
            "humidity": {"median": 85.0, "mad": 8.0, "p10": 65.0, "p90": 98.0},
            "surface_pressure_hpa": {"median": 1002.0, "mad": 4.0, "p10": 992.0, "p90": 1012.0},
            "wind_speed_kmh": {"median": 14.0, "mad": 6.0, "p10": 4.0, "p90": 32.0}
        },
        "NON_MONSOON": {
            "rainfall_1h_mm": {"median": 0.0, "mad": 0.5, "p10": 0.0, "p90": 5.0},
            "rainfall": {"median": 0.0, "mad": 0.5, "p10": 0.0, "p90": 5.0},
            "temperature_c": {"median": 27.0, "mad": 4.0, "p10": 18.0, "p90": 38.0},
            "relative_humidity_pct": {"median": 65.0, "mad": 15.0, "p10": 40.0, "p90": 85.0}
        }
    },
    "IMD_AWS_CUTTACK": {
        "MONSOON": {
            "rainfall_1h_mm": {"median": 3.0, "mad": 4.5, "p10": 0.0, "p90": 40.0},
            "rainfall": {"median": 3.0, "mad": 4.5, "p10": 0.0, "p90": 40.0},
            "temperature_c": {"median": 29.0, "mad": 2.5, "p10": 24.5, "p90": 34.5}
        }
    }
}

class StationBaselineTracker:
    """
    Maintains sensor-specific rolling statistical baselines, accounting for station, variable,
    season, diurnal patterns, and historical availability.
    """

    def __init__(self, window_size: int = 120, alpha_ewma: float = 0.15):
        self.window_size = window_size
        self.alpha_ewma = alpha_ewma
        
        # History buffers: key = (station_id, variable) -> deque of (timestamp, value)
        self._history: Dict[Tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=self.window_size))
        # Online EWMA state: key = (station_id, variable) -> {"mean": float, "var": float}
        self._ewma: Dict[Tuple[str, str], Dict[str, float]] = {}
        # Flatline detection tracking: key = (station_id, variable) -> (last_value, repeat_count)
        self._flatline_tracker: Dict[Tuple[str, str], Tuple[Optional[float], int]] = {}

    def record_observation(self, station_id: str, variable: str, value: float, obs_time: Optional[datetime] = None):
        """Records an accepted observation to maintain dynamic baselines."""
        key = (station_id, variable)
        self._history[key].append(value)

        # Update Online EWMA
        if key not in self._ewma:
            self._ewma[key] = {"mean": value, "var": 1.0}
        else:
            prev_mean = self._ewma[key]["mean"]
            diff = value - prev_mean
            new_mean = prev_mean + self.alpha_ewma * diff
            new_var = (1.0 - self.alpha_ewma) * (self._ewma[key]["var"] + self.alpha_ewma * (diff ** 2))
            self._ewma[key] = {"mean": new_mean, "var": max(new_var, 0.01)}

        # Update Flatline tracking
        last_val, count = self._flatline_tracker.get(key, (None, 0))
        if last_val is not None and math.isclose(abs(value - last_val), 0.0, abs_tol=1e-5):
            self._flatline_tracker[key] = (value, count + 1)
        else:
            self._flatline_tracker[key] = (value, 1)

    def get_baseline_stats(self, station_id: str, variable: str, obs_time: Optional[datetime] = None) -> Dict[str, float]:
        """
        Returns robust baseline statistics: median, mad, ewma_mean, ewma_std, p10, p90.
        Uses historical sample buffer if available; otherwise falls back to seasonal station prior.
        """
        key = (station_id, variable)
        history = list(self._history.get(key, []))
        season = get_current_season(obs_time)
        season_key = "MONSOON" if season == "MONSOON" else "NON_MONSOON"

        if len(history) >= 5:
            arr = np.array(history, dtype=float)
            med = float(np.median(arr))
            # MAD with normal scale factor
            mad_raw = float(np.median(np.abs(arr - med)))
            mad = max(mad_raw, 0.1) # Avoid division by zero
            p10 = float(np.percentile(arr, 10))
            p90 = float(np.percentile(arr, 90))
        else:
            # Fall back to station priors for current season
            prior_stn = DEFAULT_STATION_PRIORS.get(station_id, {})
            prior_season = prior_stn.get(season_key, prior_stn.get("MONSOON", {}))
            prior = prior_season.get(variable, {})
            
            med = prior.get("median", 10.0)
            mad = prior.get("mad", 2.0)
            p10 = prior.get("p10", max(0.0, med - 2.0 * mad))
            p90 = prior.get("p90", med + 2.0 * mad)

        # Diurnal solar/thermal adjustment for temperature, humidity, and pressure where hour is known
        hour = (obs_time or datetime.now(timezone.utc)).hour
        if variable in ["temperature", "temperature_c", "temp_c"]:
            # Diurnal sinusoidal shift: peak at 14:00 (+2.5°C), minimum at 05:00 (-2.5°C)
            diurnal_shift = 2.5 * math.sin((hour - 8.0) * math.pi / 12.0)
            med += diurnal_shift
        elif variable in ["relative_humidity_pct", "humidity", "rh_pct"]:
            # Inverse of temperature diurnal shift
            diurnal_shift = -8.0 * math.sin((hour - 8.0) * math.pi / 12.0)
            med = max(10.0, min(100.0, med + diurnal_shift))

        ewma_dict = self._ewma.get(key, {"mean": med, "var": (mad * 1.4826) ** 2})
        ewma_mean = ewma_dict["mean"]
        ewma_std = max(math.sqrt(ewma_dict["var"]), 0.1)

        return {
            "median": round(med, 3),
            "mad": round(mad, 3),
            "ewma_mean": round(ewma_mean, 3),
            "ewma_std": round(ewma_std, 3),
            "p10": round(p10, 3),
            "p90": round(p90, 3)
        }

    def get_flatline_count(self, station_id: str, variable: str) -> int:
        """Returns count of consecutive observations with identical values."""
        key = (station_id, variable)
        _, count = self._flatline_tracker.get(key, (None, 0))
        return count

    def reset(self):
        """Resets all baseline histories."""
        self._history.clear()
        self._ewma.clear()
        self._flatline_tracker.clear()

# Global baseline tracker singleton
baseline_tracker = StationBaselineTracker()
