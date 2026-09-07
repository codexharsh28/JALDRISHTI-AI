"""
Anti-Leakage and Historical Hindcasting Test Suite for JALDRISHTI AI.
Tests information cutoff enforcement, baseline progression, event isolation,
and historical data ingestion manifest generation.
"""

import os
import pytest
from datetime import datetime, timezone, timedelta

from services.ingestion.historical_ingest import (
    InformationAvailabilityRecord,
    HistoricalDataIngestionManager
)
from services.hindcast.hindcast_engine import HindcastEngine

def test_information_availability_cutoff_anti_leakage():
    cutoff_time = datetime(2022, 8, 15, 12, 0, tzinfo=timezone.utc)

    # 1. Past observation, published before cutoff -> MUST BE VISIBLE
    rec_past_published = InformationAvailabilityRecord(
        source_id="IMD_AWS",
        dataset_state="REAL_HISTORICAL_ANALYSIS",
        observation_time=cutoff_time - timedelta(hours=2),
        publication_latency_minutes=30.0,  # Published at cutoff - 1.5h
        valid_time=cutoff_time - timedelta(hours=2),
        data_payload={"rainfall_mm": 18.5}
    )
    assert rec_past_published.is_available_at(cutoff_time) is True

    # 2. Observed before cutoff, but published AFTER cutoff -> MUST BE SUPPRESSED (NO LEAKAGE)
    rec_past_delayed_publish = InformationAvailabilityRecord(
        source_id="NASA_IMERG_FINAL",
        dataset_state="REAL_HISTORICAL_ANALYSIS",
        observation_time=cutoff_time - timedelta(hours=1),
        publication_latency_minutes=7200.0,  # Published days later
        valid_time=cutoff_time - timedelta(hours=1),
        data_payload={"rainfall_mm": 35.0}
    )
    assert rec_past_delayed_publish.is_available_at(cutoff_time) is False

    # 3. Future observation -> MUST BE SUPPRESSED
    rec_future = InformationAvailabilityRecord(
        source_id="CWC_GAUGE",
        dataset_state="REAL_HISTORICAL_ANALYSIS",
        observation_time=cutoff_time + timedelta(hours=6),
        publication_latency_minutes=15.0,
        valid_time=cutoff_time + timedelta(hours=6),
        data_payload={"rainfall_mm": 50.0}
    )
    assert rec_future.is_available_at(cutoff_time) is False

def test_historical_hindcast_execution_and_progression():
    engine = HindcastEngine(basin_id="pilot-mahanadi-delta")
    cutoff = datetime(2022, 8, 15, 6, 0, tzinfo=timezone.utc)

    records = [
        InformationAvailabilityRecord(
            source_id="IMD_AWS",
            dataset_state="REAL_HISTORICAL_ANALYSIS",
            observation_time=cutoff - timedelta(hours=h),
            publication_latency_minutes=30.0,
            valid_time=cutoff - timedelta(hours=h),
            data_payload={"rainfall_mm": 15.0 + h * 0.5}
        )
        for h in range(1, 25)
    ]

    result = engine.execute_event_hindcast(
        event_id="EVT-MAHANADI-2022-08",
        cutoff_time=cutoff,
        historical_records=records,
        danger_stage_m=26.41
    )

    assert result["hindcast_run_id"].startswith("HINDCAST-EVT-MAHANADI-2022-08")
    assert result["information_cutoff_enforced"] is True
    assert result["dataset_state"] == "REAL_HISTORICAL_HINDCAST"
    assert "L0_PERSISTENCE" in result["models_evaluated"]
    assert "L1_XGBOOST" in result["models_evaluated"]
    assert "L2_LSTM_RIVER_GRAPH" in result["models_evaluated"]
    assert result["peak_predicted_stage_m"] > 0
    assert len(result["forecast_horizons"]) == 7

def test_historical_ingestion_manifest_generation():
    manager = HistoricalDataIngestionManager(cache_dir="data/historical")
    out_file, sha, manifest = manager.ingest_imd_gridded_historical_event(
        event_id="EVT-MAHANADI-2020-08",
        start_date="2020-08-25",
        end_date="2020-08-31"
    )

    assert os.path.exists(out_file)
    assert len(sha) == 64
    assert manifest["dataset_id"] == "IMD-025-GRIDDED-EVT-MAHANADI-2020-08"
    assert manifest["dataset_state"] == "REAL_HISTORICAL_ANALYSIS"
    assert manifest["records_count"] > 0
