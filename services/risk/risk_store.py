"""
Persistent Risk State Store for JALDRISHTI AI.
Appends versioned RiskState snapshots to daily JSONL files.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import threading
from collections import deque

from services.risk.risk_types import RiskState

logger = logging.getLogger(__name__)

class RiskStore:
    """
    Append-only persistent store for versioned basin risk states.
    """

    def __init__(self, storage_dir: Optional[Any] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path("data/risk")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._history: deque = deque(maxlen=200)
        self._states_by_id: Dict[str, RiskState] = {}
        self._current_state: Optional[RiskState] = None
        self._load_persisted_history()

    def _load_persisted_history(self):
        """Hydrates previous risk states from persisted JSONL files."""
        try:
            jsonl_files = sorted(self.storage_dir.glob("risk_history_*.jsonl"))
            for jfile in jsonl_files:
                with open(jfile, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            st = RiskState.model_validate_json(line)
                            self._history.append(st)
                            self._states_by_id[st.risk_state_id] = st
                            self._current_state = st
                        except Exception as rec_err:
                            logger.warning(f"Skipping malformed risk record in {jfile}: {rec_err}")
            logger.info(f"Hydrated {len(self._history)} risk states from disk.")
        except Exception as e:
            logger.warning(f"Notice during risk history hydration: {e}")

    def clear_demo_states(self):
        """Cleans up synthetic demonstration risk states to prevent leakage into live state."""
        with self._lock:
            self._history = deque([s for s in self._history if not s.risk_state_id.startswith("RSK-DEMO")], maxlen=200)
            self._states_by_id = {k: v for k, v in self._states_by_id.items() if not k.startswith("RSK-DEMO")}
            self._current_state = self._history[-1] if self._history else None

    def append(self, state: RiskState) -> bool:
        """Appends a new risk state to history."""
        with self._lock:
            self._history.append(state)
            self._states_by_id[state.risk_state_id] = state
            self._current_state = state

            # Append to daily file
            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            file_path = self.storage_dir / f"risk_history_{today_str}.jsonl"
            try:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(state.model_dump_json() + "\n")
                return True
            except Exception as e:
                logger.error(f"Failed to persist risk state {state.risk_state_id}: {e}")
                return False

    def get_current(self) -> Optional[RiskState]:
        with self._lock:
            return self._current_state

    def get_by_id(self, risk_state_id: str) -> Optional[RiskState]:
        with self._lock:
            return self._states_by_id.get(risk_state_id)

    def get_history(self, limit: int = 50) -> List[RiskState]:
        with self._lock:
            return list(reversed(list(self._history)))[:limit]

# Global risk store singleton
risk_store = RiskStore()
