"""
Automated Unit & Integration Tests for Phase 8 Scientific Amendments to Inundation Subsystem.
Verifies all 14 scientific amendments:
1. Candidate status lifecycle & promotion gating.
2. Sentinel-1 SAR Flood Reference naming & temporal mismatch detection.
3. Extent metrics vs depth model estimate decoupling.
4. Class imbalance tracking & raw unmanipulated test distribution.
5. Temporal leakage guard enforcement (t > T rejection).
6. Spatial leakage guard enforcement across train/val/test splits.
7. Probabilistic calibration (Platt scaling, ECE, Brier score, Reliability diagrams).
8. Multi-model baseline comparison execution.
9. 9-point scientific provenance retention.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

from services.models import (
    ModelStatus,
    DepthStatus,
    DepthValidationStatus,
    TemporalMatchStatus,
    InundationTileSummary,
    InundationProvenance,
    SARReferenceComparison
)
from ml.inundation.models import (
    TerrainThresholdBaseline,
    PhysicsInformedPlanarBaseline,
    RandomForestInundationSurrogate,
    AnalyticalSpatialSurrogate,
    DeepSpatialSurrogate
)
from ml.inundation.probability import (
    PlattCalibrator,
    IsotonicCalibrator,
    compute_brier_score,
    compute_expected_calibration_error,
    compute_reliability_diagram
)
from ml.inundation.leakage import (
    TemporalLeakageGuard,
    SpatialLeakageGuard
)
from ml.inundation.sar_reference import (
    validate_sar_temporal_window,
    evaluate_sar_flood_reference,
    evaluate_binary_water_masks
)
from ml.inundation.promotion import InundationPromotionEngine
from services.inundation.service import InundationService

# -----------------------------------------------------------------------------
# Test 1: Candidate Status Lifecycle & Promotion Rule Enforcement
# -----------------------------------------------------------------------------
def test_candidate_status_by_default_and_promotion_gating():
    rf_model = RandomForestSurrogate = RandomForestInundationSurrogate()
    assert rf_model.model_status == ModelStatus.CANDIDATE

    deep_model = DeepSpatialSurrogate()
    assert deep_model.model_status == ModelStatus.CANDIDATE

    promotion_engine = InundationPromotionEngine(
        min_iou_threshold=0.75,
        min_f1_threshold=0.80,
        max_brier_score=0.15,
        required_baseline_iou_margin=0.10
    )

    clean_guard = SpatialLeakageGuard(
        train_events=["EVT-2020-08"],
        val_events=["EVT-2021-09"],
        test_events=["EVT-2022-08", "EVT-2024-08"]
    )

    # Sub-par candidate metrics should FAIL promotion
    failing_metrics = {"iou": 0.65, "f1": 0.72, "brier_score": 0.22}
    baseline_metrics = {"iou": 0.58, "f1": 0.68, "brier_score": 0.20}
    verdict = promotion_engine.evaluate_candidate_for_promotion(
        candidate_model=rf_model,
        candidate_metrics=failing_metrics,
        baseline_metrics=baseline_metrics,
        split_guard=clean_guard
    )
    assert verdict["promotion_granted"] is False
    assert rf_model.model_status == ModelStatus.CANDIDATE

    # Superior candidate metrics should PASS promotion
    passing_metrics = {"iou": 0.82, "f1": 0.87, "brier_score": 0.07}
    verdict = promotion_engine.evaluate_candidate_for_promotion(
        candidate_model=rf_model,
        candidate_metrics=passing_metrics,
        baseline_metrics=baseline_metrics,
        split_guard=clean_guard
    )
    assert verdict["promotion_granted"] is True
    assert rf_model.model_status == ModelStatus.BEST_VALIDATED_MODEL
    assert verdict["resulting_status"] == ModelStatus.BEST_VALIDATED_MODEL.value

# -----------------------------------------------------------------------------
# Test 2: SAR Flood Reference Naming & Temporal Mismatch Detection
# -----------------------------------------------------------------------------
def test_sar_flood_reference_naming_and_temporal_mismatch():
    t_fcst = datetime(2022, 8, 17, 18, 0, tzinfo=timezone.utc)
    
    # 1. Matched SAR pass (within 3 hours)
    t_sar_matched = datetime(2022, 8, 17, 18, 4, tzinfo=timezone.utc)
    diff_h, status = validate_sar_temporal_window(t_fcst, t_sar_matched, max_tolerance_hours=3.0)
    assert status == TemporalMatchStatus.MATCHED
    assert diff_h < 0.1

    # 2. Exceeded tolerance pass (between 3 and 12 hours)
    t_sar_lag = datetime(2022, 8, 17, 23, 30, tzinfo=timezone.utc)
    diff_h, status = validate_sar_temporal_window(t_fcst, t_sar_lag, max_tolerance_hours=3.0)
    assert status == TemporalMatchStatus.MISMATCH_TOLERANCE_EXCEEDED
    assert round(diff_h, 1) == 5.5

    # 3. Rejected mismatch pass (over 12 hours)
    t_sar_rejected = datetime(2022, 8, 18, 12, 0, tzinfo=timezone.utc)
    diff_h, status = validate_sar_temporal_window(t_fcst, t_sar_rejected, max_tolerance_hours=3.0)
    assert status == TemporalMatchStatus.REJECTED
    assert diff_h == 18.0

# -----------------------------------------------------------------------------
# Test 3: Extent Metrics Validation & Prohibition of Deceptive Depth Accuracy
# -----------------------------------------------------------------------------
def test_extent_metrics_and_depth_validation_unavailable():
    metrics = evaluate_sar_flood_reference(observed_extent_sqkm=184.6, predicted_extent_sqkm=178.5)
    assert "iou" in metrics
    assert "f1" in metrics
    assert "csi" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert 0.70 <= metrics["iou"] <= 1.0

    # Test that InundationTileSummary enforces DepthStatus.MODEL_ESTIMATE and UNAVAILABLE
    service = InundationService()
    now = datetime(2024, 8, 5, 6, 0, tzinfo=timezone.utc)
    res = service.generate_inundation_forecast(
        peak_river_stage_m=26.85,
        danger_level_m=26.41,
        rainfall_accumulation_24h_mm=165.0,
        forecast_valid_time=now,
        lead_time_hours=12.0
    )
    assert res.depth_status == DepthStatus.MODEL_ESTIMATE
    assert res.depth_validation == DepthValidationStatus.UNAVAILABLE
    assert res.model_status == ModelStatus.CANDIDATE

# -----------------------------------------------------------------------------
# Test 4: Class Imbalance Reporting & Raw Distribution Integrity
# -----------------------------------------------------------------------------
def test_class_imbalance_reporting():
    from ml.inundation.train import log_class_imbalance
    
    # 100 cells with 15 flooded (15% positive prevalence)
    y_synth = np.array([1.2] * 15 + [0.0] * 85)
    stats = log_class_imbalance(y_synth, "TestSplit")
    assert stats["total_samples"] == 100
    assert stats["flooded_cells_positive"] == 15
    assert stats["dry_cells_negative"] == 85
    assert stats["flood_prevalence_pct"] == 15.0
    assert stats["imbalance_ratio"] == 5.67

# -----------------------------------------------------------------------------
# Test 5: Temporal Leakage Guard (Rejects Future Data t > T)
# -----------------------------------------------------------------------------
def test_temporal_leakage_guard_rejects_future_timestamps():
    cutoff = datetime(2022, 8, 16, 12, 0, tzinfo=timezone.utc)
    guard = TemporalLeakageGuard(forecast_cutoff_time=cutoff)

    records = [
        {"timestamp": "2022-08-16T06:00:00Z", "stage_surcharge_m": 2.1},
        {"timestamp": "2022-08-16T12:00:00Z", "stage_surcharge_m": 2.5},
        # Future contaminated record
        {"timestamp": "2022-08-16T18:00:00Z", "stage_surcharge_m": 3.4}
    ]

    filtered = guard.filter_records(records)
    assert len(filtered) == 2
    assert all(r["stage_surcharge_m"] <= 2.5 for r in filtered)

    # Direct timestamp check
    is_clean, violations = guard.verify_no_future_data([
        datetime(2022, 8, 16, 10, 0, tzinfo=timezone.utc),
        datetime(2022, 8, 16, 14, 0, tzinfo=timezone.utc)
    ])
    assert is_clean is False
    assert len(violations) == 1

# -----------------------------------------------------------------------------
# Test 6: Spatial Leakage Guard (Disjoint Event Splitting)
# -----------------------------------------------------------------------------
def test_spatial_leakage_guard_event_isolation():
    clean_guard = SpatialLeakageGuard(
        train_events=["EVT-MAHANADI-2020-08", "EVT-MAHANADI-2023-07"],
        val_events=["EVT-MAHANADI-2021-09"],
        test_events=["EVT-MAHANADI-2022-08", "EVT-MAHANADI-2024-08"]
    )
    assert clean_guard.verify_disjoint_partitions()["is_valid"] is True

    contaminated_guard = SpatialLeakageGuard(
        train_events=["EVT-MAHANADI-2020-08", "EVT-MAHANADI-2022-08"],
        val_events=["EVT-MAHANADI-2021-09"],
        test_events=["EVT-MAHANADI-2022-08"] # Leaked into train & test!
    )
    res = contaminated_guard.verify_disjoint_partitions()
    assert res["is_valid"] is False
    assert "EVT-MAHANADI-2022-08" in res["train_test_overlap"]

# -----------------------------------------------------------------------------
# Test 7: Probabilistic Calibration & Brier Score Evaluation
# -----------------------------------------------------------------------------
def test_probabilistic_calibration_and_brier_score():
    np.random.seed(42)
    # Generate uncalibrated logits and true labels
    raw_depth = np.random.uniform(0.0, 3.0, size=200)
    true_binary = (raw_depth > 1.0).astype(int)

    calibrator = PlattCalibrator()
    calibrator.fit(raw_depth, true_binary)
    calibrated_probs = calibrator.calibrate(raw_depth)

    assert calibrated_probs.shape == (200,)
    assert np.all((calibrated_probs >= 0.0) & (calibrated_probs <= 1.0))

    brier = compute_brier_score(true_binary, calibrated_probs)
    assert 0.0 <= brier <= 0.25

    ece = compute_expected_calibration_error(true_binary, calibrated_probs, n_bins=10)
    assert 0.0 <= ece <= 0.20

    diag = compute_reliability_diagram(true_binary, calibrated_probs, n_bins=5)
    assert len(diag["bins"]) == 5
    assert "expected_calibration_error_ece" in diag

# -----------------------------------------------------------------------------
# Test 8: Baseline Models & Binary Raster Metric Computation
# -----------------------------------------------------------------------------
def test_baseline_models_and_raster_metrics():
    t_base = TerrainThresholdBaseline(hand_threshold_m=1.5, max_elevation_m=20.0)
    assert t_base.model_status == ModelStatus.BASELINE

    hand = np.array([0.5, 1.2, 2.5, 0.8])
    dem = np.array([12.0, 18.0, 30.0, 15.0])
    depth_preds = t_base.predict(hand_m=hand, dem_elevation_m=dem)
    assert depth_preds[0] > 0.0 # hand < 1.5 and dem < 20
    assert depth_preds[2] == 0.0 # hand > 1.5 and dem > 20

    p_base = PhysicsInformedPlanarBaseline()
    assert p_base.model_status == ModelStatus.BASELINE

    # Exact binary raster metrics
    y_true = np.array([1, 1, 0, 0, 1, 0])
    y_pred = np.array([1, 1, 0, 1, 1, 0])
    raster_metrics = evaluate_binary_water_masks(y_true, y_pred)
    assert raster_metrics["tp"] == 3
    assert raster_metrics["fp"] == 1
    assert raster_metrics["fn"] == 0
    assert raster_metrics["recall"] == 1.0
    assert raster_metrics["precision"] == 0.75

# -----------------------------------------------------------------------------
# Test 9: Complete 9-Point Provenance Retention
# -----------------------------------------------------------------------------
def test_complete_9_point_provenance_retention():
    service = InundationService()
    valid_time = datetime(2022, 8, 17, 18, 0, tzinfo=timezone.utc)
    sar_record = {
        "event_id": "EVT-MAHANADI-2022-08",
        "acquisition_time": "2022-08-17T18:04:00Z",
        "observed_extent_sqkm": 184.6
    }

    result = service.generate_inundation_forecast(
        peak_river_stage_m=26.65,
        danger_level_m=26.41,
        rainfall_accumulation_24h_mm=210.0,
        forecast_valid_time=valid_time,
        lead_time_hours=6.0,
        rainfall_run_id="RAIN-RUN-001",
        hydrology_run_id="HYDRO-RUN-002",
        sar_reference_record=sar_record
    )

    prov = result.inundation_provenance
    assert prov is not None
    # Verify 9 core provenance attributes:
    assert prov.rainfall_run_id == "RAIN-RUN-001"           # 1
    assert prov.hydrology_run_id == "HYDRO-RUN-002"         # 2
    assert prov.inundation_run_id.startswith("INUND-RUN-")  # 3
    assert prov.model_version == "AnalyticalSurrogate-v3.1"      # 4
    assert prov.model_status == ModelStatus.CANDIDATE       # 5
    assert prov.feature_version == "v1.0.0"                 # 6
    assert prov.dem_version == "FABDEM_v1.2"                # 7
    assert prov.reference_version.startswith("Sentinel-1") # 8
    assert prov.forecast_valid_time == valid_time           # 9
    assert prov.dataset_state == "REAL_HISTORICAL_HINDCAST"

    # SAR reference validation attached
    sar_ref = result.sar_flood_reference
    assert sar_ref is not None
    assert sar_ref.event_id == "EVT-MAHANADI-2022-08"
    assert sar_ref.temporal_match_status == TemporalMatchStatus.MATCHED
    assert sar_ref.depth_status == DepthStatus.MODEL_ESTIMATE
    assert sar_ref.depth_validation == DepthValidationStatus.UNAVAILABLE

# -----------------------------------------------------------------------------
# Test 10: Partition Exclusivity (TRAIN/VAL Excluded from Primary Benchmark)
# -----------------------------------------------------------------------------
def test_train_and_validation_events_excluded_from_primary_benchmark():
    import json
    from pathlib import Path
    from ml.evaluation.run_inundation_benchmarks import run_inundation_benchmarks

    # Run benchmarks
    bench_results = run_inundation_benchmarks()

    assert "held_out_test_event_ids" in bench_results
    held_out_ids = bench_results["held_out_test_event_ids"]

    # 1. Assert TRAIN and VALIDATION events are NOT in held_out_test_event_ids
    assert "EVT-MAHANADI-2020-08" not in held_out_ids # TRAIN
    assert "EVT-MAHANADI-2021-09" not in held_out_ids # VALIDATION
    assert "EVT-MAHANADI-2022-08" in held_out_ids     # HELD_OUT_TEST
    assert "EVT-MAHANADI-2024-08" in held_out_ids     # HELD_OUT_TEST
    assert len(held_out_ids) == 2

    # 2. Check JSON structure for deep surrogate
    deep_res = bench_results["models"]["Deep_Spatial_Surrogate"]
    assert "primary_held_out_test_benchmark" in deep_res
    assert "train_performance" in deep_res
    assert "validation_performance" in deep_res
    assert "held_out_test_performance" in deep_res

    # 3. Assert train performance has 1 event, validation has 1 event, test has 2 events
    assert deep_res["train_performance"]["events_count"] == 1
    assert deep_res["validation_performance"]["events_count"] == 1
    assert deep_res["held_out_test_performance"]["events_count"] == 2

    # 4. Verify Promotion Engine rejects evaluation evidence containing TRAIN events
    promotion_engine = InundationPromotionEngine()
    split_guard = SpatialLeakageGuard(
        train_events=["EVT-MAHANADI-2020-08"],
        val_events=["EVT-MAHANADI-2021-09"],
        test_events=["EVT-MAHANADI-2022-08", "EVT-MAHANADI-2024-08"]
    )
    candidate_model = RandomForestInundationSurrogate()

    # Contaminated evaluation evidence (includes TRAIN event)
    contaminated_eval = ["EVT-MAHANADI-2020-08", "EVT-MAHANADI-2022-08"]
    verdict = promotion_engine.evaluate_candidate_for_promotion(
        candidate_model=candidate_model,
        candidate_metrics={"iou": 0.85, "f1": 0.90, "brier_score": 0.05},
        baseline_metrics={"iou": 0.60, "f1": 0.70, "brier_score": 0.20},
        split_guard=split_guard,
        evaluation_events=contaminated_eval
    )
    assert verdict["promotion_granted"] is False
    assert verdict["checks"]["evidence_strictly_held_out_test"] is False

