"""
Unit tests for Spatial Geofence Containment & Proximity Calculations.
"""

import pytest
from services.notifications.geofence_engine import GeofenceEngine
from services.notifications.notification_types import GeofenceMatch

def test_geofence_haversine_distance():
    # Distance between Cuttack (20.46, 85.88) and Bhubaneswar (20.29, 85.84) ~ 20km
    dist = GeofenceEngine.haversine_distance_km(20.46, 85.88, 20.29, 85.84)
    assert 18.0 <= dist <= 22.0

def test_geofence_matching_in_area():
    # User at Cuttack, Alert at Cuttack
    match, dist = GeofenceEngine.evaluate_geofence_match(
        user_lat=20.46,
        user_lon=85.88,
        target_lat=20.48,
        target_lon=85.89,
        subscription_radius_km=10.0,
        hazard_radius_km=15.0
    )
    assert match == GeofenceMatch.IN_AREA
    assert dist < 5.0

def test_geofence_matching_outside_area():
    # User at Rourkela (22.25, 84.85), Alert at Cuttack (20.46, 85.88) ~ 220km
    match, dist = GeofenceEngine.evaluate_geofence_match(
        user_lat=22.25,
        user_lon=84.85,
        target_lat=20.46,
        target_lon=85.88,
        subscription_radius_km=10.0,
        hazard_radius_km=15.0
    )
    assert match == GeofenceMatch.OUTSIDE_AREA
    assert dist > 200.0
