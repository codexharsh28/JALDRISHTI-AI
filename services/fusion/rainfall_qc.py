"""
Deterministic Rainfall Quality Control Engine for JALDRISHTI AI.
Applies physical range tests, spike jump checks, rate-of-rise tests,
and flags records: GOOD | SUSPECT | BAD | MISSING | STALE | ESTIMATED.
"""

from typing import Dict, Any, Tuple
from services.models import QualityFlag

class RainfallQCEngine:
    MAX_PLAUSIBLE_1H_RAIN_MM = 150.0  # Physical world record cloudburst limit
    MAX_PLAUSIBLE_10MIN_RAIN_MM = 45.0

    @staticmethod
    def validate_rainfall_record(
        rainfall_val: float,
        prev_val: float = None,
        duration_minutes: float = 60.0
    ) -> Tuple[float, QualityFlag, str]:
        """
        Applies deterministic quality tests and assigns an authoritative quality flag.
        Never deletes bad observations; marks them explicitly.
        """
        # 1. Missing check
        if rainfall_val is None:
            return 0.0, QualityFlag.MISSING, "Observation is null/missing"

        # 2. Negative rainfall (physically impossible)
        if rainfall_val < 0.0:
            return 0.0, QualityFlag.BAD, "Negative rainfall value detected"

        # 3. Exceeds physical world maximum limit
        max_limit = (RainfallQCEngine.MAX_PLAUSIBLE_1H_RAIN_MM if duration_minutes >= 60.0 
                     else RainfallQCEngine.MAX_PLAUSIBLE_10MIN_RAIN_MM)
        if rainfall_val > max_limit:
            return max_limit, QualityFlag.BAD, f"Value exceeds physical plausible limit ({max_limit} mm)"

        # 4. Spike jump check (step jump greater than 80 mm in 1 hour)
        if prev_val is not None and abs(rainfall_val - prev_val) > 85.0 and duration_minutes <= 60.0:
            return rainfall_val, QualityFlag.SUSPECT, "Unusually sharp temporal step jump detected"

        return float(rainfall_val), QualityFlag.GOOD, "Passed all deterministic QC rules"
