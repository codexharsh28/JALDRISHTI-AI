"""
Geofence and Spatial Matching Engine for JALDRISHTI AI Public Alerts.
Calculates distance and containment between user subscription coordinates and hazard polygons.
"""

from typing import Dict, Any, List, Tuple, Optional
import math
from services.notifications.notification_types import GeofenceMatch

class GeofenceEngine:
    """
    Computes spatial containment and proximity using Haversine distance and polygon envelopes.
    """

    EARTH_RADIUS_KM = 6371.0

    @classmethod
    def haversine_distance_km(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculates great-circle distance between two points in km."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2 +
            math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_KM * c

    @classmethod
    def evaluate_geofence_match(
        cls,
        user_lat: float,
        user_lon: float,
        target_lat: float,
        target_lon: float,
        subscription_radius_km: float = 10.0,
        hazard_radius_km: float = 15.0
    ) -> Tuple[GeofenceMatch, float]:
        """
        Determines whether a user location matches an active hazard centroid/zone.
        Returns: (GeofenceMatch, distance_km)
        """
        dist_km = cls.haversine_distance_km(user_lat, user_lon, target_lat, target_lon)

        # 1. Direct hit: distance is within subscription radius or hazard radius
        if dist_km <= subscription_radius_km:
            return GeofenceMatch.IN_AREA, round(dist_km, 2)
        
        # 2. Near hit: within buffer boundary (subscription + hazard buffer)
        buffer_km = subscription_radius_km + hazard_radius_km
        if dist_km <= buffer_km:
            return GeofenceMatch.NEAR_AREA, round(dist_km, 2)

        return GeofenceMatch.OUTSIDE_AREA, round(dist_km, 2)

    @classmethod
    def is_point_in_bounding_box(
        cls,
        lat: float,
        lon: float,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float
    ) -> bool:
        return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)

# Global singleton
geofence_engine = GeofenceEngine()
