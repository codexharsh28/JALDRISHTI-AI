"""
Geofencing & Spatial Zone Matching Tests for JALDRISHTI AI Public Alerts.
Validates Haversine calculations, IN_AREA, NEAR_AREA safety buffers, and OUTSIDE_AREA containment.
"""

import pytest
from services.notifications.geofence_engine import GeofenceEngine
from services.notifications.notification_types import GeofenceMatch

def test_haversine_distance_accuracy():
    # Distance between Cuttack (20.46, 85.88) and Kendrapara (20.50, 86.42) ~ 56km
    dist = GeofenceEngine.haversine_distance_km(20.46, 85.88, 20.50, 86.42)
    assert 54.0 <= dist <= 58.0

def test_in_area_geofence_match():
    # User in Cuttack (20.46, 85.88), Hazard Centroid at (20.47, 85.89)
    match, dist = GeofenceEngine.evaluate_geofence_match(
        user_lat=20.46,
        user_lon=85.88,
        target_lat=20.47,
        target_lon=85.89,
        subscription_radius_km=10.0,
        hazard_radius_km=15.0
    )
    assert match == GeofenceMatch.IN_AREA
    assert dist < 5.0

def test_near_area_safety_buffer_match():
    # User at Bhubaneswar (20.29, 85.84), Hazard at Cuttack (20.46, 85.88) ~ 20km
    # With 10km subscription radius and 15km hazard radius, total buffer = 25km
    match, dist = GeofenceEngine.evaluate_geofence_match(
        user_lat=20.29,
        user_lon=85.84,
        target_lat=20.46,
        target_lon=85.88,
        subscription_radius_km=10.0,
        hazard_radius_km=15.0
    )
    assert match == GeofenceMatch.NEAR_AREA
    assert 18.0 <= dist <= 24.0

def test_outside_area_geofence_match():
    # User at Sambalpur (21.46, 83.97), Hazard at Cuttack (20.46, 85.88) ~ 220km
    match, dist = GeofenceEngine.evaluate_geofence_match(
        user_lat=21.46,
        user_lon=83.97,
        target_lat=20.46,
        target_lon=85.88,
        subscription_radius_km=10.0,
        hazard_radius_km=15.0
    )
    assert match == GeofenceMatch.OUTSIDE_AREA
    assert dist > 200.0
