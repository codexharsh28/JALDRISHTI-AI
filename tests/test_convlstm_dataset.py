"""
Automated Dataset & Spatiotemporal Sequence Tests for PyTorch ConvLSTM Nowcaster.
Verifies:
1. Shape contract (N, T_in, C, H, W) and (N, T_out, 1, H, W).
2. Whole-event partition isolation (windows never cross event boundaries).
3. Normalization parameters computed exclusively on TRAIN partition.
4. Correct dataset loader integration.
"""

import pytest
import numpy as np
import torch
from ml.rainfall.deep.dataset import (
    RainfallNowcastDataset,
    build_event_sequences,
    create_partitioned_datasets
)
import pandas as pd

def test_event_sequence_builder_shapes_and_boundaries():
    df = pd.DataFrame({
        "fused_precip_rate_mm_hr": np.random.uniform(5.0, 45.0, 30),
        "timestamp": [f"2022-08-15T{i:02d}:00:00Z" for i in range(30)]
    })

    sx, sy, sm = build_event_sequences("EVT-TEST-01", df, grid_height=8, grid_width=12, t_in=4, t_out=6)

    # 30 timesteps - (4 + 6) + 1 = 21 windows
    assert len(sx) == 21
    assert len(sy) == 21
    assert len(sm) == 21
    assert sx.shape == (21, 4, 1, 8, 12)
    assert sy.shape == (21, 6, 1, 8, 12)

    # All metadata should belong strictly to EVT-TEST-01
    for meta in sm:
        assert meta["event_id"] == "EVT-TEST-01"

def test_partition_isolation_and_training_normalization():
    train_ds, val_ds, test_ds = create_partitioned_datasets(
        manifest_path="data/manifests/rainfall_split_manifest.yaml",
        t_in=4,
        t_out=12,
        grid_height=16,
        grid_width=24
    )

    assert len(train_ds) > 0
    assert len(val_ds) > 0
    assert len(test_ds) > 0

    # Normalization statistics of val and test must be exactly equal to train's
    assert val_ds.normalization_stats == train_ds.normalization_stats
    assert test_ds.normalization_stats == train_ds.normalization_stats

    # Verify distinct event IDs in each partition
    train_events = set(m["event_id"] for m in train_ds.metadata)
    val_events = set(m["event_id"] for m in val_ds.metadata)
    test_events = set(m["event_id"] for m in test_ds.metadata)

    # Assert completely disjoint sets
    assert len(train_events.intersection(val_events)) == 0, "Train and Val events overlap!"
    assert len(train_events.intersection(test_events)) == 0, "Train and Test events overlap!"
    assert len(val_events.intersection(test_events)) == 0, "Val and Test events overlap!"

def test_dataset_unnormalize_reproducibility():
    x_raw = np.random.uniform(0.0, 50.0, (10, 4, 1, 16, 24)).astype(np.float32)
    y_raw = np.random.uniform(0.0, 50.0, (10, 12, 1, 16, 24)).astype(np.float32)
    meta = [{"event_id": f"EVT-{i}"} for i in range(10)]

    ds = RainfallNowcastDataset(x_raw, y_raw, meta, normalize=True)
    x_norm_tensor, _, _ = ds[0]

    # Invert normalization
    x_recovered = ds.unnormalize(x_norm_tensor.numpy())
    np.testing.assert_allclose(x_recovered, x_raw[0], rtol=1e-4, atol=1e-4)
