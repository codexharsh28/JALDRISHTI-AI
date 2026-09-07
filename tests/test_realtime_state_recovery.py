"""
Unit tests for Monotonic State Versioning and Restart Snapshot Recovery.
"""

import pytest
from services.runtime.current_state import CurrentStateManager

def test_monotonic_state_version_increment():
    mgr = CurrentStateManager()
    v1 = mgr.state_version
    v2 = mgr.increment_state_version()
    v3 = mgr.increment_state_version()
    assert v2 == v1 + 1
    assert v3 == v2 + 1

def test_state_snapshot_generation():
    mgr = CurrentStateManager()
    snap = mgr.get_current_snapshot()
    assert snap.state_version == mgr.state_version
    assert snap.basin_id == "pilot-mahanadi-delta"
    assert "SNAP-" in snap.snapshot_id
