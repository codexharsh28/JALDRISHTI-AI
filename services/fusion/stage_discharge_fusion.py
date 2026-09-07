"""
Multi-Source River Stage and Discharge Fusion Engine for JALDRISHTI AI (Phase 17).
Fuses telemetry, manual staff gauges, barrage logs, and satellite altimetry
with dynamic variance-latency reliability weighting.
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import logging
from services.models import ConfidenceLevel

logger = logging.getLogger(__name__)

class StageDischargeFusionEngine:
    """
    Computes statistically robust fused river stage and discharge estimates.
    """

    # Baseline sensor nominal variances (m^2)
    NOMINAL_VARIANCES: Dict[str, float] = {
        "CWC_TELEMETRY": 0.0025,       # std = 0.05m
        "CWC_MANUAL_GAUGE": 0.0100,    # std = 0.10m
        "WRD_BARRAGE_LOG": 0.0064,     # std = 0.08m
        "SATELLITE_ALTIMETRY": 0.0400  # std = 0.20m
    }

    @classmethod
    def fuse_stage_observations(
        cls,
        observations: List[Dict[str, Any]],
        latency_penalty_coeff: float = 0.005,
        anomaly_penalty_coeff: float = 0.05
    ) -> Tuple[float, float, Dict[str, float], ConfidenceLevel]:
        """
        Fuses river stage observations from multiple concurrent sources.
        Returns: (fused_stage_m, uncertainty_std_m, source_weights, data_confidence)
        """
        if not observations:
            return 25.0, 0.50, {}, ConfidenceLevel.DATA_DEGRADED

        weights: Dict[str, float] = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for obs in observations:
            src = obs.get("source_id", "CWC_TELEMETRY")
            val = float(obs.get("stage_m", 25.0))
            latency_hr = float(obs.get("latency_hours", 0.0))
            is_anomalous = bool(obs.get("is_anomalous", False))
            quality_flag = obs.get("quality_flag", "GOOD")

            if quality_flag == "BAD":
                continue

            base_var = cls.NOMINAL_VARIANCES.get(src, 0.02)
            adjusted_var = base_var + (latency_hr * latency_penalty_coeff) + (anomaly_penalty_coeff if is_anomalous else 0.0)
            
            w = 1.0 / max(0.0001, adjusted_var)
            weights[src] = w
            weighted_sum += w * val
            total_weight += w

        if total_weight <= 0.0:
            return 25.0, 0.50, {}, ConfidenceLevel.DATA_DEGRADED

        fused_stage = weighted_sum / total_weight
        uncertainty_std = math.sqrt(1.0 / total_weight)

        # Normalize weights to percentages
        normalized_weights = {k: round(v / total_weight, 4) for k, v in weights.items()}

        # Confidence level
        if uncertainty_std <= 0.06 and len(weights) >= 2:
            confidence = ConfidenceLevel.HIGH
        elif uncertainty_std <= 0.15:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.DATA_DEGRADED

        return round(fused_stage, 3), round(uncertainty_std, 3), normalized_weights, confidence

    @classmethod
    def fuse_discharge_observations(
        cls,
        observations: List[Dict[str, Any]]
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Fuses discharge observations in cumecs.
        """
        if not observations:
            return 15000.0, 1000.0, {}

        weighted_sum = 0.0
        total_weight = 0.0
        weights: Dict[str, float] = {}

        for obs in observations:
            src = obs.get("source_id", "BARRAGE_DISCHARGE")
            val = float(obs.get("discharge_cumec", 15000.0))
            rel = float(obs.get("reliability_pct", 90.0)) / 100.0
            
            w = rel / 100.0
            weights[src] = w
            weighted_sum += w * val
            total_weight += w

        if total_weight <= 0:
            return 15000.0, 1000.0, {}

        fused_q = weighted_sum / total_weight
        norm_weights = {k: round(v / total_weight, 4) for k, v in weights.items()}
        return round(fused_q, 1), round(fused_q * 0.06, 1), norm_weights
