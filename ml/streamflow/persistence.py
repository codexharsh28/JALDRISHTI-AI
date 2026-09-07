"""
Level 0: Persistence / Auto-Regressive Streamflow Baseline.
Predicts future river stage and discharge by holding current state or projecting 3h linear trend.
"""

import numpy as np
from typing import Dict, Any, List

class PersistenceStreamflowBaseline:
    def __init__(self, mode: str = "trend_extrapolation"):
        self.mode = mode
        self.model_id = "STREAMFLOW_L0_PERSISTENCE"
        self.version = "v1.0.0"

    def predict_multi_horizon(
        self,
        current_stage_m: float,
        rate_of_rise_m_hr: float,
        current_discharge_cumec: float,
        horizons_hours: List[int] = [1, 3, 6, 12, 24, 48, 72]
    ) -> Dict[str, Any]:
        """Projects stage and discharge across multiple lead times."""
        stage_preds = []
        discharge_preds = []

        for h in horizons_hours:
            if self.mode == "trend_extrapolation":
                # Dampen rate of rise over long horizons
                damping = np.exp(-0.04 * h)
                stage_h = current_stage_m + (rate_of_rise_m_hr * h * damping)
                discharge_h = current_discharge_cumec + (rate_of_rise_m_hr * 450.0 * h * damping)
            else:
                # Flat persistence
                stage_h = current_stage_m
                discharge_h = current_discharge_cumec

            stage_preds.append(round(float(np.clip(stage_h, 15.0, 30.0)), 2))
            discharge_preds.append(round(float(np.clip(discharge_h, 500.0, 50000.0)), 1))

        # Rule-based uncertainty expansion for persistence
        p10_stages = [round(s - (0.08 * np.sqrt(h)), 2) for s, h in zip(stage_preds, horizons_hours)]
        p90_stages = [round(s + (0.12 * np.sqrt(h)), 2) for s, h in zip(stage_preds, horizons_hours)]

        return {
            "model_id": self.model_id,
            "version": self.version,
            "horizons_hours": horizons_hours,
            "stage_p50": stage_preds,
            "stage_p10": p10_stages,
            "stage_p90": p90_stages,
            "discharge_p50": discharge_preds,
            "uncertainty_method": "RULE_BASED_UNCERTAINTY"
        }
