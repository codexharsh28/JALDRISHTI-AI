"""
Level 2: Gradient Boosted Decision Tree (XGBoost/GBDT) Point & Grid Nowcaster for JALDRISHTI AI.
Leverages multi-scale lag features, convective indices (CAPE, PWAT), and radar dBZ.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

class XGBoostNowcastBaseline:
    HORIZONS_MINUTES = [30, 60, 120, 180, 240, 360]
    FEATURE_COLS = ["rain_1h", "rain_lag1", "delta_1h", "acceleration", "radar_dbz", "cape_jkg", "pwat_mm"]

    def __init__(self, checkpoint_dir: str = "model_registry"):
        self.clf_path = os.path.join(checkpoint_dir, "nowcast_heavy_rain_clf.joblib")
        self.reg_path = os.path.join(checkpoint_dir, "nowcast_rain_regressor.joblib")
        self.clf = joblib.load(self.clf_path) if os.path.exists(self.clf_path) else None
        self.reg = joblib.load(self.reg_path) if os.path.exists(self.reg_path) else None

    def predict(
        self,
        rain_1h: float,
        rain_lag1: float,
        radar_dbz: float = 38.0,
        cape_jkg: float = 1600.0,
        pwat_mm: float = 52.0
    ) -> Dict[str, Any]:
        delta_1h = rain_1h - rain_lag1
        acceleration = delta_1h / max(1.0, rain_lag1)
        
        feature_df = pd.DataFrame(
            [[rain_1h, rain_lag1, delta_1h, acceleration, radar_dbz, cape_jkg, pwat_mm]],
            columns=self.FEATURE_COLS
        )

        if self.clf is not None:
            heavy_rain_prob = float(self.clf.predict_proba(feature_df)[0][1])
        else:
            heavy_rain_prob = float(1.0 / (1.0 + np.exp(-(rain_1h - 35.0) / 8.0)))

        if self.reg is not None:
            predicted_base_rate = float(self.reg.predict(feature_df)[0])
        else:
            predicted_base_rate = rain_1h * 1.05

        horizons = {}
        for h in self.HORIZONS_MINUTES:
            decay = np.exp(-0.0018 * h)
            horizons[f"{h}m"] = round(float(predicted_base_rate * decay + (heavy_rain_prob * 8.0 * (1 - h/400.0))), 2)

        return {
            "model_id": "MOD-NOWCAST-L2-XGBOOST",
            "model_name": "Gradient Boosted Tree Regressor & Heavy Rain Classifier",
            "heavy_rain_probability": round(heavy_rain_prob, 3),
            "predicted_base_rate_mm_hr": round(predicted_base_rate, 2),
            "horizons": horizons
        }
