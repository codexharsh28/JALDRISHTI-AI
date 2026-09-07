"""
Base Source Adapter Specification for JALDRISHTI AI.
All data ingestion providers must adhere to this abstract contract.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from services.models import DataSourceHealth, SourceStatus, ConfidenceLevel, ProvenanceMetadata, QualityFlag

Tuple_bool_anomalies = Tuple[bool, Dict[str, str]]

class BaseSourceAdapter(ABC):
    def __init__(self, source_id: str, provider: str, product_name: str, is_simulation: bool = True):
        self.source_id = source_id
        self.provider = provider
        self.product_name = product_name
        self.is_simulation = is_simulation
        self.last_fetch_time: Optional[datetime] = None
        self.last_status = SourceStatus.HEALTHY
        self.quality_flag = QualityFlag.GOOD
        self.latency_seconds = 60.0
        self.quality_score = 0.95
        self.error_count = 0
        self.total_fetches = 0

    @property
    def status(self) -> SourceStatus:
        return self.last_status

    @status.setter
    def status(self, val: SourceStatus):
        self.last_status = val

    @abstractmethod
    async def fetch(self, basin_bounds: Dict[str, float], timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch raw payload from external endpoint or fallback simulation."""
        pass

    @abstractmethod
    def validate(self, raw_data: Dict[str, Any]) -> Tuple_bool_anomalies:
        """Validate structure, schema, CRS, and timestamp."""
        pass

    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize raw units and formats into standardized canonical records."""
        pass

    def health_check(self) -> DataSourceHealth:
        """Return standardized data source health & confidence metrics."""
        now = datetime.now(timezone.utc)
        last_up = self.last_fetch_time or now
        latency = (now - last_up).total_seconds()
        
        # Calculate data confidence
        if self.last_status == SourceStatus.HEALTHY and self.quality_score >= 0.85:
            conf = ConfidenceLevel.HIGH
        elif self.last_status == SourceStatus.DEGRADED or (0.60 <= self.quality_score < 0.85):
            conf = ConfidenceLevel.MEDIUM
        elif self.last_status == SourceStatus.STALE:
            conf = ConfidenceLevel.DATA_DEGRADED
        else:
            conf = ConfidenceLevel.LOW

        return DataSourceHealth(
            source_id=self.source_id,
            provider=self.provider,
            product_name=self.product_name,
            status=self.last_status,
            last_update=last_up,
            latency_seconds=round(max(self.latency_seconds, latency), 1),
            coverage_pct=100.0 if self.last_status != SourceStatus.OFFLINE else 0.0,
            missingness_pct=round((1.0 - self.quality_score) * 100.0, 1),
            quality_score=round(self.quality_score, 2),
            fallback_active=self.is_simulation,
            data_confidence=conf,
            is_simulation=self.is_simulation,
            error_message=None if self.last_status == SourceStatus.HEALTHY else "Operating in fallback simulation mode"
        )

    def metadata(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "provider": self.provider,
            "product_name": self.product_name,
            "is_simulation": self.is_simulation,
            "quality_score": self.quality_score
        }
