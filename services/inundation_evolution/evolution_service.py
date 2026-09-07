"""
Live Inundation Evolution & Impact Propagation Service for JALDRISHTI AI (Phase 15).
Coordinates reactive spatial differencing, critical asset vulnerability updates,
and emits INUNDATION_CHANGE_DETECTED and IMPACT_CHANGE_DETECTED domain events.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import logging

from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent
from services.events.event_bus import event_bus
from services.runtime.current_state import current_state_manager
from services.inundation_evolution.evolution_types import (
    InundationSnapshot,
    DepthClassBreakdown,
    SpatialChangeSummary,
    AssetExposureItem,
    PopulationExposureSummary
)
from services.inundation_evolution.differencing_engine import InundationDifferencingEngine
from services.inundation_evolution.impact_propagator import ImpactPropagator
from services.inundation_evolution.evolution_store import evolution_store

logger = logging.getLogger(__name__)

class InundationEvolutionService:
    """
    Coordinates live spatial flood updates and propagates impacts.
    """

    def __init__(self):
        # Seed initial baseline snapshot
        init_snap = InundationSnapshot(
            inundation_snapshot_id="INUN-SNAP-BASELINE-01",
            snapshot_id="INUN-SNAP-BASELINE-01",
            forecast_run_id="FR-BASELINE-01",
            valid_time=datetime.now(timezone.utc).isoformat(),
            scenario="P50",
            model_version="SpatialSurrogate_v3.1",
            inundated_area_sqkm=380.0,
            mean_flood_probability=0.72,
            peak_depth_m=2.45,
            depth_classes=DepthClassBreakdown(
                depth_0_to_0_3m_sqkm=120.0,
                depth_0_3_to_1m_sqkm=150.0,
                depth_1_to_2m_sqkm=80.0,
                depth_gt_2m_sqkm=30.0
            ),
            confidence="HIGH",
            hydrology_source="OBSERVED_CWC"
        )
        assets, pop = ImpactPropagator.propagate_impact(init_snap)
        evolution_store.append_snapshot(init_snap, None, assets, pop)

    def initialize(self):
        """Subscribe to hydrology updates from event bus."""
        event_bus.subscribe(EventType.HYDROLOGY_UPDATED, self._on_hydrology_updated)

    async def _on_hydrology_updated(self, event: OperationalEvent):
        """Reacts to new river stage/discharge forecast and updates inundation extent."""
        data = event.data or {}
        stage = data.get("predicted_stage_m", 26.85)
        source_label = data.get("input_hydrology_source", "OBSERVED_CWC")
        confidence = "DATA_DEGRADED" if "GLOFAS" in str(source_label).upper() else "HIGH"

        # Calculate new extent based on stage
        area = round(380.0 + (stage - 26.0) * 45.0, 1)
        prob = min(0.95, round(0.70 + (stage - 26.0) * 0.20, 2))

        await self.process_new_inundation(
            forecast_run_id=event.forecast_run_id or "FR-DEFAULT",
            inundated_area_sqkm=area,
            flood_prob=prob,
            stage_m=stage,
            hydrology_source=source_label,
            confidence=confidence,
            correlation_id=event.correlation_id,
            causation_id=event.event_id
        )

    async def process_new_inundation(
        self,
        forecast_run_id: str,
        inundated_area_sqkm: float,
        flood_prob: float,
        stage_m: float,
        hydrology_source: str = "OBSERVED_CWC",
        confidence: str = "HIGH",
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Tuple[InundationSnapshot, SpatialChangeSummary, List[AssetExposureItem], PopulationExposureSummary]:
        """
        Creates new snapshot, computes differencing, propagates impact, and emits domain events.
        """
        now = datetime.now(timezone.utc)
        prev_snap = evolution_store.get_current_snapshot()

        is_glofas = "GLOFAS" in str(hydrology_source).upper()
        dataset_state = "MODELED_GLOFAS" if is_glofas else "MODELED_SURROGATE"
        effective_confidence = "DATA_DEGRADED" if is_glofas else confidence

        depths = DepthClassBreakdown(
            depth_0_to_0_3m_sqkm=round(inundated_area_sqkm * 0.30, 1),
            depth_0_3_to_1m_sqkm=round(inundated_area_sqkm * 0.40, 1),
            depth_1_to_2m_sqkm=round(inundated_area_sqkm * 0.20, 1),
            depth_gt_2m_sqkm=round(inundated_area_sqkm * 0.10, 1),
            dataset_state="MODEL_ESTIMATE"
        )

        curr_snap = InundationSnapshot(
            forecast_run_id=forecast_run_id,
            valid_time=now.isoformat(),
            scenario="P50",
            model_version="SpatialSurrogate_v3.1",
            inundated_area_sqkm=inundated_area_sqkm,
            mean_flood_probability=flood_prob,
            peak_depth_m=round(max(0.5, (stage_m - 24.0) * 0.8), 2),
            depth_classes=depths,
            dataset_state=dataset_state,
            confidence=effective_confidence,
            hydrology_source=hydrology_source
        )

        # Spatial Differencing
        if prev_snap:
            change_summary = InundationDifferencingEngine.compute_spatial_change(curr_snap, prev_snap)
        else:
            change_summary = SpatialChangeSummary(
                current_snapshot_id=curr_snap.snapshot_id,
                previous_snapshot_id="NONE",
                expansion_sqkm=0.0,
                net_delta_sqkm=0.0,
                is_material_change=True
            )

        # Impact Propagation
        prev_pop = evolution_store.get_current_population()
        prev_pop_count = prev_pop.population_exposed_now if prev_pop else 45000
        assets, pop_summary = ImpactPropagator.propagate_impact(curr_snap, prev_pop_count)

        # Store
        evolution_store.append_snapshot(curr_snap, change_summary, assets, pop_summary)
        version = current_state_manager.increment_state_version()

        # Publish Events
        if change_summary.is_material_change:
            ev_inun = OperationalEvent.create(
                event_type=EventType.INUNDATION_UPDATED,
                source_id="INUNDATION_EVOLUTION_SERVICE",
                provider="Spatial Differencing Engine",
                data={
                    "snapshot": curr_snap.model_dump(),
                    "spatial_change": change_summary.model_dump()
                },
                forecast_run_id=forecast_run_id,
                state_version=version,
                correlation_id=correlation_id,
                causation_id=causation_id,
                priority=EventPriority.HIGH
            )
            await event_bus.publish(ev_inun)

            ev_inun_chg = OperationalEvent.create(
                event_type=EventType.INUNDATION_CHANGE_DETECTED,
                source_id="INUNDATION_EVOLUTION_SERVICE",
                provider="Spatial Differencing Engine",
                data={
                    "snapshot_id": curr_snap.snapshot_id,
                    "spatial_change": change_summary.model_dump(),
                    "expansion_sqkm": change_summary.expansion_sqkm,
                    "contraction_sqkm": change_summary.contraction_sqkm,
                    "rate_of_expansion_sqkm_per_hr": change_summary.inundation_expansion_rate_km2_per_hour
                },
                forecast_run_id=forecast_run_id,
                state_version=version,
                correlation_id=correlation_id,
                causation_id=ev_inun.event_id,
                priority=EventPriority.HIGH
            )
            await event_bus.publish(ev_inun_chg)

            ev_impact = OperationalEvent.create(
                event_type=EventType.IMPACT_UPDATED,
                source_id="IMPACT_PROPAGATION_SERVICE",
                provider="Vulnerability & Exposure Engine",
                data={
                    "critical_assets_count": len([a for a in assets if a.risk_state == "HIGH_RISK"]),
                    "critical_assets_at_risk": len([a for a in assets if a.risk_state == "HIGH_RISK"]),
                    "population_exposed": pop_summary.population_exposed_forecast,
                    "newly_exposed_population": pop_summary.newly_exposed_population,
                    "population_summary": pop_summary.model_dump()
                },
                forecast_run_id=forecast_run_id,
                state_version=version,
                correlation_id=correlation_id,
                causation_id=ev_inun.event_id,
                priority=EventPriority.HIGH
            )
            await event_bus.publish(ev_impact)

            ev_impact_chg = OperationalEvent.create(
                event_type=EventType.IMPACT_CHANGE_DETECTED,
                source_id="IMPACT_PROPAGATION_SERVICE",
                provider="Vulnerability & Exposure Engine",
                data={
                    "assets": [a.model_dump() for a in assets],
                    "population_summary": pop_summary.model_dump(),
                    "newly_exposed_population": pop_summary.newly_exposed_population,
                    "dataset_state": pop_summary.dataset_state
                },
                forecast_run_id=forecast_run_id,
                state_version=version,
                correlation_id=correlation_id,
                causation_id=ev_impact.event_id,
                priority=EventPriority.HIGH
            )
            await event_bus.publish(ev_impact_chg)

        return curr_snap, change_summary, assets, pop_summary

# Global evolution service singleton
inundation_evolution_service = InundationEvolutionService()
