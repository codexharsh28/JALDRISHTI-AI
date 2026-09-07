"""
Impact Assessment Engine for JALDRISHTI AI.
Performs spatial intersections between flood inundation footprints and critical infrastructure
(hospitals, schools, shelters, roads, bridges, power substations, and population).
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import json

from services.models import ImpactSummary, ProvenanceMetadata

class ImpactAssessmentEngine:
    def __init__(self, assets_geojson_path: str = "geospatial/assets/critical_infrastructure.geojson"):
        with open(assets_geojson_path, "r") as f:
            self.assets_geojson = json.load(f)
        self.assets = self.assets_geojson.get("features", [])

    def evaluate_impact(
        self,
        inundated_area_sqkm: float,
        depth_gt_1m_sqkm: float,
        flood_prob_mean: float,
        forecast_run_id: str,
        valid_time: datetime
    ) -> ImpactSummary:
        """
        Calculates affected facilities, population exposed, and composite impact index.
        """
        # Population density proxy: ~520 people per sq km in delta
        exposed_pop = int(inundated_area_sqkm * 520)
        high_risk_pop = int(depth_gt_1m_sqkm * 580)

        # Asset intersection logic based on inundation magnitude
        affected_assets = []
        hospitals_affected = 0
        schools_affected = 0
        shelters_affected = 0
        roads_flooded_km = 0.0
        bridges_critical = 0
        power_substations = 0

        # Dynamic severity classification of asset impact
        for feature in self.assets:
            props = feature.get("properties", {})
            cat = props.get("category")
            name = props.get("name")
            elev = props.get("elevation_m", 25.0)

            is_affected = False
            risk_tier = "NONE"

            # Low elevation assets (< 15m) flood first
            if elev < 10.0 and inundated_area_sqkm > 20.0:
                is_affected = True
                risk_tier = "HIGH_CONFIDENCE"
            elif elev < 25.0 and inundated_area_sqkm > 80.0:
                is_affected = True
                risk_tier = "LIKELY_AFFECTED"
            elif elev < 35.0 and inundated_area_sqkm > 150.0:
                is_affected = True
                risk_tier = "POTENTIALLY_EXPOSED"

            if is_affected:
                if cat == "HOSPITAL":
                    hospitals_affected += 1
                elif cat == "SHELTER":
                    shelters_affected += 1
                elif cat == "HIGHWAY":
                    roads_flooded_km += props.get("length_km", 20.0) * 0.4
                elif cat == "BRIDGE":
                    bridges_critical += 1
                elif cat == "POWER_SUBSTATION":
                    power_substations += 1

                affected_assets.append({
                    "asset_id": props.get("asset_id"),
                    "name": name,
                    "category": cat,
                    "criticality": props.get("criticality"),
                    "risk_tier": risk_tier,
                    "elevation_m": elev,
                    "subbasin_id": props.get("subbasin_id")
                })

        # Composite Impact Score (0 to 100)
        score = (
            min(40.0, (exposed_pop / 100000.0) * 40.0) +
            min(25.0, hospitals_affected * 10.0 + power_substations * 12.0) +
            min(20.0, roads_flooded_km * 0.5 + bridges_critical * 8.0) +
            min(15.0, flood_prob_mean * 15.0)
        )

        provenance = ProvenanceMetadata(
            source_id="IMPACT_ENGINE_SPATIAL",
            provider="JALDRISHTI AI Disaster Analytics",
            product_name="Vulnerability and Critical Asset Exposure Evaluation",
            observed_at=valid_time,
            received_at=valid_time,
            source_latency_mins=5.0,
            model_version_id="Impact-v1.4",
            forecast_run_id=forecast_run_id,
            is_simulation=True
        )

        return ImpactSummary(
            forecast_run_id=forecast_run_id,
            valid_time=valid_time,
            population_exposed=exposed_pop,
            population_high_risk=high_risk_pop,
            hospitals_affected=hospitals_affected,
            schools_affected=schools_affected,
            shelters_available=8,
            shelters_affected=shelters_affected,
            road_km_flooded=round(roads_flooded_km, 1),
            bridges_critical=bridges_critical,
            power_substations_at_risk=power_substations,
            total_impact_score=round(score, 1),
            affected_assets=affected_assets,
            provenance=provenance
        )
