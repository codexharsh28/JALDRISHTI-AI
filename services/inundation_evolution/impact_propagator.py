"""
Dynamic Critical Asset & Population Exposure Propagator for JALDRISHTI AI (Phase 15).
Translates evolving hydraulic surfaces into infrastructure vulnerability and population exposure.
"""

from typing import Dict, Any, List, Tuple, Optional
import logging

from services.inundation_evolution.evolution_types import (
    AssetExposureItem,
    PopulationExposureSummary,
    InundationSnapshot
)

logger = logging.getLogger(__name__)

# Mahanadi Delta Critical Infrastructure Assets Catalog
MAHANADI_ASSETS = [
    {
        "asset_id": "HOSP_SCB_CUTTACK",
        "name": "SCB Medical College & Hospital, Cuttack",
        "asset_type": "HOSPITAL",
        "lat": 20.4780,
        "lon": 85.8790,
        "elevation_m": 27.5
    },
    {
        "asset_id": "HOSP_DHH_KENDRAPARA",
        "name": "District Headquarters Hospital, Kendrapara",
        "asset_type": "HOSPITAL",
        "lat": 20.5020,
        "lon": 86.4250,
        "elevation_m": 23.0
    },
    {
        "asset_id": "SHELTER_MARSHAGHAI_01",
        "name": "Marshaghai Multi-Purpose Cyclone & Flood Shelter",
        "asset_type": "SHELTER",
        "lat": 20.4500,
        "lon": 86.5300,
        "elevation_m": 22.5
    },
    {
        "asset_id": "SHELTER_NIMAPARA_02",
        "name": "Nimapara Cyclone Shelter Hub",
        "asset_type": "SHELTER",
        "lat": 20.0600,
        "lon": 86.0150,
        "elevation_m": 24.0
    },
    {
        "asset_id": "BRIDGE_MAHANADI_NH16",
        "name": "Mahanadi Rail & Road Bridge, NH16",
        "asset_type": "BRIDGE",
        "lat": 20.4900,
        "lon": 85.8600,
        "elevation_m": 28.0
    },
    {
        "asset_id": "BRIDGE_KATHAJODI_CUTTACK",
        "name": "Kathajodi River Bridge & Embankment Sluice",
        "asset_type": "BRIDGE",
        "lat": 20.4400,
        "lon": 85.8700,
        "elevation_m": 26.2
    },
    {
        "asset_id": "GRID_SUBSTATION_CHOUDWAR",
        "name": "Choudwar 220kV Grid Substation",
        "asset_type": "POWER_SUBSTATION",
        "lat": 20.5300,
        "lon": 85.9100,
        "elevation_m": 27.0
    },
    {
        "asset_id": "HWY_NH53_PARADIP_CORRIDOR",
        "name": "NH-53 Cuttack-Paradip Port Expressway Corridor",
        "asset_type": "ROAD_NETWORK",
        "lat": 20.3500,
        "lon": 86.3000,
        "elevation_m": 23.5
    }
]

class ImpactPropagator:
    """
    Evaluates asset exposure and population vulnerability against updated inundation snapshots.
    """

    def evaluate_asset_exposure(
        self,
        inundated_area_sqkm: float,
        flood_prob: float,
        stage_m: float = 26.0,
        hydrology_source: str = "OBSERVED_CWC"
    ) -> List[AssetExposureItem]:
        confidence = "DATA_DEGRADED" if "GLOFAS" in hydrology_source.upper() else "HIGH"
        snap = InundationSnapshot(
            inundated_area_sqkm=inundated_area_sqkm,
            mean_flood_probability=flood_prob,
            hydrology_source=hydrology_source,
            confidence=confidence
        )
        assets, _ = self.propagate_impact(snap)
        return assets

    def evaluate_population_exposure(
        self,
        inundated_area_sqkm: float,
        flood_prob: float,
        previous_population_exposed: int = 45000,
        hydrology_source: str = "OBSERVED_CWC"
    ) -> PopulationExposureSummary:
        confidence = "DATA_DEGRADED" if "GLOFAS" in hydrology_source.upper() else "HIGH"
        snap = InundationSnapshot(
            inundated_area_sqkm=inundated_area_sqkm,
            mean_flood_probability=flood_prob,
            hydrology_source=hydrology_source,
            confidence=confidence
        )
        _, pop = self.propagate_impact(snap, previous_population_exposed=previous_population_exposed)
        return pop

    @staticmethod
    def propagate_impact(
        snapshot: InundationSnapshot,
        previous_population_exposed: int = 45000
    ) -> Tuple[List[AssetExposureItem], PopulationExposureSummary]:
        """
        Calculates exposure profiles for critical facilities and population grids.
        """
        area = snapshot.inundated_area_sqkm
        prob = snapshot.mean_flood_probability
        raw_source = snapshot.hydrology_source or "OBSERVED_CWC"
        
        is_glofas = "GLOFAS" in raw_source.upper()
        source_label = "MODELED_GLOFAS" if is_glofas else raw_source
        confidence = "DATA_DEGRADED" if is_glofas else snapshot.confidence

        # 1. Evaluate Asset Exposure
        asset_items: List[AssetExposureItem] = []
        for a in MAHANADI_ASSETS:
            elev = a["elevation_m"]
            # Exposure logic based on flood extent & stage
            if area >= 350.0 and elev <= 27.5:
                risk_st = "HIGH_RISK"
                f_prob = min(0.95, prob * 1.1)
                d_class = ">2m" if elev <= 23.5 else "1-2m"
                dist_m = 0.0
            elif area > 200.0 and elev <= 27.5:
                risk_st = "MODERATE_RISK"
                f_prob = min(0.75, prob * 0.85)
                d_class = "0.3-1m" if elev <= 26.2 else "<0.3m"
                dist_m = 150.0
            else:
                risk_st = "SAFE"
                f_prob = 0.05
                d_class = "DRY"
                dist_m = 1200.0

            mitigation_note = f"Impact based on {source_label}" if is_glofas else "Routine floodplain monitoring"

            asset_items.append(AssetExposureItem(
                asset_id=a["asset_id"],
                asset_name=a["name"],
                name=a["name"],
                asset_type=a["asset_type"],
                latitude=a["lat"],
                longitude=a["lon"],
                lat=a["lat"],
                lon=a["lon"],
                flood_probability=round(f_prob, 2),
                depth_class=d_class,
                distance_to_flood_m=dist_m,
                risk_state=risk_st,
                confidence=confidence,
                dataset_state=source_label,
                source_label=source_label,
                mitigation_protocol=mitigation_note
            ))

        # 2. Evaluate Population Exposure
        pop_forecast = int(area * 306.6)
        pop_now = int(area * 260.0)
        newly_exposed = max(0, pop_now - previous_population_exposed)
        severely_affected = int(snapshot.depth_classes.depth_gt_2m_sqkm * 340.0) if hasattr(snapshot, "depth_classes") and snapshot.depth_classes else int(area * 50)

        pop_summary = PopulationExposureSummary(
            population_exposed_now=pop_now,
            population_exposed_forecast=pop_forecast,
            newly_exposed_population=newly_exposed,
            severely_affected_population_gt_1m=severely_affected,
            dataset_state=source_label
        )

        return asset_items, pop_summary
