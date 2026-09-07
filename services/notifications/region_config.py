"""
Multi-Region Deployment Configuration for JALDRISHTI AI Public Alerts.
Decouples core notification and geofencing engines from specific basin names,
supporting pilot deployment in Mahanadi Delta, Odisha and future extensions to other basins.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import os
import yaml

class RegionalDeploymentConfig(BaseModel):
    region_id: str = "MAHANADI_DELTA"
    region_name: str = "Mahanadi Delta"
    state: str = "Odisha"
    country: str = "India"
    bounding_box: Dict[str, float] = Field(default_factory=lambda: {
        "min_lat": 19.80,
        "max_lat": 21.00,
        "min_lon": 85.00,
        "max_lon": 87.00
    })
    default_safety_buffer_km: float = 15.0
    authority_name: str = "Odisha State Disaster Management Authority (OSDMA) / Special Relief Commissioner"
    authority_short: str = "OSDMA / DDMA"

class RegionConfigManager:
    """
    Manages regional deployment metadata dynamically loaded from basin_config.yaml or environment.
    """

    def __init__(self, config_path: str = "basin_config.yaml"):
        self.config_path = config_path
        self._current_config = self._load_config()

    def _load_config(self) -> RegionalDeploymentConfig:
        region_id = os.getenv("DEPLOYMENT_REGION_ID")
        region_name = os.getenv("DEPLOYMENT_REGION_NAME")
        state = os.getenv("DEPLOYMENT_STATE")
        
        if region_id and region_name and state:
            return RegionalDeploymentConfig(
                region_id=region_id,
                region_name=region_name,
                state=state,
                country=os.getenv("DEPLOYMENT_COUNTRY", "India")
            )

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                    basin = cfg.get("basin", {})
                    raw_state = basin.get("state", "Odisha")
                    clean_state = raw_state.split(",")[0].strip() if raw_state else "Odisha"
                    return RegionalDeploymentConfig(
                        region_id=basin.get("id", "MAHANADI_DELTA").upper().replace("-", "_"),
                        region_name="Mahanadi Delta",
                        state=clean_state,
                        country=basin.get("country", "India"),
                        bounding_box={
                            "min_lat": basin.get("bounds", {}).get("min_lat", 19.80),
                            "max_lat": basin.get("bounds", {}).get("max_lat", 21.00),
                            "min_lon": basin.get("bounds", {}).get("min_lon", 85.00),
                            "max_lon": basin.get("bounds", {}).get("max_lon", 87.00)
                        }
                    )
            except Exception:
                pass

        return RegionalDeploymentConfig()

    @property
    def current_region(self) -> RegionalDeploymentConfig:
        return self._current_config

    def get_public_metadata(self) -> Dict[str, Any]:
        return {
            "region_id": self._current_config.region_id,
            "region_name": self._current_config.region_name,
            "state": self._current_config.state,
            "country": self._current_config.country,
            "authority_guidance_entity": self._current_config.authority_short,
            "is_pilot_deployment": ("MAHANADI_DELTA" in self._current_config.region_id)
        }

# Global singleton
region_config_manager = RegionConfigManager()
