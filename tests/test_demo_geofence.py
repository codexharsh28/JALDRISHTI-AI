"""
Geofence Point-in-Polygon Isolation Tests for Demo Citizens.
Verifies that Cuttack user receives alerts and Sundargarh user is isolated.
"""

import pytest
from services.notifications.geofence_engine import GeofenceEngine
from services.notifications.notification_types import GeofenceMatch

def test_demo_geofence_targeting_and_isolation():
    # Flood zone centered on Cuttack (20.46, 85.88)
    hazard_center = (20.46, 85.88)

    # User 1: Cuttack Delta (Inside)
    cuttack_loc = (20.48, 85.90)
    match_cuttack, dist1 = GeofenceEngine.evaluate_geofence_match(
        cuttack_loc[0], cuttack_loc[1], hazard_center[0], hazard_center[1]
    )
    assert match_cuttack in [GeofenceMatch.IN_AREA, GeofenceMatch.NEAR_AREA]
    assert dist1 < 10.0

    # User 2: Rourkela Highlands (Outside ~250km away)
    rourkela_loc = (22.25, 84.85)
    match_rourkela, dist2 = GeofenceEngine.evaluate_geofence_match(
        rourkela_loc[0], rourkela_loc[1], hazard_center[0], hazard_center[1]
    )
    assert match_rourkela == GeofenceMatch.OUTSIDE_AREA
    assert dist2 > 100.0
