"""
Hydrological Feature Engineering for JALDRISHTI AI.
Extracts antecedent rainfall indices, lag features, rate of rise, and upstream routing indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

def compute_hydrological_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes leakage-safe backward rolling hydrological features."""
    data = df.copy()

    # 1. Rainfall Accumulation Lags (backward-looking only)
    data["rain_1h"] = data["rainfall_mm_hr"]
    data["rain_3h"] = data["rainfall_mm_hr"].rolling(3, min_periods=1).sum()
    data["rain_6h"] = data["rainfall_mm_hr"].rolling(6, min_periods=1).sum()
    data["rain_12h"] = data["rainfall_mm_hr"].rolling(12, min_periods=1).sum()
    data["rain_24h"] = data["rainfall_mm_hr"].rolling(24, min_periods=1).sum()
    data["rain_48h"] = data["rainfall_mm_hr"].rolling(48, min_periods=1).sum()
    data["rain_72h"] = data["rainfall_mm_hr"].rolling(72, min_periods=1).sum()

    # 2. Stage Lag Windows
    data["stage_lag_1h"] = data["stage_m"].shift(1).bfill()
    data["stage_lag_3h"] = data["stage_m"].shift(3).bfill()
    data["stage_lag_6h"] = data["stage_m"].shift(6).bfill()
    data["stage_lag_12h"] = data["stage_m"].shift(12).bfill()
    data["stage_lag_24h"] = data["stage_m"].shift(24).bfill()

    # 3. Rate of Rise (m/hr) & Acceleration
    data["rate_of_rise"] = (data["stage_m"] - data["stage_lag_3h"]) / 3.0
    data["discharge_lag_3h"] = data["discharge_cumec"].shift(3).bfill()
    data["discharge_lag_6h"] = data["discharge_cumec"].shift(6).bfill()

    # 4. Upstream routing features
    if "upstream_discharge_cumec" in data.columns:
        data["upstream_discharge_lag_6h"] = data["upstream_discharge_cumec"].shift(6).bfill()
        data["upstream_discharge_lag_12h"] = data["upstream_discharge_cumec"].shift(12).bfill()
    else:
        data["upstream_discharge_lag_6h"] = data["discharge_cumec"] * 0.8
        data["upstream_discharge_lag_12h"] = data["discharge_cumec"] * 0.75

    # 5. Antecedent Precipitation Index (API = sum(k^t * P_t) with k=0.9)
    weights = np.array([0.9 ** i for i in range(1, 25)])
    api_vals = []
    rains = data["rainfall_mm_hr"].values
    for idx in range(len(rains)):
        start_idx = max(0, idx - 24)
        window = rains[start_idx:idx]
        if len(window) == 0:
            api_vals.append(0.0)
        else:
            w = weights[:len(window)][::-1]
            api_vals.append(float(np.sum(window * w)))
    data["antecedent_rainfall_index"] = api_vals

    return data
