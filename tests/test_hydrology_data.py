"""
Automated Tests for Hydrology Data Manifests and Whole-Event Split Partitions.
"""

import yaml
from pathlib import Path

def test_hydrology_datasets_manifest_structure():
    mpath = Path("data/manifests/hydrology_datasets.yaml")
    assert mpath.exists()
    with open(mpath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "datasets" in data
    assert len(data["datasets"]) >= 2
    
    cwc_set = data["datasets"][0]
    assert cwc_set["dataset_id"] == "CWC_MAHANADI_HOURLY_TELEMETRY_V1"
    assert cwc_set["state"] == "REAL_HISTORICAL_ANALYSIS"
    assert "CWC_MUNDALI" in cwc_set["station_ids"]

def test_whole_event_partition_isolation():
    mpath = Path("data/manifests/hydrology_split_manifest.yaml")
    assert mpath.exists()
    with open(mpath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["split_policy"] == "WHOLE_EVENT_PARTITIONING"
    partitions = data["partitions"]
    assert "TRAIN" in partitions
    assert "VALIDATION" in partitions
    assert "HELD_OUT_TEST" in partitions

    train_events = {e["event_id"] for e in partitions["TRAIN"]["events"]}
    val_events = {e["event_id"] for e in partitions["VALIDATION"]["events"]}
    test_events = {e["event_id"] for e in partitions["HELD_OUT_TEST"]["events"]}

    # Verify complete mutual exclusivity
    assert len(train_events.intersection(val_events)) == 0
    assert len(train_events.intersection(test_events)) == 0
    assert len(val_events.intersection(test_events)) == 0
