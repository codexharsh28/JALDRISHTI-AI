"""
Basin State Store for JALDRISHTI AI (Phase 17).
Maintains append-only history and fast querying of versioned Digital Basin States.
"""

from typing import Dict, Any, List, Optional
from collections import deque
import threading
import logging

from services.basin_state.basin_types import DigitalBasinState

logger = logging.getLogger(__name__)

class BasinStateStore:
    """
    Thread-safe in-memory store for Digital Basin States.
    """

    def __init__(self, max_history: int = 500):
        self._max_history = max_history
        self._history: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()

    def record_state(self, state: DigitalBasinState) -> None:
        with self._lock:
            self._history.append(state)

    def get_latest_state(self) -> Optional[DigitalBasinState]:
        with self._lock:
            if self._history:
                return self._history[-1]
            return None

    def get_history(self, limit: int = 50) -> List[DigitalBasinState]:
        with self._lock:
            return list(reversed(list(self._history)))[:limit]

# Global singleton instance
basin_state_store = BasinStateStore()
