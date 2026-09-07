"""
Deterministic 11-Stage Historical Replay Engine for JALDRISHTI AI.
Simulates a complete causal flood event (Mahanadi Monsoon Event) with synchronized
subsystem states, deterministic random seeding, and variable playback speeds.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import numpy as np

from services.models import ReplayStepState, AlertSeverity, ConfidenceLevel

REPLAY_STAGES = [
    {"index": 0, "name": "NORMAL", "description": "Baseline dry-weather flow, isolated drizzle", "base_rain": 0.0},
    {"index": 1, "name": "RAINFALL_INCREASE", "description": "Convective storm cell develops over upstream catchment", "base_rain": 15.0},
    {"index": 2, "name": "HEAVY_RAIN", "description": "Extensive heavy precipitation (>35mm/h) across Delta", "base_rain": 42.0},
    {"index": 3, "name": "RUNOFF_INCREASE", "description": "Catchment soil saturation reaches 85%, rapid runoff generation", "base_rain": 68.0},
    {"index": 4, "name": "RIVER_RISING", "description": "Upstream barrage release surges to 22,000 cumecs, river rises +0.25m/h", "base_rain": 88.0},
    {"index": 5, "name": "THRESHOLD_APPROACH", "description": "Stage reaches Warning Level (25.40m) at Naraj Barrage", "base_rain": 110.0},
    {"index": 6, "name": "FLOOD_RISK_HIGH", "description": "Hydrodynamic models project breach danger within 6 hours", "base_rain": 135.0},
    {"index": 7, "name": "INUNDATION_EXPANSION", "description": "Embankment overtopping in Kathajodi lowlands, flood depth 0.8-1.5m", "base_rain": 160.0},
    {"index": 8, "name": "ALERT", "description": "RED Alert recommended: Mandatory human operator review gate triggered", "base_rain": 185.0},
    {"index": 9, "name": "PEAK", "description": "Flood wave crest reaches 26.85m (+0.55m above Danger Level), 215 km² inundated", "base_rain": 215.0},
    {"index": 10, "name": "RECOVERY", "description": "Rain stops, floodwaters recede gradually into Bay of Bengal", "base_rain": 140.0}
]

class ReplayEngine:
    def __init__(self):
        self.current_step = 0
        self.total_steps = len(REPLAY_STAGES)
        self.is_playing = False
        self.playback_speed = 1.0
        self.base_time = datetime(2020, 8, 26, 6, 0, tzinfo=timezone.utc)

    def get_all_events(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": "EVT-MAHANADI-2020-08",
                "name": "August 2020 Mahanadi Delta Extreme Flood Replay",
                "description": "Synchronized 11-stage historical storm and river surge scenario in Cuttack-Puri-Kendrapara-Jagatsinghpur districts.",
                "duration_hours": 84,
                "peak_stage_m": 26.85,
                "peak_inundation_sqkm": 215.4,
                "peak_rainfall_24h_mm": 284.0,
                "total_stages": self.total_steps
            }
        ]

    def get_current_state(self) -> ReplayStepState:
        rng = np.random.RandomState(42 + self.current_step)
        stage = REPLAY_STAGES[self.current_step]
        
        step_time = self.base_time + timedelta(hours=self.current_step * 7.5)
        
        rainfall_rate = [2.0, 12.0, 38.5, 48.0, 32.0, 24.0, 18.0, 12.0, 8.0, 4.0, 0.5][self.current_step]
        current_stage = [21.2, 21.5, 22.1, 23.0, 24.1, 25.4, 26.0, 26.4, 26.7, 26.85, 25.0][self.current_step]
        inundation_area = [0.0, 0.0, 8.5, 24.0, 56.0, 95.0, 142.0, 184.0, 208.0, 215.4, 88.0][self.current_step]

        if self.current_step >= 8:
            severity = AlertSeverity.RED
        elif self.current_step >= 5:
            severity = AlertSeverity.ORANGE
        elif self.current_step >= 2:
            severity = AlertSeverity.YELLOW
        else:
            severity = AlertSeverity.GREEN

        return ReplayStepState(
            step_index=self.current_step,
            total_steps=self.total_steps,
            stage_name=stage["name"],
            scenario_time=step_time,
            rainfall_mm_hr=round(rainfall_rate, 1),
            river_level_m=round(current_stage, 2),
            inundation_area_sqkm=round(inundation_area, 1),
            active_alert_severity=severity,
            data_confidence=ConfidenceLevel.HIGH,
            synced_narrative=stage["description"]
        )

    def step_forward(self) -> ReplayStepState:
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
        return self.get_current_state()

    def step_backward(self) -> ReplayStepState:
        if self.current_step > 0:
            self.current_step -= 1
        return self.get_current_state()

    def set_step(self, step: int) -> ReplayStepState:
        self.current_step = max(0, min(self.total_steps - 1, step))
        return self.get_current_state()

    def reset(self) -> ReplayStepState:
        self.current_step = 0
        self.is_playing = False
        return self.get_current_state()
