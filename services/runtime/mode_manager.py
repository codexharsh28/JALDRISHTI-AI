"""
Centralized Runtime Operating Mode Manager for JALDRISHTI AI.
Strictly separates System Mode (SIMULATION, REPLAY, LIVE), Data State, and Map State.
Enforces fail-safe safety confirmation before engaging LIVE mode.
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

class SystemMode(str, Enum):
    SIMULATION = "SIMULATION"
    REPLAY = "REPLAY"
    LIVE = "LIVE"

class DataState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    OFFLINE = "OFFLINE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    MOCK_LIVE = "MOCK_LIVE"
    SYNTHETIC = "SYNTHETIC"
    REAL_HISTORICAL = "REAL_HISTORICAL"

class MapState(str, Enum):
    LIVE_MAP = "LIVE_MAP"
    OFFLINE_MAP = "OFFLINE_MAP"

class RuntimeModeStatus(BaseModel):
    system_mode: SystemMode
    data_state: DataState
    map_state: MapState
    active_scenario_id: Optional[str] = None
    replay_event_id: Optional[str] = None
    live_ingestion_active: bool = False
    data_confidence: str  # "HIGH", "MEDIUM", "LOW", "DATA_DEGRADED"
    last_mode_change_at: datetime
    operator_notice: str

class ModeManager:
    """Singleton Mode Manager."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModeManager, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        # Default mode is unconditionally SIMULATION
        self._system_mode = SystemMode.SIMULATION
        self._data_state = DataState.SYNTHETIC
        self._map_state = MapState.LIVE_MAP
        self._active_scenario_id = "SCENARIO-MONSOON-SURGE-2026"
        self._replay_event_id = None
        self._live_ingestion_active = False
        self._data_confidence = "HIGH"
        self._last_change = datetime.now(timezone.utc)
        self._operator_notice = "System operating in default deterministic SIMULATION mode. Zero external data feeds connected."

    def get_status(self) -> RuntimeModeStatus:
        return RuntimeModeStatus(
            system_mode=self._system_mode,
            data_state=self._data_state,
            map_state=self._map_state,
            active_scenario_id=self._active_scenario_id,
            replay_event_id=self._replay_event_id,
            live_ingestion_active=self._live_ingestion_active,
            data_confidence=self._data_confidence,
            last_mode_change_at=self._last_change,
            operator_notice=self._operator_notice
        )

    def switch_to_simulation(self, scenario_id: str = "SCENARIO-MONSOON-SURGE-2026") -> RuntimeModeStatus:
        self._system_mode = SystemMode.SIMULATION
        self._data_state = DataState.SYNTHETIC
        self._active_scenario_id = scenario_id
        self._replay_event_id = None
        self._live_ingestion_active = False
        self._data_confidence = "HIGH"
        self._last_change = datetime.now(timezone.utc)
        self._operator_notice = f"Operating in SIMULATION mode ({scenario_id}). Output is synthetic holdout benchmark data."
        return self.get_status()

    def switch_to_replay(self, event_id: str = "EVT-MAHANADI-2022-08") -> RuntimeModeStatus:
        self._system_mode = SystemMode.REPLAY
        self._data_state = DataState.REAL_HISTORICAL
        self._replay_event_id = event_id
        self._active_scenario_id = None
        self._live_ingestion_active = False
        self._data_confidence = "HIGH"
        self._last_change = datetime.now(timezone.utc)
        self._operator_notice = f"Operating in REPLAY mode for event {event_id}. Output is real historical hindcast."
        return self.get_status()

    def switch_to_live(self, operator_confirmation: bool = False) -> RuntimeModeStatus:
        if not operator_confirmation:
            raise ValueError(
                "SAFETY LOCK: Explicit operator confirmation is mandatory before switching to LIVE mode. "
                "Notice: LIVE DATA MAY BE DELAYED OR DEGRADED."
            )
        
        self._system_mode = SystemMode.LIVE
        self._active_scenario_id = None
        self._replay_event_id = None
        self._live_ingestion_active = True
        self._last_change = datetime.now(timezone.utc)
        
        # In LIVE mode, evaluate real data state
        self._data_state = DataState.HEALTHY
        self._data_confidence = "MEDIUM"  # Never blindly assert HIGH in live mode without verifying all feeds
        self._operator_notice = (
            "Operating in LIVE OPERATIONAL mode. External hydromet feeds active. "
            "Decision support only — not an official government warning system."
        )
        return self.get_status()

    def update_data_health_state(self, source_states: Dict[str, str], confidence: str):
        """Updates data state according to actual external feed health."""
        if self._system_mode != SystemMode.LIVE:
            return

        unavailable_count = sum(1 for s in source_states.values() if s in ["OFFLINE", "UNAVAILABLE", "NOT_CONFIGURED"])
        degraded_count = sum(1 for s in source_states.values() if s in ["DEGRADED", "STALE"])

        if unavailable_count >= len(source_states) / 2:
            self._data_state = DataState.DEGRADED
            self._data_confidence = "DATA_DEGRADED"
        elif degraded_count > 0:
            self._data_state = DataState.DEGRADED
            self._data_confidence = "LOW"
        else:
            self._data_state = DataState.HEALTHY
            self._data_confidence = confidence

    def set_map_state(self, is_online: bool):
        self._map_state = MapState.LIVE_MAP if is_online else MapState.OFFLINE_MAP

# Global mode manager instance
mode_manager = ModeManager()
