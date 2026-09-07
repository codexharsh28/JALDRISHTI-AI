"""
Automated Evaluation Tests for PyTorch ConvLSTM Nowcaster.
Verifies:
1. Held-out test evaluation execution.
2. Metrics computation (RMSE, MAE, CSI, POD, FAR).
3. Baseline comparison structure and report generation.
"""

import pytest
import os
import json
from pathlib import Path
from ml.rainfall.deep.metrics import compute_nowcast_metrics
import numpy as np

def test_metrics_calculation_known_cases():
    # Perfect forecast
    y_true = np.array([0.0, 10.0, 20.0, 40.0, 70.0])
    y_pred = np.array([0.0, 10.0, 20.0, 40.0, 70.0])

    m = compute_nowcast_metrics(y_pred, y_true)
    assert m["rmse_mm"] == 0.0
    assert m["mae_mm"] == 0.0
    assert m["thresholds"]["35mm"]["csi"] == 1.0
    assert m["thresholds"]["35mm"]["pod"] == 1.0
    assert m["thresholds"]["35mm"]["far"] == 0.0

def test_metrics_calculation_false_alarms_and_misses():
    y_true = np.array([0.0, 0.0, 40.0, 0.0])
    y_pred = np.array([40.0, 0.0, 0.0, 0.0])

    m = compute_nowcast_metrics(y_pred, y_true)
    # Threshold 35mm: 1 false alarm, 1 miss, 0 hits
    th = m["thresholds"]["35mm"]
    assert th["hits"] == 0
    assert th["false_alarms"] == 1
    assert th["misses"] == 1
    assert th["csi"] == 0.0

def test_hindcast_report_integrity():
    report_file = "ml/evaluation/convlstm_hindcast.json"
    assert Path(report_file).exists(), f"{report_file} does not exist"

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["evaluation_partition"] == "HELD_OUT_TEST"
    assert data["HELD_OUT_TEST_EVENT_COUNT"] == 2
    assert data["HELD_OUT_TEST_SEQUENCE_COUNT"] == 1170
    assert data["HELD_OUT_TEST_EVENT_COUNT"] != data["HELD_OUT_TEST_SEQUENCE_COUNT"]
    assert "EVT-MAHANADI-2022-08" in data["held_out_events"]
    assert "EVT-MAHANADI-2024-08" in data["held_out_events"]

    # All 5 required models must be present in the benchmark
    required_models = [
        "L0_PERSISTENCE",
        "L1_ADVECTION",
        "L2_GRADIENT_BOOSTED",
        "L3_ANALYTICAL_SURROGATE",
        "L3_PYTORCH_CONVLSTM"
    ]
    for model_key in required_models:
        assert model_key in data["models"], f"Missing required model: {model_key}"
        assert "overall" in data["models"][model_key]
        assert "horizons" in data["models"][model_key]
        # Must evaluate across required lead times
        for h in ["30m", "1h", "2h", "3h", "4h", "5h", "6h"]:
            assert h in data["models"][model_key]["horizons"], f"Model {model_key} missing horizon {h}"
