"""
Demo State Dataclass and Runtime Snapshot Model.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from services.demo.demo_scenario import DEMO_SCENARIO_STAGES, DemoScenarioStage

@dataclass
class DemoState:
    is_active: bool = False
    is_playing: bool = False
    current_step: int = 0
    total_steps: int = len(DEMO_SCENARIO_STAGES)
    playback_speed: float = 1.0
    scenario_id: str = "DEMO-MAHANADI-STORM-01"
    scenario_name: str = "August 2020 Extreme Delta Flood & Inundation Surge"
    system_mode: str = "SIMULATION"
    data_state: str = "SYNTHETIC_DEMO"
    operator_review_acknowledged: bool = False
    affected_citizen_notified: bool = False
    outside_citizen_excluded: bool = True
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def current_stage(self) -> DemoScenarioStage:
        idx = max(0, min(self.total_steps - 1, self.current_step))
        return DEMO_SCENARIO_STAGES[idx]

    @property
    def next_stage_name(self) -> str:
        if self.current_step < self.total_steps - 1:
            return DEMO_SCENARIO_STAGES[self.current_step + 1].name
        return "SCENARIO_COMPLETE"

    def to_dict(self) -> Dict[str, Any]:
        stage = self.current_stage
        return {
            "is_active": self.is_active,
            "is_playing": self.is_playing,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "playback_speed": self.playback_speed,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "system_mode": self.system_mode,
            "data_state": self.data_state,
            "current_stage": {
                "index": stage.index,
                "stage_id": stage.stage_id,
                "name": stage.name,
                "headline": stage.headline,
                "description": stage.description,
                "rainfall_rate_mm_hr": stage.rainfall_rate_mm_hr,
                "rainfall_acc_6h_mm": stage.rainfall_acc_6h_mm,
                "river_stage_m": stage.river_stage_m,
                "river_discharge_cumec": stage.river_discharge_cumec,
                "inundated_area_sqkm": stage.inundated_area_sqkm,
                "exposed_population": stage.exposed_population,
                "exposed_villages": stage.exposed_villages,
                "risk_score": stage.risk_score,
                "previous_risk_score": stage.previous_risk_score,
                "material_risk_delta": stage.material_risk_delta,
                "top_causal_driver": stage.top_causal_driver,
                "alert_severity": stage.alert_severity.value,
                "requires_operator_review": stage.requires_operator_review and not self.operator_review_acknowledged,
                "is_notification_dispatched": stage.is_notification_dispatched,
                "data_confidence": stage.data_confidence.value
            },
            "next_stage": self.next_stage_name,
            "operator_review_acknowledged": self.operator_review_acknowledged,
            "affected_citizen_notified": self.affected_citizen_notified,
            "outside_citizen_excluded": self.outside_citizen_excluded,
            "last_updated": self.last_updated
        }
