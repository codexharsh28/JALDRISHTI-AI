"""
Spatial Consistency & Multi-Source Cross-Corroborator for JALDRISHTI AI Hydromet Anomaly Detection.
Differentiates legitimate extreme meteorological events from isolated sensor hardware failure
using neighboring gauges, NASA GPM IMERG satellite rainfall, and NWP forecast fields.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import logging
from services.anomaly.anomaly_types import AnomalyClassification

logger = logging.getLogger(__name__)

# Representative station coordinates (Mahanadi Delta Pilot Region)
STATION_COORDINATES: Dict[str, Tuple[float, float]] = {
    "IMD_AWS_BHUBANESWAR": (20.2961, 85.8245),
    "IMD_AWS_CUTTACK": (20.4625, 85.8828),
    "IMD_AWS_PARADIP": (20.3160, 86.6110),
    "IMD_AWS_PURI": (19.8135, 85.8312),
    "IMD_AWS_KENDRAPARA": (20.5000, 86.4200),
    "CWC_MUNDALI": (20.4430, 85.7480),
    "CWC_NARAJ": (20.4600, 85.7700),
    "CWC_TIKRAPARA": (20.6000, 84.7800),
    "CWC_KHAIRMAL": (20.8100, 84.1500)
}

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two points on Earth in kilometers."""
    R = 6371.0 # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))

class SpatialConsistencyEngine:
    """
    Cross-checks sensor observations against neighboring stations, NASA GPM IMERG satellite QPE,
    and ECMWF/NCMRWF NWP forecast forcing.
    """

    def __init__(self, max_neighbor_radius_km: float = 75.0):
        self.max_neighbor_radius_km = max_neighbor_radius_km

    def evaluate_spatial_consistency(
        self,
        station_id: str,
        variable: str,
        observed_value: float,
        all_recent_observations: Dict[str, Dict[str, Any]],
        satellite_qpe: Optional[float] = None,
        nwp_forecast: Optional[float] = None
    ) -> Tuple[float, AnomalyClassification, Dict[str, Any]]:
        """
        Calculates spatial disagreement and classifies anomaly plausibility.
        Returns:
            disagreement_score (0.0 to 1.0)
            classification (VALID_EXTREME, POSSIBLE_ANOMALY, LIKELY_SENSOR_ERROR, INSUFFICIENT_CONTEXT)
            evidence (dict)
        """
        target_coords = STATION_COORDINATES.get(station_id)
        if not target_coords:
            return 0.15, AnomalyClassification.INSUFFICIENT_CONTEXT, {
                "reason": "No spatial coordinates registered for station",
                "station_id": station_id
            }

        t_lat, t_lon = target_coords

        # 1. Discover neighboring stations reporting the same or equivalent variable within radius
        neighbors: List[Dict[str, Any]] = []
        for other_id, obs_dict in all_recent_observations.items():
            if other_id == station_id:
                continue
            other_coords = STATION_COORDINATES.get(other_id)
            if not other_coords:
                continue
            o_lat, o_lon = other_coords
            dist_km = haversine_km(t_lat, t_lon, o_lat, o_lon)
            if dist_km <= self.max_neighbor_radius_km:
                # Find matching variable
                val = obs_dict.get(variable)
                if val is None:
                    # Check field aliases
                    if "rain" in variable:
                        val = obs_dict.get("rainfall_1h_mm", obs_dict.get("rainfall", obs_dict.get("rain_mm")))
                    elif "stage" in variable or "water" in variable:
                        val = obs_dict.get("river_stage_m", obs_dict.get("river_stage", obs_dict.get("water_level")))
                    elif "temp" in variable:
                        val = obs_dict.get("temperature_c", obs_dict.get("temperature"))
                
                if val is not None and not math.isnan(float(val)):
                    neighbors.append({
                        "station_id": other_id,
                        "distance_km": round(dist_km, 1),
                        "value": float(val)
                    })

        evidence: Dict[str, Any] = {
            "target_station": station_id,
            "target_value": observed_value,
            "neighbors_found": len(neighbors),
            "neighbors": neighbors,
            "satellite_qpe": satellite_qpe,
            "nwp_forecast": nwp_forecast
        }

        # 2. Check if any spatial context exists
        if not neighbors and satellite_qpe is None and nwp_forecast is None:
            return 0.1, AnomalyClassification.INSUFFICIENT_CONTEXT, evidence

        # Inverse Distance Weighting (IDW) of neighbors
        if neighbors:
            weights = [1.0 / max(n["distance_km"], 1.0) for n in neighbors]
            sum_w = sum(weights)
            neighbor_mean = sum(n["value"] * w for n, w in zip(neighbors, weights)) / sum_w
            max_neighbor = max(n["value"] for n in neighbors)
            min_neighbor = min(n["value"] for n in neighbors)
            evidence["neighbor_idw_mean"] = round(neighbor_mean, 2)
            evidence["neighbor_max"] = round(max_neighbor, 2)
            evidence["neighbor_min"] = round(min_neighbor, 2)
        else:
            neighbor_mean = None
            max_neighbor = None
            min_neighbor = None

        # 3. Assess Corroboration Signals
        corroborated_signals = 0
        total_signals = 0

        # Neighboring Gauge Consensus Check
        if neighbors and neighbor_mean is not None and max_neighbor is not None:
            total_signals += 1
            if observed_value >= 30.0:
                # Heavy rainfall / extreme condition: if max neighbor reports significant activity
                if max_neighbor >= 15.0 or (neighbor_mean >= 10.0 and abs(observed_value - neighbor_mean) <= max(25.0, 0.7 * observed_value)):
                    corroborated_signals += 1
            elif abs(observed_value - neighbor_mean) <= max(12.0, 0.4 * max(abs(observed_value), 1.0)):
                corroborated_signals += 1

        # Satellite QPE Check (e.g. NASA GPM IMERG Early / INSAT HEM)
        if satellite_qpe is not None and not math.isnan(satellite_qpe):
            total_signals += 1
            delta = abs(observed_value - satellite_qpe)
            evidence["satellite_qpe_delta"] = round(delta, 2)
            if observed_value >= 30.0:
                if satellite_qpe >= 15.0 or delta <= max(25.0, 0.6 * observed_value):
                    corroborated_signals += 1
            elif delta <= max(15.0, 0.5 * max(abs(observed_value), 1.0)):
                corroborated_signals += 1

        # NWP Atmospheric Forcing Model Check (ECMWF / NCMRWF)
        if nwp_forecast is not None and not math.isnan(nwp_forecast):
            total_signals += 1
            if observed_value >= 30.0:
                if nwp_forecast >= 12.0 or abs(observed_value - nwp_forecast) <= max(30.0, 0.7 * observed_value):
                    corroborated_signals += 1
            elif abs(observed_value - nwp_forecast) <= max(18.0, 0.5 * max(abs(observed_value), 1.0)):
                corroborated_signals += 1

        evidence["corroborated_signals"] = corroborated_signals
        evidence["total_signals"] = total_signals

        if total_signals == 0:
            return 0.1, AnomalyClassification.INSUFFICIENT_CONTEXT, evidence

        agreement_ratio = corroborated_signals / total_signals
        evidence["agreement_ratio"] = round(agreement_ratio, 2)

        # 4. Multi-Signal Classification & Disagreement Score
        # Case A: Corroborated Extreme Event -> VALID_EXTREME
        if observed_value >= 30.0 and agreement_ratio >= 0.4:
            disagreement_score = round(max(0.1, 0.4 * (1.0 - agreement_ratio)), 3)
            return disagreement_score, AnomalyClassification.VALID_EXTREME, evidence

        # Case B: Isolated Extreme Surge with ZERO corroboration -> LIKELY_SENSOR_ERROR
        if observed_value >= 40.0 and agreement_ratio == 0.0:
            disagreement_score = 0.92
            return disagreement_score, AnomalyClassification.LIKELY_SENSOR_ERROR, evidence

        # Case C: Partial Disagreement / Moderate Outlier -> POSSIBLE_ANOMALY
        if agreement_ratio < 0.5:
            disagreement_score = round(0.5 + 0.4 * (1.0 - agreement_ratio), 3)
            return disagreement_score, AnomalyClassification.POSSIBLE_ANOMALY, evidence

        # Case D: Normal spatial consistency
        disagreement_score = round(0.1 * (1.0 - agreement_ratio), 3)
        classification = AnomalyClassification.VALID_EXTREME if observed_value > 0 else AnomalyClassification.INSUFFICIENT_CONTEXT
        return disagreement_score, classification, evidence

# Global spatial consistency engine singleton
spatial_consistency_engine = SpatialConsistencyEngine()
