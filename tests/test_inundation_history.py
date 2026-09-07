"""
Unit tests for Inundation Evolution Append-Only History Store (Phase 15).
"""

import pytest
from services.inundation_evolution.evolution_types import InundationSnapshot, SpatialChangeSummary
from services.inundation_evolution.evolution_store import InundationEvolutionStore

def test_inundation_store_history_and_query():
    store = InundationEvolutionStore()
    
    snap1 = InundationSnapshot(inundation_snapshot_id="SNAP-HIST-01", inundated_area_sqkm=280.0)
    snap2 = InundationSnapshot(inundation_snapshot_id="SNAP-HIST-02", inundated_area_sqkm=340.0)
    
    store.append_snapshot(snap1)
    store.append_snapshot(snap2)

    curr = store.get_current_snapshot()
    assert curr.inundation_snapshot_id == "SNAP-HIST-02"

    prev = store.get_previous_snapshot()
    assert prev.inundation_snapshot_id == "SNAP-HIST-01"

    hist = store.get_snapshots_history(limit=5)
    assert len(hist) >= 2
    assert hist[0].inundation_snapshot_id == "SNAP-HIST-02"

    fetched = store.get_snapshot_by_id("SNAP-HIST-01")
    assert fetched is not None
    assert fetched.inundated_area_sqkm == 280.0
