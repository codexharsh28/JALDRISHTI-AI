"""
Composite Risk Engine & Material Change Gating for JALDRISHTI AI.
Synthesizes hydrometeorological hazard, inundation extent, asset vulnerability, and data confidence.
"""

from typing import Dict, Any, Tuple
import math
import logging
from services.risk.risk_types import RiskLevel

logger = logging.getLogger(__name__)

# Material change thresholds (filters out insignificant numerical noise)
MINIMUM_SCORE_CHANGE = 3.0
MINIMUM_PROBABILITY_CHANGE = 0.04
MINIMUM_AREA_CHANGE_SQKM = 5.0
MINIMUM_STAGE_CHANGE_M = 0.15

class RiskCalculator:
    """
    Computes normalized basin risk score (0-100) and evaluates material change thresholds.
    """

    @staticmethod
    def calculate_risk_score(
        fused_rain_mm_hr: float = 0.0,
        rain_24h_mm: float = 0.0,
        river_stage_m: float = 20.0,
        danger_stage_m: float = 26.3,
        discharge_cumec: float = 12000.0,
        flood_prob: float = 0.0,
        inundated_area_sqkm: float = 0.0,
        population_exposed: int = 0,
        critical_assets_exposed: int = 0,
        data_confidence: str = "HIGH",
        **kwargs
    ) -> Tuple[float, RiskLevel, Dict[str, float]]:
        """
        Calculates holistic risk score (0 - 100) from actual operational inputs.
        Supports both kwargs and dict unpacking.
        """
        # If first argument was a dictionary
        if isinstance(fused_rain_mm_hr, dict):
            d = fused_rain_mm_hr
            fused_rain_mm_hr = float(d.get("fused_rain_mm_hr", 0.0))
            rain_24h_mm = float(d.get("rain_24h_mm", 0.0))
            river_stage_m = float(d.get("river_stage_m", 20.0))
            danger_stage_m = float(d.get("danger_stage_m", 26.3))
            discharge_cumec = float(d.get("discharge_cumec", 12000.0))
            flood_prob = float(d.get("flood_prob", 0.0))
            inundated_area_sqkm = float(d.get("inundated_area_sqkm", 0.0))
            population_exposed = int(d.get("population_exposed", 0))
            critical_assets_exposed = int(d.get("critical_assets_exposed", 0))
            data_confidence = str(d.get("data_confidence", "HIGH"))
        # 1. Meteorological Component (0 - 25 pts)
        rain_intensity_score = min(15.0, (fused_rain_mm_hr / 65.0) * 15.0)
        rain_acc_score = min(10.0, (rain_24h_mm / 200.0) * 10.0)
        met_subscore = rain_intensity_score + rain_acc_score

        # 2. Hydrological Component (0 - 30 pts)
        stage_ratio = max(0.0, (river_stage_m - 20.0) / max(1.0, (danger_stage_m - 20.0)))
        stage_score = min(20.0, stage_ratio * 18.0)
        discharge_score = min(10.0, (discharge_cumec / 25000.0) * 10.0)
        hydro_subscore = stage_score + discharge_score

        # 3. Inundation Hydraulic Component (0 - 25 pts)
        prob_score = min(15.0, flood_prob * 15.0)
        area_score = min(10.0, (inundated_area_sqkm / 500.0) * 10.0)
        inun_subscore = prob_score + area_score

        # 4. Exposure & Vulnerability Component (0 - 20 pts)
        pop_score = min(10.0, (population_exposed / 200000.0) * 10.0)
        asset_score = min(10.0, (critical_assets_exposed / 40.0) * 10.0)
        vuln_subscore = pop_score + asset_score

        raw_score = met_subscore + hydro_subscore + inun_subscore + vuln_subscore

        # 5. Data Confidence & Quality Adjustment
        # Note: If data is degraded, risk score reflects adjusted uncertainty penalty
        confidence_adj = 0.0
        if data_confidence == "DATA_DEGRADED":
            confidence_adj = 4.0 # Uncertainty buffer
        elif data_confidence == "LOW":
            confidence_adj = 2.0

        final_score = max(0.0, min(100.0, raw_score + confidence_adj))

        # 6. Map to RiskLevel
        if final_score >= 80.0:
            level = RiskLevel.CRITICAL
        elif final_score >= 65.0:
            level = RiskLevel.ALERT
        elif final_score >= 45.0:
            level = RiskLevel.WARNING
        elif final_score >= 25.0:
            level = RiskLevel.WATCH
        else:
            level = RiskLevel.NORMAL

        subscores = {
            "meteorological": round(met_subscore, 2),
            "hydrological": round(hydro_subscore, 2),
            "inundation": round(inun_subscore, 2),
            "exposure": round(vuln_subscore, 2),
            "confidence_adjustment": round(confidence_adj, 2)
        }

        return round(final_score, 1), level, subscores

    @staticmethod
    def is_material_change(
        prev_score: float,
        new_score: float,
        prev_prob: float,
        new_prob: float,
        prev_area: float,
        new_area: float,
        prev_stage: float,
        new_stage: float
    ) -> bool:
        """
        Determines if state change exceeds material thresholds to prevent noisy recalculations.
        """
        if abs(new_score - prev_score) >= MINIMUM_SCORE_CHANGE:
            return True
        if abs(new_prob - prev_prob) >= MINIMUM_PROBABILITY_CHANGE:
            return True
        if abs(new_area - prev_area) >= MINIMUM_AREA_CHANGE_SQKM:
            return True
        if abs(new_stage - prev_stage) >= MINIMUM_STAGE_CHANGE_M:
            return True
        return False
