"""
Persistent Storage for Inundation Snapshots and Spatial Changes in JALDRISHTI AI (Phase 15).
"""

import json
import threading
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
from collections import deque

from services.inundation_evolution.evolution_types import (
    InundationSnapshot,
    SpatialChangeSummary,
    AssetExposureItem,
    PopulationExposureSummary
)

logger = logging.getLogger(__name__)

class InundationEvolutionStore:
    """
    Append-only persistent store for flood extent snapshots, spatial changes, and asset exposure.
    """

    def __init__(self, storage_dir: Optional[Any] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path("data/inundation_evolution")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        
        self._snapshots: deque = deque(maxlen=100)
        self._changes: deque = deque(maxlen=100)
        self._current_assets: List[AssetExposureItem] = []
        self._current_population: Optional[PopulationExposureSummary] = None
        self._load_persisted_history()

    def _load_persisted_history(self):
        """Hydrates previous inundation snapshots and spatial changes from persisted JSONL files."""
        try:
            jsonl_files = sorted(self.storage_dir.glob("inundation_evolution_*.jsonl"))
            for jfile in jsonl_files:
                with open(jfile, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "snapshot" in data and data["snapshot"]:
                                snap = InundationSnapshot.model_validate(data["snapshot"])
                                self._snapshots.append(snap)
                            if "change" in data and data["change"]:
                                chg = SpatialChangeSummary.model_validate(data["change"])
                                self._changes.append(chg)
                            if "assets" in data and data["assets"]:
                                self._current_assets = [AssetExposureItem.model_validate(a) for a in data["assets"]]
                            if "population" in data and data["population"]:
                                self._current_population = PopulationExposureSummary.model_validate(data["population"])
                        except Exception as rec_err:
                            logger.warning(f"Skipping malformed inundation record in {jfile}: {rec_err}")
            logger.info(f"Hydrated {len(self._snapshots)} inundation snapshots and {len(self._changes)} changes from disk.")
        except Exception as e:
            logger.warning(f"Notice during inundation history hydration: {e}")

    def append_snapshot(
        self,
        snapshot: InundationSnapshot,
        change: Optional[SpatialChangeSummary] = None,
        assets: Optional[List[AssetExposureItem]] = None,
        population: Optional[PopulationExposureSummary] = None
    ):
        with self._lock:
            self._snapshots.append(snapshot)
            if change:
                self._changes.append(change)
            if assets is not None:
                self._current_assets = assets
            if population is not None:
                self._current_population = population

            # Daily file persistence
            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            file_path = self.storage_dir / f"inundation_evolution_{today_str}.jsonl"
            try:
                with open(file_path, "a", encoding="utf-8") as f:
                    entry = {
                        "snapshot": snapshot.model_dump(),
                        "change": change.model_dump() if change else None,
                        "assets": [a.model_dump() for a in self._current_assets] if self._current_assets else None,
                        "population": population.model_dump() if population else None
                    }
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                logger.error(f"Failed to persist inundation snapshot {snapshot.snapshot_id}: {e}")

    def get_current_snapshot(self) -> Optional[InundationSnapshot]:
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None

    def get_previous_snapshot(self) -> Optional[InundationSnapshot]:
        with self._lock:
            return self._snapshots[-2] if len(self._snapshots) >= 2 else None

    def get_snapshots_history(self, limit: int = 20) -> List[InundationSnapshot]:
        with self._lock:
            return list(reversed(list(self._snapshots)))[:limit]

    def get_history(self, limit: int = 20) -> List[InundationSnapshot]:
        return self.get_snapshots_history(limit=limit)

    def get_snapshot_by_id(self, snapshot_id: str) -> Optional[InundationSnapshot]:
        with self._lock:
            for s in self._snapshots:
                if s.snapshot_id == snapshot_id or s.inundation_snapshot_id == snapshot_id:
                    return s
            return None

    def get_latest_change(self) -> Optional[SpatialChangeSummary]:
        with self._lock:
            return self._changes[-1] if self._changes else None

    def get_current_assets(self) -> List[AssetExposureItem]:
        with self._lock:
            return list(self._current_assets)

    def get_current_population(self) -> Optional[PopulationExposureSummary]:
        with self._lock:
            return self._current_population

# Global evolution store singleton
evolution_store = InundationEvolutionStore()
