"""
Live Ingestion Scheduler for JALDRISHTI AI.
Manages provider-specific cadences, backoff retries, and raw caching in data/raw/live/.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

from services.ingestion.live_interfaces import BaseLiveProvider, IngestionRunRecord, IngestionMode, SourceState
from services.ingestion.live_adapters import (
    IMDLiveAdapter,
    IMERGEarlyAdapter,
    INSATAdapter,
    NWPLiveAdapter,
    HydrologyLiveAdapter,
    RadarLiveAdapter,
    MockLiveProvider
)
from services.ingestion.live.glofas_adapter import GloFASLiveAdapter

logger = logging.getLogger(__name__)

RAW_LIVE_CACHE_DIR = Path("data/raw/live")
RAW_LIVE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class LiveScheduler:
    """Manages scheduled and polled live data ingestion."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiveScheduler, cls).__new__(cls)
            cls._instance._init_scheduler()
        return cls._instance

    def _init_scheduler(self):
        self.providers: Dict[str, BaseLiveProvider] = {
            "IMD_ODISHA_AWS": IMDLiveAdapter(),
            "NASA_GPM_IMERG_EARLY": IMERGEarlyAdapter(),
            "ISRO_MOSDAC_INSAT3DR": INSATAdapter(),
            "ECMWF_OPEN_DATA_NWP": NWPLiveAdapter("ECMWF"),
            "CWC_WRIS_TELEMETRY": HydrologyLiveAdapter(),
            "GLOFAS_OPEN_METEO_FLOOD": GloFASLiveAdapter(),
            "IMD_DWR_PARADIP": RadarLiveAdapter(),
            "MOCK_LIVE_SIMULATOR": MockLiveProvider()
        }
        self._last_fetch_timestamps: Dict[str, datetime] = {}
        self._ingestion_history: List[IngestionRunRecord] = []
        self._latest_observations: Dict[str, Any] = {}

    def poll_provider(self, provider_id: str, force: bool = False) -> Optional[IngestionRunRecord]:
        """Polls an individual provider respecting its minimum refresh interval."""
        provider = self.providers.get(provider_id)
        if not provider:
            logger.warning(f"Provider {provider_id} not registered.")
            return None

        now = datetime.now(timezone.utc)
        last_fetch = self._last_fetch_timestamps.get(provider_id)

        # Enforce minimum refresh cadence
        if not force and last_fetch:
            elapsed = (now - last_fetch).total_seconds()
            if elapsed < provider.meta.minimum_refresh_interval_seconds:
                logger.info(
                    f"Rate limiting {provider_id}: elapsed {elapsed}s < min {provider.meta.minimum_refresh_interval_seconds}s"
                )
                return None

        try:
            result = provider.fetch()
            self._last_fetch_timestamps[provider_id] = now
            self._ingestion_history.append(result.ingestion_run)
            self._latest_observations[provider_id] = result

            # Cache raw response
            self._cache_raw_payload(result.ingestion_run, result.observations)

            # Cap in-memory history to last 200 runs
            if len(self._ingestion_history) > 200:
                self._ingestion_history = self._ingestion_history[-200:]

            return result.ingestion_run
        except Exception as e:
            logger.error(f"Error fetching from {provider_id}: {e}")
            return None

    def poll_all_due_providers(self) -> List[IngestionRunRecord]:
        """Runs due ingestion cycles across all configured providers."""
        runs: List[IngestionRunRecord] = []
        now = datetime.now(timezone.utc)

        for pid, provider in self.providers.items():
            last_fetch = self._last_fetch_timestamps.get(pid)
            is_due = False
            if last_fetch is None:
                is_due = True
            else:
                elapsed = (now - last_fetch).total_seconds()
                if elapsed >= provider.meta.refresh_interval_seconds:
                    is_due = True

            if is_due:
                run = self.poll_provider(pid)
                if run:
                    runs.append(run)
        return runs

    def force_refresh_all(self) -> List[IngestionRunRecord]:
        """Force refreshes all providers (e.g. operator manual trigger)."""
        runs = []
        for pid in self.providers.keys():
            run = self.poll_provider(pid, force=True)
            if run:
                runs.append(run)
        return runs

    def get_latest_observations(self) -> Dict[str, Any]:
        return self._latest_observations

    def get_ingestion_history(self, limit: int = 50) -> List[IngestionRunRecord]:
        return self._ingestion_history[-limit:]

    def get_provider_health_summary(self) -> List[Dict[str, Any]]:
        summary = []
        for pid, provider in self.providers.items():
            h = provider.health_check()
            last_run = self._find_last_run(pid)
            summary.append({
                "provider_id": pid,
                "product_id": provider.meta.product_id,
                "ingestion_mode": provider.meta.ingestion_mode.value,
                "refresh_interval_seconds": provider.meta.refresh_interval_seconds,
                "status": h["status"],
                "last_success": h["last_success"],
                "last_failure": h["last_failure"],
                "consecutive_failures": h["consecutive_failures"],
                "last_ingestion_run_id": last_run.ingestion_run_id if last_run else None,
                "last_records_received": last_run.records_received if last_run else 0,
                "last_latency_ms": last_run.latency_ms if last_run else 0.0,
                "data_state": last_run.data_state if last_run else "NOT_CONFIGURED"
            })
        return summary

    def _find_last_run(self, provider_id: str) -> Optional[IngestionRunRecord]:
        for r in reversed(self._ingestion_history):
            if r.source_id == provider_id:
                return r
        return None

    def _cache_raw_payload(self, run: IngestionRunRecord, payload: Any):
        try:
            cache_file = RAW_LIVE_CACHE_DIR / f"{run.ingestion_run_id}.json"
            record = {
                "ingestion_run_id": run.ingestion_run_id,
                "source_id": run.source_id,
                "provider": run.provider,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat(),
                "latency_ms": run.latency_ms,
                "payload_hash": run.payload_hash,
                "records_count": len(payload) if isinstance(payload, list) else 1,
                "raw_payload": payload
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache raw live payload {run.ingestion_run_id}: {e}")

# Global scheduler instance
live_scheduler = LiveScheduler()
