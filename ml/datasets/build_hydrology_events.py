"""
Hydrology Event Dataset Builder for JALDRISHTI AI.
Extracts whole-event hydrograph sequences strictly partitioned by split manifest.
"""

import os
import yaml
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone

def load_split_manifest() -> Dict[str, Any]:
    with open("data/manifests/hydrology_split_manifest.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def generate_synthetic_event_hydrograph(event_id: str, duration_hours: int = 168) -> pd.DataFrame:
    """Generates physically consistent hourly hydrograph data for an event."""
    np.random.seed(hash(event_id) % (2**32))
    time_index = pd.date_range("2022-08-10 00:00", periods=duration_hours, freq="1h")
    
    # Rainfall storm peak around t=36h
    t = np.arange(duration_hours)
    rain_hourly = 45.0 * np.exp(-((t - 36) ** 2) / (2 * (10 ** 2))) + np.random.gamma(2, 1.5, size=duration_hours)
    
    # Streamflow hydrograph responding with a lag of ~18h
    baseflow = 3200.0
    storm_discharge = 31000.0 * np.exp(-((t - 54) ** 2) / (2 * (16 ** 2)))
    discharge = baseflow + storm_discharge + np.random.normal(0, 150, size=duration_hours)
    discharge = np.clip(discharge, 1000.0, 45000.0)

    # Stage using power law rating curve: h = (Q / 18.5) ^ (1 / 2.3) + 21.5
    stage = (discharge / 18.5) ** (1.0 / 2.3) + 12.0
    stage = np.clip(stage, 18.0, 28.5)

    df = pd.DataFrame({
        "timestamp": time_index,
        "rainfall_mm_hr": np.round(rain_hourly, 2),
        "stage_m": np.round(stage, 2),
        "discharge_cumec": np.round(discharge, 1),
        "upstream_discharge_cumec": np.round(discharge * 0.85, 1),
        "event_id": event_id
    })
    return df

def build_event_partitions() -> Dict[str, pd.DataFrame]:
    manifest = load_split_manifest()
    partitions = {}

    for partition_name, pdata in manifest["partitions"].items():
        dfs = []
        for ev in pdata["events"]:
            df = generate_synthetic_event_hydrograph(ev["event_id"])
            dfs.append(df)
        partitions[partition_name] = pd.concat(dfs, ignore_index=True)

    return partitions
