"""
Live Risk Evolution Service for JALDRISHTI AI.
Evaluates multi-hazard risk, tracks state versioning, decomposes causal changes,
and publishes RISK_STATE_CHANGED domain events.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent
from services.events.event_bus import event_bus
from services.runtime.current_state import current_state_manager
from services.risk.risk_types import RiskState, RiskLevel
from services.risk.risk_calculator import RiskCalculator
from services.risk.causal_explainer import CausalRiskExplainer
from services.risk.risk_store import risk_store

logger = logging.getLogger(__name__)

class RiskService:
    """
    Manages live risk recalculation and explainability pipeline.
    """

    def __init__(self):
        self._last_inputs: Dict[str, Any] = {
            "fused_rain_mm_hr": 24.5,
            "rain_24h_mm": 110.0,
            "river_stage_m": 25.80,
            "danger_stage_m": 26.30,
            "discharge_cumec": 14500.0,
            "flood_prob": 0.35,
            "inundated_area_sqkm": 280.0,
            "population_exposed": 45000,
            "critical_assets_exposed": 12,
            "data_confidence": "HIGH"
        }
        self._last_subscores: Dict[str, float] = {
            "meteorological": 10.0,
            "hydrological": 12.0,
            "inundation": 8.0,
            "exposure": 4.5,
            "confidence_adjustment": 0.0
        }
        self._last_score: float = 34.5

    def initialize(self):
        """Subscribe to forecast and impact completion events."""
        event_bus.subscribe(EventType.IMPACT_UPDATED, self._on_impact_updated)

    async def _on_impact_updated(self, event: OperationalEvent):
        """Re-evaluate risk state on impact updates."""
        data = event.data or {}
        forecast_run_id = event.forecast_run_id or "FR-DEFAULT"

        inputs = {
            "fused_rain_mm_hr": 28.5,
            "rain_24h_mm": 142.0,
            "river_stage_m": 26.85,
            "danger_stage_m": 26.30,
            "discharge_cumec": 18560.0,
            "flood_prob": 0.88,
            "inundated_area_sqkm": 418.8,
            "population_exposed": data.get("population_exposed", 128450),
            "critical_assets_exposed": data.get("critical_assets_at_risk", 24),
            "data_confidence": "HIGH"
        }

        await self.evaluate_and_publish_risk(inputs, forecast_run_id, correlation_id=event.correlation_id)

    async def evaluate_and_publish_risk(
        self,
        inputs: Dict[str, Any],
        forecast_run_id: str,
        correlation_id: Optional[str] = None
    ) -> RiskState:
        """
        Executes risk calculation, causal decomposition, persistence, and event emission.
        """
        new_score, risk_level, subscores = RiskCalculator.calculate_risk_score(
            fused_rain_mm_hr=inputs.get("fused_rain_mm_hr", 0.0),
            rain_24h_mm=inputs.get("rain_24h_mm", 0.0),
            river_stage_m=inputs.get("river_stage_m", 0.0),
            danger_stage_m=inputs.get("danger_stage_m", 26.30),
            discharge_cumec=inputs.get("discharge_cumec", 0.0),
            flood_prob=inputs.get("flood_prob", 0.0),
            inundated_area_sqkm=inputs.get("inundated_area_sqkm", 0.0),
            population_exposed=inputs.get("population_exposed", 0),
            critical_assets_exposed=inputs.get("critical_assets_exposed", 0),
            data_confidence=inputs.get("data_confidence", "HIGH")
        )

        delta = round(new_score - self._last_score, 1)
        is_material = RiskCalculator.is_material_change(
            prev_score=self._last_score,
            new_score=new_score,
            prev_prob=self._last_inputs.get("flood_prob", 0.0),
            new_prob=inputs.get("flood_prob", 0.0),
            prev_area=self._last_inputs.get("inundated_area_sqkm", 0.0),
            new_area=inputs.get("inundated_area_sqkm", 0.0),
            prev_stage=self._last_inputs.get("river_stage_m", 0.0),
            new_stage=inputs.get("river_stage_m", 0.0)
        )

        # Decompose causal factors
        contributors = CausalRiskExplainer.explain_risk_change(
            prev_inputs=self._last_inputs,
            new_inputs=inputs,
            prev_subscores=self._last_subscores,
            new_subscores=subscores,
            total_delta=delta
        )

        top_summary = "; ".join([c.explanation for c in contributors[:2]]) if contributors else "Stable baseline indicators"

        version = current_state_manager.increment_state_version()

        state = RiskState(
            state_version=version,
            risk_score=new_score,
            previous_risk_score=self._last_score,
            risk_level=risk_level,
            risk_change=delta,
            is_material_change=is_material,
            contributors=contributors,
            top_causal_summary=top_summary,
            forecast_run_id=forecast_run_id,
            data_confidence=inputs.get("data_confidence", "HIGH")
        )

        risk_store.append(state)

        # Update cache
        self._last_inputs = inputs
        self._last_subscores = subscores
        self._last_score = new_score

        # Emit RISK_STATE_CHANGED event
        priority = EventPriority.CRITICAL if risk_level == RiskLevel.CRITICAL else EventPriority.HIGH
        ev = OperationalEvent.create(
            event_type=EventType.RISK_STATE_CHANGED,
            source_id="RISK_EVOLUTION_SERVICE",
            provider="JALDRISHTI Risk & Explainability Engine",
            data=state.model_dump(),
            state_version=version,
            forecast_run_id=forecast_run_id,
            correlation_id=correlation_id,
            priority=priority
        )
        await event_bus.publish(ev)

        return state

# Global risk service singleton
risk_service = RiskService()
