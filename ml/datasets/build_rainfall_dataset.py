"""
Event-Isolated Sliding Window Rainfall Dataset Builder for JALDRISHTI AI.
Generates input-output sequence pairs for nowcasting models while strictly isolating event partitions.
"""

import os
import json
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

class RainfallDatasetBuilder:
    @staticmethod
    def build_event_sequences(
        df_timeseries: pd.DataFrame,
        event_id: str,
        input_window_steps: int = 4,   # e.g., 4 x 30min = 2 hours of history
        forecast_horizon_steps: int = 12 # e.g., 12 x 30min = 6 hours of nowcasting
    ) -> List[Dict[str, Any]]:
        """
        Creates sliding window samples strictly inside a single flood event window.
        Prevents timesteps from one event from bleeding across partition boundaries.
        """
        samples = []
        total_len = len(df_timeseries)
        required_len = input_window_steps + forecast_horizon_steps

        if total_len < required_len:
            return samples

        for i in range(0, total_len - required_len + 1):
            input_chunk = df_timeseries.iloc[i : i + input_window_steps]
            target_chunk = df_timeseries.iloc[i + input_window_steps : i + required_len]

            samples.append({
                "sample_id": f"{event_id}-SEQ-{i:04d}",
                "event_id": event_id,
                "input_start": str(input_chunk.iloc[0]["timestamp"]),
                "input_end": str(input_chunk.iloc[-1]["timestamp"]),
                "forecast_start": str(target_chunk.iloc[0]["timestamp"]),
                "forecast_end": str(target_chunk.iloc[-1]["timestamp"]),
                "input_rates": [float(r) for r in input_chunk["fused_precip_rate_mm_hr"]],
                "target_rates": [float(r) for r in target_chunk["fused_precip_rate_mm_hr"]],
                "max_target_rate": float(np.max(target_chunk["fused_precip_rate_mm_hr"]))
            })

        return samples
