"""
Multi-Source Precipitation Fusion Service for JALDRISHTI AI.
Performs dynamic, quality-weighted fusion across IMD AWS, Doppler Radar, INSAT-3DR, GPM IMERG, and NWP.
Tolerates missing sources, outputs fused rainfall, uncertainty, source weights, and data confidence.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from services.models import ConfidenceLevel
from services.fusion.rainfall_qc import RainfallQCEngine
from services.fusion.gauge_bias_correction import GaugeBiasCorrectionService

class MultiSourceRainfallFusionEngine:
    def __init__(self):
        self.bias_corrector = GaugeBiasCorrectionService()
        self.base_weights = {
            "radar": 0.40,
            "aws_gauges": 0.30,
            "insat_3dr": 0.15,
            "gpm_imerg": 0.10,
            "ecmwf_nwp": 0.05
        }

    def fuse_rainfall_sources(
        self,
        radar_val: Optional[float] = None,
        gauge_val: Optional[float] = None,
        insat_val: Optional[float] = None,
        imerg_val: Optional[float] = None,
        nwp_val: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Dynamically fuses available rainfall observations, renormalizing weights when feeds are absent.
        """
        valid_sources = {}
        
        # 1. Apply QC & Bias Corrections
        if radar_val is not None and radar_val >= 0:
            val, flag, _ = RainfallQCEngine.validate_rainfall_record(radar_val)
            if flag.value in ["GOOD", "SUSPECT"]:
                valid_sources["radar"] = self.bias_corrector.apply_radar_bias_correction(val)

        if gauge_val is not None and gauge_val >= 0:
            val, flag, _ = RainfallQCEngine.validate_rainfall_record(gauge_val)
            if flag.value in ["GOOD", "SUSPECT"]:
                valid_sources["aws_gauges"] = val

        if insat_val is not None and insat_val >= 0:
            val, flag, _ = RainfallQCEngine.validate_rainfall_record(insat_val)
            if flag.value in ["GOOD", "SUSPECT"]:
                valid_sources["insat_3dr"] = self.bias_corrector.apply_satellite_bias_correction(val)

        if imerg_val is not None and imerg_val >= 0:
            val, flag, _ = RainfallQCEngine.validate_rainfall_record(imerg_val)
            if flag.value in ["GOOD", "SUSPECT"]:
                valid_sources["gpm_imerg"] = self.bias_corrector.apply_satellite_bias_correction(val)

        if nwp_val is not None and nwp_val >= 0:
            val, flag, _ = RainfallQCEngine.validate_rainfall_record(nwp_val)
            if flag.value in ["GOOD", "SUSPECT"]:
                valid_sources["ecmwf_nwp"] = val

        # Fallback if no valid observations exist
        if not valid_sources:
            return {
                "fused_rainfall_mm_hr": 0.0,
                "fusion_uncertainty_std": 5.0,
                "data_confidence": ConfidenceLevel.DATA_DEGRADED.value,
                "active_sources_count": 0,
                "source_weights": {}
            }

        # 2. Renormalize weights for available sources
        raw_weights = {k: self.base_weights[k] for k in valid_sources.keys()}
        total_w = sum(raw_weights.values())
        normalized_weights = {k: w / total_w for k, w in raw_weights.items()}

        # 3. Compute weighted mean
        fused_val = sum(valid_sources[k] * normalized_weights[k] for k in valid_sources.keys())

        # 4. Compute source disagreement (weighted variance)
        values_arr = np.array(list(valid_sources.values()))
        weights_arr = np.array(list(normalized_weights.values()))
        weighted_variance = np.average((values_arr - fused_val) ** 2, weights=weights_arr)
        uncertainty_std = round(float(np.sqrt(max(0.25, weighted_variance))), 2)

        # 5. Data confidence evaluation
        if "radar" in valid_sources and "aws_gauges" in valid_sources:
            confidence = ConfidenceLevel.HIGH
        elif "radar" in valid_sources or "aws_gauges" in valid_sources:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.DATA_DEGRADED

        return {
            "fused_rainfall_mm_hr": round(float(fused_val), 2),
            "fusion_uncertainty_std": uncertainty_std,
            "data_confidence": confidence.value,
            "active_sources_count": len(valid_sources),
            "source_weights": {k: round(v, 3) for k, v in normalized_weights.items()},
            "contributing_values": {k: round(v, 2) for k, v in valid_sources.items()}
        }
