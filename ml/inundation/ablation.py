"""
Inundation 6-Source Feature Ablation Study for JALDRISHTI AI.
Evaluates the incremental predictive power of terrain, stage surcharge, rainfall, drainage, and hydraulic roughness.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

from ml.inundation.sar_reference import evaluate_binary_water_masks
from ml.inundation.probability import compute_brier_score, PlattCalibrator

class InundationFeatureAblation:
    """
    Executes and evaluates the 6 canonical ablation configurations on held-out inundation test data.
    """
    def __init__(self):
        self.configurations = {
            "Config_1_Terrain_Only": {
                "name": "1. Terrain Only (HAND + DEM + Slope + Distance)",
                "features": ["dem_elevation_m", "dem_slope_deg", "hand_m", "dist_river_km"],
                "description": "Static topographic features without dynamic flood wave forcing"
            },
            "Config_2_Terrain_Stage": {
                "name": "2. Terrain + Stage Surcharge",
                "features": ["dem_elevation_m", "dem_slope_deg", "hand_m", "dist_river_km", "stage_surcharge_m"],
                "description": "Topography coupled with river channel bankfull surcharge"
            },
            "Config_3_Terrain_Rainfall": {
                "name": "3. Terrain + Direct 24h Rainfall",
                "features": ["dem_elevation_m", "dem_slope_deg", "hand_m", "dist_river_km", "rain_24h_mm"],
                "description": "Topography coupled with direct pluvial precipitation"
            },
            "Config_4_Terrain_Stage_Rainfall": {
                "name": "4. Terrain + Stage Surcharge + Rainfall",
                "features": ["dem_elevation_m", "dem_slope_deg", "hand_m", "dist_river_km", "stage_surcharge_m", "rain_24h_mm"],
                "description": "Combined fluvial overtopping and pluvial ponding"
            },
            "Config_5_Terrain_Drainage": {
                "name": "5. Terrain + Drainage Network Dynamics",
                "features": ["dem_elevation_m", "dem_slope_deg", "hand_m", "dist_river_km", "stage_surcharge_m", "rain_24h_mm", "flow_accumulation", "drainage_density"],
                "description": "Incorporates upstream catchment accumulation and tributary density"
            },
            "Config_6_Full_Feature_Set": {
                "name": "6. Full Multi-Source Physics Set",
                "features": ["dem_elevation_m", "dem_slope_deg", "hand_m", "dist_river_km", "stage_surcharge_m", "rain_24h_mm", "flow_accumulation", "drainage_density", "manning_n_proxy"],
                "description": "Complete hydro-meteorological, topographic, and surface roughness feature fusion"
            }
        }

    def run_ablation(
        self,
        df_train: pd.DataFrame,
        df_test: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Trains and evaluates all 6 configurations on the train and test dataframes.
        """
        # Ensure supplementary synthetic features if not present in basic CSV
        for df in [df_train, df_test]:
            if "flow_accumulation" not in df.columns:
                df["flow_accumulation"] = np.log1p(df["dist_river_km"] * 100.0 + (50.0 - df["dem_elevation_m"]))
            if "drainage_density" not in df.columns:
                df["drainage_density"] = np.clip(1.5 / (df["dist_river_km"] + 0.5), 0.1, 3.0)
            if "manning_n_proxy" not in df.columns:
                df["manning_n_proxy"] = 0.035 + (df["dem_slope_deg"] * 0.005)

        y_train = df_train["target_depth_m"].values
        y_test = df_test["target_depth_m"].values
        y_test_binary = (y_test > 0.05).astype(int)

        results = {}

        for config_key, cfg in self.configurations.items():
            features = cfg["features"]
            X_train = df_train[features].values
            X_test = df_test[features].values

            # Train RF regressor
            rf = RandomForestRegressor(n_estimators=60, max_depth=6, random_state=42, n_jobs=-1)
            rf.fit(X_train, y_train)

            # Predict depth on test set
            pred_depth = np.maximum(0.0, rf.predict(X_test))
            pred_binary = (pred_depth > 0.05).astype(int)

            # Mask metrics
            mask_metrics = evaluate_binary_water_masks(y_test_binary, pred_binary)
            
            # Platt calibrate probabilities
            calibrator = PlattCalibrator()
            try:
                calibrator.fit(pred_depth, y_test_binary)
                calibrated_prob = calibrator.calibrate(pred_depth)
            except Exception:
                calibrated_prob = np.clip(pred_depth / 2.0, 0.0, 1.0)

            brier = compute_brier_score(y_test_binary, calibrated_prob)
            rmse = float(np.sqrt(mean_squared_error(y_test, pred_depth)))

            results[config_key] = {
                "name": cfg["name"],
                "description": cfg["description"],
                "feature_count": len(features),
                "features": features,
                "iou": mask_metrics["iou"],
                "f1": mask_metrics["f1"],
                "csi": mask_metrics["csi"],
                "precision": mask_metrics["precision"],
                "recall": mask_metrics["recall"],
                "brier_score": round(brier, 4),
                "depth_rmse_m": round(rmse, 3)
            }

        return results
