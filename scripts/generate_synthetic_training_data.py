"""
Causal Synthetic Hydrometeorological Training Dataset Generator for JALDRISHTI AI.
Generates physically consistent, causally coupled training and validation sets
for rainfall nowcasting, streamflow forecasting, and inundation depth prediction.
"""

import os
import numpy as np
import pandas as pd

def generate_causal_datasets():
    os.makedirs("data/simulation", exist_ok=True)
    np.random.seed(42)  # Deterministic seed for reproducible ML training

    # =========================================================================
    # 1. RAINFALL NOWCASTING TRAINING DATASET (Storm Cells & Convective Dynamics)
    # =========================================================================
    n_samples = 2500
    # Features: current rain rate, 1h lag, 3h lag, delta_1h, acceleration, radar MaxZ, CAPE, PWAT
    rain_1h = np.random.exponential(scale=12.0, size=n_samples)
    rain_lag1 = rain_1h * np.random.uniform(0.7, 1.3, size=n_samples)
    delta_1h = rain_1h - rain_lag1
    accel = delta_1h * np.random.uniform(-0.5, 0.8, size=n_samples)
    
    # Physics: radar reflectivity dBZ correlated with rain via Marshall-Palmer: dBZ ~ 10*log10(200 * R^1.6)
    radar_dbz = np.clip(10.0 * np.log10(200.0 * np.maximum(rain_1h, 0.1)**1.6) + np.random.normal(0, 2, size=n_samples), 10.0, 58.0)
    cape = np.random.uniform(800.0, 3200.0, size=n_samples)
    pwat = np.random.uniform(35.0, 75.0, size=n_samples)
    
    # Causal Target: Future rain rate at +1h and +3h
    # Strong convective burst if CAPE > 2000 and delta_1h > 5
    convective_boost = np.where((cape > 2000.0) & (delta_1h > 5.0), 1.5, 0.85)
    target_rain_1h = np.maximum(0.0, (rain_1h + 0.8 * delta_1h + 0.3 * accel) * convective_boost + np.random.normal(0, 2, size=n_samples))
    target_heavy_rain = (target_rain_1h >= 35.0).astype(int)

    df_rainfall = pd.DataFrame({
        "rain_1h": rain_1h.round(2),
        "rain_lag1": rain_lag1.round(2),
        "delta_1h": delta_1h.round(2),
        "acceleration": accel.round(2),
        "radar_dbz": radar_dbz.round(1),
        "cape_jkg": cape.round(0),
        "pwat_mm": pwat.round(1),
        "target_rain_1h": target_rain_1h.round(2),
        "target_heavy_rain": target_heavy_rain
    })

    # Split 80% train / 20% val
    train_idx = int(0.8 * n_samples)
    df_rainfall.iloc[:train_idx].to_csv("data/simulation/rainfall_events_train.csv", index=False)
    df_rainfall.iloc[train_idx:].to_csv("data/simulation/rainfall_events_val.csv", index=False)

    # =========================================================================
    # 2. HYDROLOGICAL STREAMFLOW DATASET (Catchment Runoff & River Routing)
    # =========================================================================
    # Causal chain: 6h/24h rain + soil saturation -> runoff -> river stage rise after lag
    rain_6h = np.random.exponential(scale=35.0, size=n_samples)
    rain_24h = rain_6h * np.random.uniform(1.8, 3.5, size=n_samples)
    soil_sat = np.clip(0.4 + (rain_24h / 250.0) + np.random.normal(0, 0.05, size=n_samples), 0.2, 0.98)
    
    current_stage = np.random.uniform(20.0, 25.0, size=n_samples)
    stage_lag_3h = current_stage - np.random.uniform(-0.5, 0.8, size=n_samples)
    rate_of_rise = (current_stage - stage_lag_3h) / 3.0
    upstream_discharge = np.clip(12000.0 + (rain_24h * 65.0 * soil_sat) + np.random.normal(0, 500, size=n_samples), 4000.0, 32000.0)

    # Causal Target: Peak stage surge in next 12h-24h
    stage_surge = (rain_6h * 0.022 + rain_24h * 0.008 + rate_of_rise * 3.2) * soil_sat
    target_peak_stage_24h = current_stage + stage_surge + np.random.normal(0, 0.15, size=n_samples)

    df_hydro = pd.DataFrame({
        "rain_6h": rain_6h.round(2),
        "rain_24h": rain_24h.round(2),
        "soil_saturation": soil_sat.round(3),
        "current_stage_m": current_stage.round(2),
        "stage_lag_3h_m": stage_lag_3h.round(2),
        "rate_of_rise_m_hr": rate_of_rise.round(3),
        "upstream_discharge_cumec": upstream_discharge.round(1),
        "target_peak_stage_24h": target_peak_stage_24h.round(2)
    })

    df_hydro.iloc[:train_idx].to_csv("data/simulation/hydrograph_events_train.csv", index=False)
    df_hydro.iloc[train_idx:].to_csv("data/simulation/hydrograph_events_val.csv", index=False)

    # =========================================================================
    # 3. 2D INUNDATION DEPTH DATASET (Topographic Surcharge & HAND Features)
    # =========================================================================
    # Features: river stage surcharge above bankfull, DEM elevation, slope, HAND index, dist to river
    stage_surcharge = np.random.uniform(0.0, 3.5, size=n_samples)
    dem_elevation = np.random.uniform(2.0, 45.0, size=n_samples)
    dem_slope_deg = np.random.uniform(0.2, 5.0, size=n_samples)
    hand_m = np.random.uniform(0.2, 15.0, size=n_samples)
    dist_river_km = np.random.uniform(0.1, 15.0, size=n_samples)

    # Causal Target: Inundation flood depth in meters
    water_surface = stage_surcharge * 1.5 + (rain_24h / 100.0) * 0.4
    raw_depth = np.maximum(0.0, water_surface - hand_m * 0.35 - (dem_slope_deg * 0.2))
    target_depth_m = np.where(dist_river_km < 8.0, raw_depth, 0.0)
    target_depth_m = np.clip(target_depth_m + np.random.normal(0, 0.05, size=n_samples), 0.0, 4.5)

    df_inund = pd.DataFrame({
        "stage_surcharge_m": stage_surcharge.round(2),
        "dem_elevation_m": dem_elevation.round(2),
        "dem_slope_deg": dem_slope_deg.round(2),
        "hand_m": hand_m.round(2),
        "dist_river_km": dist_river_km.round(2),
        "rain_24h_mm": rain_24h.round(2),
        "target_depth_m": target_depth_m.round(2)
    })

    df_inund.iloc[:train_idx].to_csv("data/simulation/inundation_samples_train.csv", index=False)
    df_inund.iloc[train_idx:].to_csv("data/simulation/inundation_samples_val.csv", index=False)

    print("Causal synthetic training and validation datasets successfully generated in data/simulation/")

if __name__ == "__main__":
    generate_causal_datasets()
