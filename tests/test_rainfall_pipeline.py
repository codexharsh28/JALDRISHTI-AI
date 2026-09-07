"""
Automated Test Suite for Phase 4 Real Historical Rainfall Data Pipeline & Nowcasting.
Tests source readiness, ingestion manifests, anti-leakage guards, QC rules,
gauge bias correction, multi-source fusion, and model hierarchy (L0, L1, L2, L3).
"""

import os
import pytest
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

from services.ingestion.source_readiness import SourceReadinessGate
from services.ingestion.rainfall_historical import RainfallHistoricalIngestManager
from services.fusion.rainfall_qc import RainfallQCEngine
from services.fusion.gauge_bias_correction import GaugeBiasCorrectionService
from services.fusion.rainfall_fusion_service import MultiSourceRainfallFusionEngine
from ml.datasets.build_rainfall_dataset import RainfallDatasetBuilder
from ml.rainfall.persistence import PersistenceNowcastBaseline
from ml.rainfall.advection import AdvectionFlowNowcastBaseline
from ml.rainfall.xgboost_nowcast import XGBoostNowcastBaseline
from ml.rainfall.spatiotemporal_nowcaster import SpatiotemporalConvLSTMNowcaster

def test_source_readiness_audit():
    readiness = SourceReadinessGate.audit_all_sources(raw_dir="data/raw/rainfall")
    assert "IMD_GRIDDED_025" in readiness
    assert "NASA_GPM_IMERG_EARLY" in readiness
    assert "PARADIP_DWR_RADAR" in readiness
    assert readiness["PARADIP_DWR_RADAR"]["state"] == "UNAVAILABLE"
    assert "RADAR_HISTORY_UNAVAILABLE" in readiness["PARADIP_DWR_RADAR"]["unavailability_reason"]

def test_rainfall_ingestion_and_checksum():
    mgr = RainfallHistoricalIngestManager(raw_dir="data/raw/rainfall")
    manifest = mgr.ingest_event_raw_datasets(
        event_id="EVT-MAHANADI-2022-08",
        start_time="2022-08-12T00:00:00Z",
        end_time="2022-08-20T23:59:59Z"
    )
    assert manifest["status"] == "INGESTION_COMPLETED"
    assert len(manifest["raw_files"]["imd_gridded"]["sha256"]) == 64
    assert len(manifest["raw_files"]["gpm_imerg"]["sha256"]) == 64

def test_rainfall_qc_deterministic_rules():
    # 1. Negative rain
    val, flag, _ = RainfallQCEngine.validate_rainfall_record(-5.0)
    assert flag.value == "BAD"
    assert val == 0.0

    # 2. Exceeds physical limit
    val, flag, _ = RainfallQCEngine.validate_rainfall_record(250.0, duration_minutes=60.0)
    assert flag.value == "BAD"
    assert val == 150.0

    # 3. Valid rainfall
    val, flag, _ = RainfallQCEngine.validate_rainfall_record(35.5)
    assert flag.value == "GOOD"
    assert val == 35.5

def test_gauge_bias_correction_isolation():
    corrector = GaugeBiasCorrectionService()
    assert corrector.calibrated_parameters["calibration_status"] == "CALIBRATED_ISOLATED"
    assert "EVT-MAHANADI-2020-08" in corrector.calibrated_parameters["training_partition_events"]
    assert "EVT-MAHANADI-2022-08" not in corrector.calibrated_parameters["training_partition_events"]
    
    corrected_radar = corrector.apply_radar_bias_correction(20.0)
    assert corrected_radar == 20.0 * 1.08

def test_multi_source_fusion_fault_tolerance():
    engine = MultiSourceRainfallFusionEngine()

    # All active
    res_full = engine.fuse_rainfall_sources(
        radar_val=30.0,
        gauge_val=32.0,
        insat_val=28.0,
        imerg_val=26.0,
        nwp_val=25.0
    )
    assert res_full["data_confidence"] == "HIGH"
    assert res_full["active_sources_count"] == 5
    assert res_full["fused_rainfall_mm_hr"] > 0

    # Radar disconnected (graceful fallback)
    res_no_radar = engine.fuse_rainfall_sources(
        radar_val=None,
        gauge_val=32.0,
        insat_val=28.0,
        imerg_val=26.0,
        nwp_val=25.0
    )
    assert res_no_radar["data_confidence"] == "MEDIUM"
    assert "radar" not in res_no_radar["source_weights"]
    assert sum(res_no_radar["source_weights"].values()) == pytest.approx(1.0, 0.01)

def test_event_sliding_window_dataset_isolation():
    dates = pd.date_range("2022-08-15 00:00", "2022-08-16 12:00", freq="30min")
    df_test = pd.DataFrame({
        "timestamp": [d.isoformat() for d in dates],
        "fused_precip_rate_mm_hr": [10.0 + (i % 5) * 2.0 for i in range(len(dates))]
    })

    samples = RainfallDatasetBuilder.build_event_sequences(
        df_timeseries=df_test,
        event_id="EVT-MAHANADI-2022-08",
        input_window_steps=4,
        forecast_horizon_steps=12
    )
    assert len(samples) > 0
    assert samples[0]["event_id"] == "EVT-MAHANADI-2022-08"
    assert len(samples[0]["input_rates"]) == 4
    assert len(samples[0]["target_rates"]) == 12

def test_model_hierarchy_predictions():
    # L0 Persistence
    p_res = PersistenceNowcastBaseline.predict(latest_observed_rate_mm_hr=25.0)
    assert p_res["30m"] == 25.0
    assert p_res["360m"] == 25.0

    # L1 Advection
    a_res = AdvectionFlowNowcastBaseline.predict([18.0, 22.0, 26.0, 30.0])
    assert "motion_vector" in a_res
    assert a_res["horizons"]["30m"] > 0

    # L2 XGBoost
    xgb = XGBoostNowcastBaseline()
    x_res = xgb.predict(rain_1h=32.0, rain_lag1=25.0)
    assert "heavy_rain_probability" in x_res
    assert x_res["horizons"]["60m"] > 0

    # L3 ConvLSTM
    deep = SpatiotemporalConvLSTMNowcaster()
    d_res = deep.predict_multi_horizon([15.0, 20.0, 28.0, 35.0], radar_available=True)
    assert d_res["horizons"]["60m"]["p50_fused_rate_mm_hr"] > 0
    assert d_res["horizons"]["60m"]["p10_lower_bound_mm_hr"] <= d_res["horizons"]["60m"]["p50_fused_rate_mm_hr"]
    assert d_res["horizons"]["60m"]["p90_upper_bound_mm_hr"] >= d_res["horizons"]["60m"]["p50_fused_rate_mm_hr"]
