"""
Uncertainty Decomposition & Inundation Exceedance Surface Engine for JALDRISHTI AI (Phase 18).
Separates aleatoric variance (stochastic atmospheric physics) from epistemic variance
(sparse telemetry and model structure uncertainty).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import math
from pydantic import BaseModel, Field

class HorizonUncertaintyBreakdown(BaseModel):
    lead_time_hours: float
    total_variance: float
    aleatoric_variance: float
    epistemic_variance: float
    aleatoric_pct: float
    epistemic_pct: float
    interval_width_90pct_m: float

class UncertaintyDecompositionResponse(BaseModel):
    station_id: str
    forecast_run_id: str
    base_time: str
    data_confidence: str
    model_confidence: str
    mean_aleatoric_pct: float
    mean_epistemic_pct: float
    horizons: List[HorizonUncertaintyBreakdown]

class InundationExceedanceSummary(BaseModel):
    forecast_run_id: str
    lead_time_hours: float
    prob_exceed_0_5m_pct: float
    prob_exceed_1_0m_pct: float
    prob_exceed_2_0m_pct: float
    inundation_extent_sqkm_p50: float
    inundation_extent_sqkm_p90: float
    spatial_coverage_status: str = "CALIBRATED_SURROGATE"

class UncertaintyDecomposer:
    """
    Decomposes total predictive variance into physical aleatoric and observational/epistemic parts.
    """

    @classmethod
    def decompose_uncertainty(
        cls,
        station_id: str = "CWC_MUNDALI",
        data_confidence: str = "HIGH",
        model_confidence: str = "HIGH",
        horizons_hours: Optional[List[float]] = None,
        forecast_run_id: str = "FR-UNC-01"
    ) -> UncertaintyDecompositionResponse:
        if horizons_hours is None:
            horizons_hours = [3.0, 6.0, 12.0, 18.0, 24.0, 36.0, 48.0, 72.0]

        # Epistemic multiplier based on telemetry health
        epistemic_factor = 1.0 if data_confidence == "HIGH" else (1.8 if data_confidence == "MEDIUM" else 3.2)
        breakdowns: List[HorizonUncertaintyBreakdown] = []

        for h in horizons_hours:
            # Aleatoric grows with lead time (diffusion and chaos): ~ 0.005 * h^1.2
            var_aleatoric = 0.004 * (h ** 1.15)
            # Epistemic starts as baseline calibration error and widens slightly: ~ 0.008 * factor * sqrt(h)
            var_epistemic = 0.008 * epistemic_factor * (1.0 + 0.12 * math.sqrt(h))
            
            var_al = round(var_aleatoric, 4)
            var_ep = round(var_epistemic, 4)
            var_total = round(var_al + var_ep, 4)

            al_pct = round((var_al / max(1e-6, var_total)) * 100.0, 1)
            ep_pct = round((var_ep / max(1e-6, var_total)) * 100.0, 1)
            width = round(2.0 * 1.645 * math.sqrt(var_total), 3)

            breakdowns.append(HorizonUncertaintyBreakdown(
                lead_time_hours=h,
                total_variance=var_total,
                aleatoric_variance=var_al,
                epistemic_variance=var_ep,
                aleatoric_pct=al_pct,
                epistemic_pct=ep_pct,
                interval_width_90pct_m=width
            ))

        mean_al = round(sum(b.aleatoric_pct for b in breakdowns) / len(breakdowns), 1)
        mean_ep = round(sum(b.epistemic_pct for b in breakdowns) / len(breakdowns), 1)

        return UncertaintyDecompositionResponse(
            station_id=station_id,
            forecast_run_id=forecast_run_id,
            base_time=datetime.now(timezone.utc).isoformat(),
            data_confidence=data_confidence,
            model_confidence=model_confidence,
            mean_aleatoric_pct=mean_al,
            mean_epistemic_pct=mean_ep,
            horizons=breakdowns
        )

    @classmethod
    def compute_inundation_exceedance(
        cls,
        peak_river_stage_m: float,
        danger_threshold_m: float = 26.30,
        lead_time_hours: float = 18.0,
        forecast_run_id: str = "FR-INUND-EXC-01"
    ) -> InundationExceedanceSummary:
        """
        Computes probabilistic depth exceedance across 0.5m, 1.0m, and 2.0m thresholds.
        """
        surcharge = max(0.0, peak_river_stage_m - danger_threshold_m)
        
        # Continuous logistic sigmoid for depth exceedance
        p_05 = min(0.99, max(0.05, 1.0 / (1.0 + math.exp(-3.5 * (surcharge + 0.20)))))
        p_10 = min(0.95, max(0.02, 1.0 / (1.0 + math.exp(-3.0 * (surcharge - 0.15)))))
        p_20 = min(0.85, max(0.01, 1.0 / (1.0 + math.exp(-2.8 * (surcharge - 0.60)))))

        area_p50 = round(max(15.0, 120.0 * surcharge + 45.0), 1)
        area_p90 = round(area_p50 * 1.35, 1)

        return InundationExceedanceSummary(
            forecast_run_id=forecast_run_id,
            lead_time_hours=lead_time_hours,
            prob_exceed_0_5m_pct=round(p_05 * 100.0, 1),
            prob_exceed_1_0m_pct=round(p_10 * 100.0, 1),
            prob_exceed_2_0m_pct=round(p_20 * 100.0, 1),
            inundation_extent_sqkm_p50=area_p50,
            inundation_extent_sqkm_p90=area_p90
        )

# Global singleton instance
uncertainty_decomposer = UncertaintyDecomposer()
