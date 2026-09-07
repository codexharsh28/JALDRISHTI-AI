"""
Deterministic Quality Control (QC) Engine for JALDRISHTI AI.
Applies physical limit checks, spike/jump detection, temporal continuity,
spatial bounds, and sensor consistency before feature generation or ML inference.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from services.models import QualityFlag

# Physical limits for hydrometeorological parameters
PHYSICAL_LIMITS = {
    "rainfall_15m_mm": (0.0, 150.0),       # Max ~600mm/hr extreme convective burst
    "rainfall_1h_mm": (0.0, 300.0),
    "rainfall_24h_mm": (0.0, 1000.0),
    "temperature_c": (-5.0, 55.0),
    "relative_humidity_pct": (5.0, 100.0),
    "wind_speed_kmh": (0.0, 350.0),
    "surface_pressure_hpa": (850.0, 1050.0),
    "river_stage_m": (0.0, 60.0),
    "river_discharge_cumec": (0.0, 80000.0)
}

# Maximum plausible 1-hour jumps
MAX_1H_JUMPS = {
    "river_stage_m": 4.5,       # River stage cannot jump >4.5m in 1h under normal hydraulics
    "temperature_c": 15.0,      # Temperature cannot jump >15C in 1h
    "surface_pressure_hpa": 20.0
}

class QualityControlEngine:
    @staticmethod
    def check_observation(
        record: Dict[str, Any],
        previous_record: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None
    ) -> Tuple[QualityFlag, Dict[str, str]]:
        """
        Evaluates an observation dictionary against deterministic QC rules.
        Returns overall QualityFlag and a dictionary of detected anomalies.
        """
        anomalies = {}
        flag = QualityFlag.GOOD

        # 1. Coordinates check
        lat = record.get("lat")
        lon = record.get("lon")
        if lat is None or lon is None or not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            anomalies["coordinates"] = "Invalid or missing geospatial coordinates"
            return QualityFlag.BAD, anomalies

        # 2. Timestamp validity & Staleness check
        obs_time = record.get("timestamp")
        if not obs_time:
            anomalies["timestamp"] = "Missing observation timestamp"
            return QualityFlag.MISSING, anomalies

        if now:
            latency_mins = (now - obs_time).total_seconds() / 60.0
            if latency_mins > 180.0:  # > 3 hours old
                flag = QualityFlag.STALE
                anomalies["staleness"] = f"Observation is stale ({latency_mins:.1f} mins old)"

        # 3. Physical range checks
        for param, (min_val, max_val) in PHYSICAL_LIMITS.items():
            val = record.get(param)
            if val is not None:
                if val < 0.0 and param.startswith("rainfall"):
                    anomalies[param] = f"Negative rainfall detected: {val}"
                    flag = QualityFlag.BAD
                elif val < min_val or val > max_val:
                    anomalies[param] = f"Out of physical bounds ({min_val} - {max_val}): {val}"
                    if flag != QualityFlag.BAD:
                        flag = QualityFlag.SUSPECT

        # 4. Spike / Rate-of-Change checks against previous observation
        if previous_record:
            for param, max_jump in MAX_1H_JUMPS.items():
                curr_val = record.get(param)
                prev_val = previous_record.get(param)
                if curr_val is not None and prev_val is not None:
                    jump = abs(curr_val - prev_val)
                    if jump > max_jump:
                        anomalies[param] = f"Unrealistic spike/jump detected ({jump:.2f} > max {max_jump})"
                        flag = QualityFlag.SUSPECT

        # 5. Missing critical parameters
        if record.get("rainfall_1h_mm") is None and record.get("river_stage_m") is None:
            if flag == QualityFlag.GOOD:
                flag = QualityFlag.MISSING
                anomalies["missing_data"] = "Both rainfall and river stage are missing"

        return flag, anomalies
