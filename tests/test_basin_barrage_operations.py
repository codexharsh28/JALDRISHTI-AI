"""
Unit tests for Barrage Gate Regulation & Delta Mass Balance (Phase 17).
"""

import pytest
from services.basin_state import DigitalBasinEngine

def test_barrage_operations_update():
    engine = DigitalBasinEngine()
    
    updates = [
        {"structure_id": "BAR-MUNDALI-02", "open_gates": 38, "discharge_cumec": 21500.0, "status": "FLOOD_DISCHARGE"},
        {"structure_id": "BAR-JOBRA-04", "open_gates": 50, "discharge_cumec": 9500.0, "status": "FLOOD_DISCHARGE"}
    ]

    updated = engine.update_barrage_operations(updates)
    
    mundali = next(s for s in updated.structures if s.structure_id == "BAR-MUNDALI-02")
    assert mundali.open_gates == 38
    assert mundali.discharge_cumec == 21500.0
    assert updated.total_delta_inflow_cumec >= 21500.0
