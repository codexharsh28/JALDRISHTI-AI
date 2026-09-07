"""
Adapter Registry managing all active hydrometeorological providers.
"""

from typing import Dict, List, Any
from services.ingestion.adapters.base import BaseSourceAdapter
from services.ingestion.adapters.implementations import (
    IMDWeatherAdapter,
    DopplerRadarAdapter,
    MOSDACInsatAdapter,
    GPMImergAdapter,
    NWPWeatherAdapter,
    CWCHydrologyAdapter
)
from services.models import DataSourceHealth

class AdapterRegistry:
    def __init__(self, is_simulation: bool = True):
        self.adapters: Dict[str, BaseSourceAdapter] = {
            "IMD_AWS_ARG_ODISHA": IMDWeatherAdapter(is_simulation=is_simulation),
            "DOPPLER_RADAR_PARADIP": DopplerRadarAdapter(is_simulation=is_simulation),
            "MOSDAC_INSAT_3DR_HEM": MOSDACInsatAdapter(is_simulation=is_simulation),
            "NASA_GPM_IMERG_EARLY": GPMImergAdapter(is_simulation=is_simulation),
            "ECMWF_IFS_OPEN_DATA": NWPWeatherAdapter(is_simulation=is_simulation),
            "CWC_TELEMETRY_MAHANADI": CWCHydrologyAdapter(is_simulation=is_simulation)
        }

    def get(self, source_id: str) -> BaseSourceAdapter:
        return self.adapters.get(source_id)

    def get_adapter(self, source_id: str) -> BaseSourceAdapter:
        return self.adapters.get(source_id)

    def list_all(self) -> List[BaseSourceAdapter]:
        return list(self.adapters.values())

    def get_all_health(self) -> List[DataSourceHealth]:
        return [adapter.health_check() for adapter in self.adapters.values()]
