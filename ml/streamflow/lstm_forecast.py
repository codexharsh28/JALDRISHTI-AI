"""
Level 2: Analytical Hydrograph Surrogate Multi-Horizon Predictor.
Processes 24-hour historical input sequence (rainfall, stages, discharge)
and outputs a 72-hour hydrograph with parameterized Gaussian peak timing and spread.

NOTE ON SCIENTIFIC INTEGRITY: This model implements stage surcharge estimation via
parameterized Gaussian pulse response and logarithmic spread functions.
This is a physics-informed analytical surrogate, NOT an LSTM, GRU, or recurrent neural network.
"""

import numpy as np
from typing import Dict, Any, List

class AnalyticalHydrographSurrogate:
    def __init__(self, surrogate_type: str = "GAUSSIAN_SURCHARGE"):
        self.model_id = "STREAMFLOW_L2_ANALYTICAL_HYDROGRAPH"
        self.version = "v3.0.0"
        self.surrogate_type = surrogate_type
        self.horizons_hours = [1, 3, 6, 12, 24, 48, 72]

    def predict_sequence(
        self,
        historical_sequence: List[Dict[str, float]],
        nwp_forecast_rain: List[float]
    ) -> Dict[str, Any]:
        """
        Input: 24-hour sequence of historical dicts:
        {"rain_mm": ..., "stage_m": ..., "discharge_cumec": ..., "upstream_q": ...}
        """
        if not historical_sequence:
            curr_stage = 25.5
            curr_discharge = 8200.0
        else:
            curr_stage = historical_sequence[-1].get("stage_m", 25.5)
            curr_discharge = historical_sequence[-1].get("discharge_cumec", 8200.0)

        # Antecedent cumulative rain in last 24h
        accum_24h = sum(step.get("rain_mm", 0.0) for step in historical_sequence) if historical_sequence else 120.0
        
        # Temporal hydrograph projection
        stage_p50, stage_p10, stage_p90 = [], [], []
        discharge_p50, discharge_p10, discharge_p90 = [], [], []

        for h in self.horizons_hours:
            # Surcharge pulse response
            pulse = np.exp(-((h - 19.5) ** 2) / (2 * (12.0 ** 2)))
            delta_stage = (accum_24h * 0.0115 * pulse) + (curr_stage * 0.005 * np.sin(h / 24.0))

            p50 = curr_stage + delta_stage
            # Analytical parametric spread
            spread = 0.12 + 0.045 * np.sqrt(h)

            p10 = p50 - spread * 0.9
            p90 = p50 + spread * 1.1

            stage_p50.append(round(float(p50), 2))
            stage_p10.append(round(float(p10), 2))
            stage_p90.append(round(float(p90), 2))

            q_p50 = (max(0.1, p50 - 12.0) ** 2.3) * 18.5
            q_p10 = (max(0.1, p10 - 12.0) ** 2.3) * 18.5
            q_p90 = (max(0.1, p90 - 12.0) ** 2.3) * 18.5

            discharge_p50.append(round(float(q_p50), 1))
            discharge_p10.append(round(float(q_p10), 1))
            discharge_p90.append(round(float(q_p90), 1))

        return {
            "model_id": self.model_id,
            "version": self.version,
            "surrogate_type": self.surrogate_type,
            "horizons_hours": self.horizons_hours,
            "stage_p50": stage_p50,
            "stage_p10": stage_p10,
            "stage_p90": stage_p90,
            "discharge_p50": discharge_p50,
            "discharge_p10": discharge_p10,
            "discharge_p90": discharge_p90,
            "uncertainty_method": "ANALYTICAL_PARAMETRIC_SPREAD"
        }

# Alias for backward compatibility during migration
SequenceLSTMStreamflowModel = AnalyticalHydrographSurrogate
