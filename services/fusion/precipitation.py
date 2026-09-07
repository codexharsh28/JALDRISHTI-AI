"""
Multi-Source Precipitation Fusion Engine for JALDRISHTI AI.
Applies quality-weighted spatial harmonization, gauge multiplicative bias correction,
uncertainty variance estimation, and graceful degradation on sensor outage.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime, timezone

from services.models import QualityFlag, ConfidenceLevel, SourceStatus

class PrecipitationFusionEngine:
    """
    Fuses Doppler Radar, Station Rain Gauges, INSAT-3DR HEM, NASA GPM IMERG, and ECMWF NWP.
    """

    # Baseline sensor precision weights
    BASE_WEIGHTS = {
        "DOPPLER_RADAR_PARADIP": 0.45,
        "IMD_AWS_ARG_ODISHA": 0.25,
        "MOSDAC_INSAT_3DR_HEM": 0.15,
        "NASA_GPM_IMERG_EARLY": 0.10,
        "ECMWF_IFS_OPEN_DATA": 0.05
    }

    # Sensor quality multiplier
    QUALITY_MULTIPLIERS = {
        QualityFlag.GOOD: 1.0,
        QualityFlag.ESTIMATED: 0.75,
        QualityFlag.SUSPECT: 0.35,
        QualityFlag.STALE: 0.10,
        QualityFlag.BAD: 0.0,
        QualityFlag.MISSING: 0.0
    }

    @classmethod
    def fuse_precipitation(
        cls,
        observations: List[Dict[str, Any]],
        gauge_multiplier_bias: float = 1.08
    ) -> Tuple[float, float, Dict[str, float], ConfidenceLevel]:
        """
        Calculates fused rainfall rate (mm/h), standard deviation uncertainty,
        normalized source weights, and overall data confidence.
        """
        valid_sources = []
        weighted_sum = 0.0
        total_effective_weight = 0.0
        applied_weights = {}

        for obs in observations:
            source_id = obs.get("source_id", "")
            raw_rate = float(obs.get("value", 0.0))
            q_flag = obs.get("quality_flag", QualityFlag.GOOD)
            status = obs.get("status", SourceStatus.HEALTHY)

            base_w = cls.BASE_WEIGHTS.get(source_id, 0.05)
            q_mult = cls.QUALITY_MULTIPLIERS.get(q_flag, 0.0)
            if status != SourceStatus.HEALTHY:
                q_mult = 0.0

            effective_w = base_w * q_mult
            
            # Apply gauge multiplicative bias correction to radar and satellite estimates
            corrected_rate = raw_rate
            if "RADAR" in source_id or "MOSDAC" in source_id or "IMERG" in source_id:
                corrected_rate = raw_rate * gauge_multiplier_bias

            if effective_w > 0.0:
                valid_sources.append((source_id, corrected_rate, effective_w))
                weighted_sum += corrected_rate * effective_w
                total_effective_weight += effective_w

        if total_effective_weight > 0.0:
            fused_rate = weighted_sum / total_effective_weight
            for src_id, rate, eff_w in valid_sources:
                applied_weights[src_id] = round(eff_w / total_effective_weight, 3)
        else:
            # Complete sensor failure fallback
            fused_rate = 0.0
            applied_weights["FALLBACK_CLIMATOLOGY"] = 1.0

        # Evaluate Data Confidence and Uncertainty Expansion
        # If Doppler Radar or AWS gauges are unavailable, data confidence is DEGRADED
        has_radar = any(s[0] == "DOPPLER_RADAR_PARADIP" for s in valid_sources)
        has_gauges = any(s[0] == "IMD_AWS_ARG_ODISHA" for s in valid_sources)

        if has_radar and has_gauges and total_effective_weight >= 0.65:
            data_confidence = ConfidenceLevel.HIGH
            uncertainty_std_mm = round(0.12 * fused_rate + 0.45, 2)
        elif has_radar or has_gauges:
            data_confidence = ConfidenceLevel.MEDIUM
            uncertainty_std_mm = round(0.24 * fused_rate + 1.20, 2)
        else:
            data_confidence = ConfidenceLevel.DATA_DEGRADED
            # Expand uncertainty bounds by 2.5x under data degradation
            uncertainty_std_mm = round(0.55 * fused_rate + 3.80, 2)

        return round(fused_rate, 2), uncertainty_std_mm, applied_weights, data_confidence

    @classmethod
    def fuse(
        cls,
        radar_precip_mm_hr: float = 28.5,
        gauge_mean_precip_mm_hr: float = 24.0,
        insat_precip_mm_hr: float = 22.4,
        imerg_precip_mm_hr: float = 19.8,
        nwp_precip_mm_hr: float = 20.5,
        source_health_map: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        obs = [
            {"source_id": "DOPPLER_RADAR_PARADIP", "value": radar_precip_mm_hr, "quality_flag": QualityFlag.GOOD, "status": SourceStatus.HEALTHY},
            {"source_id": "IMD_AWS_ARG_ODISHA", "value": gauge_mean_precip_mm_hr, "quality_flag": QualityFlag.GOOD, "status": SourceStatus.HEALTHY},
            {"source_id": "MOSDAC_INSAT_3DR_HEM", "value": insat_precip_mm_hr, "quality_flag": QualityFlag.GOOD, "status": SourceStatus.HEALTHY},
            {"source_id": "NASA_GPM_IMERG_EARLY", "value": imerg_precip_mm_hr, "quality_flag": QualityFlag.GOOD, "status": SourceStatus.HEALTHY},
            {"source_id": "ECMWF_IFS_OPEN_DATA", "value": nwp_precip_mm_hr, "quality_flag": QualityFlag.GOOD, "status": SourceStatus.HEALTHY}
        ]
        fused_rate, unc_std, weights, data_conf = cls.fuse_precipitation(obs)
        return {
            "fused_rainfall_mm_hr": fused_rate,
            "uncertainty_std_mm": unc_std,
            "source_weights": weights,
            "data_confidence": data_conf
        }
