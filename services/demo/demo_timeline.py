"""
Demo Timeline Formatting & Narrative Generation.
"""

from typing import List, Dict, Any
from services.demo.demo_scenario import DEMO_SCENARIO_STAGES

class DemoTimeline:
    """
    Produces structured scenario timeline representations for UI progress visualization.
    """

    @classmethod
    def get_full_timeline(cls) -> List[Dict[str, Any]]:
        timeline = []
        for stage in DEMO_SCENARIO_STAGES:
            timeline.append({
                "step_index": stage.index,
                "stage_id": stage.stage_id,
                "name": stage.name,
                "headline": stage.headline,
                "rainfall_mm_hr": stage.rainfall_rate_mm_hr,
                "stage_m": stage.river_stage_m,
                "inundation_sqkm": stage.inundated_area_sqkm,
                "risk_score": stage.risk_score,
                "severity": stage.alert_severity.value,
                "review_gate": stage.requires_operator_review
            })
        return timeline
