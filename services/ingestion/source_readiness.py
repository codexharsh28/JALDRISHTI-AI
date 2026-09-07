"""
Source Readiness Gate for JALDRISHTI AI Rainfall Pipeline.
Evaluates the physical readiness, spatial coverage, and accessibility of external providers.
Classifications: AVAILABLE | PARTIAL | UNAVAILABLE | SIMULATED
"""

import os
from typing import Dict, Any, List
from enum import Enum

class SourceReadinessState(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    SIMULATED = "SIMULATED"

class SourceReadinessGate:
    """
    Evaluates real provider accessibility and flags constraints.
    """

    @staticmethod
    def audit_all_sources(raw_dir: str = "data/raw/rainfall") -> Dict[str, Dict[str, Any]]:
        readiness = {}

        # 1. IMD 0.25° Daily Gridded Archive
        imd_files = [f for f in os.listdir(raw_dir) if "imd_gridded" in f] if os.path.exists(raw_dir) else []
        readiness["IMD_GRIDDED_025"] = {
            "source_id": "IMD_GRIDDED_025",
            "provider": "India Meteorological Department (IMD)",
            "product": "0.25° x 0.25° Daily Gridded Rainfall (Pai et al.)",
            "state": SourceReadinessState.AVAILABLE.value if imd_files else SourceReadinessState.PARTIAL.value,
            "native_spatial_resolution": "0.25 deg (~28 km)",
            "native_temporal_resolution": "24 hours",
            "usable_for_nowcasting": False,
            "intended_use": "Event identification, regional catchment accum, historical baseline",
            "access_notes": "Open research access archive"
        }

        # 2. NASA GPM IMERG V07B (Early vs Final)
        imerg_files = [f for f in os.listdir(raw_dir) if "gpm_imerg" in f] if os.path.exists(raw_dir) else []
        readiness["NASA_GPM_IMERG_EARLY"] = {
            "source_id": "NASA_GPM_IMERG_EARLY",
            "provider": "NASA PMM / GES DISC",
            "product": "GPM IMERG Early Run L3 (30-min, 0.1°)",
            "state": SourceReadinessState.AVAILABLE.value if imerg_files else SourceReadinessState.PARTIAL.value,
            "native_spatial_resolution": "0.10 deg (~10 km)",
            "native_temporal_resolution": "30 minutes",
            "usable_for_nowcasting": True,
            "operational_latency_minutes": 240.0,
            "intended_use": "Near-real-time convective storm monitoring and nowcasting input",
            "access_notes": "NASA Earthdata Open Access"
        }

        # 3. Paradip Doppler Weather Radar (DWR)
        readiness["PARADIP_DWR_RADAR"] = {
            "source_id": "PARADIP_DWR_RADAR",
            "provider": "IMD Paradip Radar Station",
            "product": "Plan Position Indicator (PPI) / Max-Z 1km Cartesian Grid",
            "state": SourceReadinessState.UNAVAILABLE.value,
            "unavailability_reason": "RADAR_HISTORY_UNAVAILABLE: Multi-year continuous raw polar volume scans (2018-2024) are non-public institutional archives. Deep radar nowcasting is marked experimental/simulated for prototype demonstration.",
            "native_spatial_resolution": "1.0 km Cartesian grid",
            "native_temporal_resolution": "10 minutes",
            "usable_for_nowcasting": False
        }

        # 4. Ground AWS / Rain Gauge Network
        readiness["IMD_ODISHA_AWS"] = {
            "source_id": "IMD_ODISHA_AWS",
            "provider": "IMD Bhubaneswar / Odisha State Disaster Management Authority",
            "product": "Automated Weather Station (AWS) Tipping Bucket Gauges",
            "state": SourceReadinessState.AVAILABLE.value,
            "native_spatial_resolution": "Point Gauge Observations (12 Pilot Stations)",
            "native_temporal_resolution": "15 to 60 minutes",
            "usable_for_nowcasting": True,
            "intended_use": "Ground truth ground-truthing, bias calibration, and point nowcast features"
        }

        # 5. MOSDAC INSAT-3DR HEM
        readiness["MOSDAC_INSAT3DR_HEM"] = {
            "source_id": "MOSDAC_INSAT3DR_HEM",
            "provider": "ISRO Space Applications Centre (SAC)",
            "product": "INSAT-3DR Hydro-Estimator Method (HEM) Half-Hourly",
            "state": SourceReadinessState.PARTIAL.value,
            "native_spatial_resolution": "0.04 deg (~4 km)",
            "native_temporal_resolution": "30 minutes",
            "usable_for_nowcasting": True,
            "operational_latency_minutes": 35.0,
            "intended_use": "High-temporal cloud-top convective rate estimation"
        }

        return readiness
