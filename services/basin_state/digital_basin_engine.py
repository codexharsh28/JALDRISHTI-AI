"""
Digital Basin Twin Engine for JALDRISHTI AI (Phase 17).
Computes real-time dynamic evolution of soil moisture, channel storage routing,
barrage mass balances, and tidal boundary conditions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import math
import logging

from services.basin_state.basin_types import (
    SoilMoistureState,
    ChannelStorageState,
    BarrageStructure,
    BarrageOperationState,
    TidalBoundaryState,
    DigitalBasinState
)

logger = logging.getLogger(__name__)

class DigitalBasinEngine:
    """
    Simulates and tracks continuous physical basin state dynamics.
    """

    def __init__(self, basin_id: str = "pilot-mahanadi-delta"):
        self.basin_id = basin_id
        self._current_state: DigitalBasinState = self._initialize_default_state()

    def _initialize_default_state(self) -> DigitalBasinState:
        barrages = [
            BarrageStructure(
                structure_id="BAR-HIRAKUD-01",
                name="Hirakud Dam Spillway",
                location_lat=21.52,
                location_lon=83.87,
                total_gates=64,
                open_gates=24,
                upstream_stage_m=192.15,
                downstream_stage_m=160.40,
                discharge_cumec=14200.0,
                status="FLOOD_DISCHARGE"
            ),
            BarrageStructure(
                structure_id="BAR-MUNDALI-02",
                name="Mundali Weir (Delta Apex)",
                location_lat=20.44,
                location_lon=85.74,
                total_gates=44,
                open_gates=32,
                upstream_stage_m=28.40,
                downstream_stage_m=27.10,
                discharge_cumec=18500.0,
                status="FLOOD_DISCHARGE"
            ),
            BarrageStructure(
                structure_id="BAR-NARAJ-03",
                name="Naraj Barrage (Kathajodi Bifurcation)",
                location_lat=20.46,
                location_lon=85.77,
                total_gates=46,
                open_gates=30,
                upstream_stage_m=26.85,
                downstream_stage_m=25.90,
                discharge_cumec=11200.0,
                status="FLOOD_DISCHARGE"
            ),
            BarrageStructure(
                structure_id="BAR-JOBRA-04",
                name="Jobra Barrage (Cuttack City Reach)",
                location_lat=20.49,
                location_lon=85.90,
                total_gates=68,
                open_gates=42,
                upstream_stage_m=21.60,
                downstream_stage_m=20.80,
                discharge_cumec=7300.0,
                status="FLOOD_DISCHARGE"
            )
        ]

        return DigitalBasinState(
            basin_id=self.basin_id,
            version=1,
            soil_moisture=SoilMoistureState(),
            channel_storage=ChannelStorageState(),
            barrage_operations=BarrageOperationState(
                structures=barrages,
                total_delta_inflow_cumec=18500.0,
                total_delta_outflow_cumec=18500.0
            ),
            tidal_boundary=TidalBoundaryState(),
            effective_precipitation_mm_hr=12.5,
            basin_hydraulic_risk_index=68.5
        )

    def get_current_state(self) -> DigitalBasinState:
        return self._current_state

    def update_soil_moisture(
        self,
        fused_rain_mm_hr: float,
        dt_hours: float = 1.0,
        temp_c: float = 28.0
    ) -> SoilMoistureState:
        """
        Updates catchment soil saturation using Green-Ampt infiltration and Horton depletion.
        """
        curr = self._current_state.soil_moisture
        
        # Infiltration capacity decreases as saturation increases
        f_c = max(1.5, 18.0 * (1.0 - curr.saturation_index) ** 1.5)
        infiltration = min(fused_rain_mm_hr, f_c)
        effective_rain = max(0.0, fused_rain_mm_hr - infiltration)

        # Evapotranspiration depletion (mm/hr)
        et_rate = max(0.1, 0.05 * (temp_c / 25.0))
        
        # Net saturation delta
        recharge = (infiltration - et_rate * dt_hours) / 100.0
        new_sat = max(0.10, min(1.0, curr.saturation_index + recharge))
        
        # Moisture deficit (assuming 150mm total root zone capacity)
        new_deficit = max(0.0, 150.0 * (1.0 - new_sat))
        
        # API 30-day update: decay 0.92 daily (0.996 hourly) + new rainfall
        hourly_decay = math.exp(-0.08 / 24.0 * dt_hours)
        new_api = max(0.0, curr.antecedent_precipitation_index_30d * hourly_decay + fused_rain_mm_hr * dt_hours)

        updated = SoilMoistureState(
            saturation_index=round(new_sat, 3),
            antecedent_precipitation_index_30d=round(new_api, 1),
            moisture_deficit_mm=round(new_deficit, 1),
            infiltration_capacity_mm_hr=round(f_c, 2),
            spatial_saturation_grid_mean=round(new_sat * 0.96, 3)
        )
        self._current_state.soil_moisture = updated
        self._current_state.effective_precipitation_mm_hr = round(effective_rain, 2)
        return updated

    def update_channel_storage(
        self,
        inflow_cumec: float,
        outflow_cumec: float,
        dt_hours: float = 1.0,
        downstream_water_level_m: float = 2.30
    ) -> ChannelStorageState:
        """
        Updates reach channel storage volume via continuity: dV = (Q_in - Q_out) * dt.
        """
        curr = self._current_state.channel_storage
        
        # Delta volume in MCM (1 cumec * 3600s = 0.0036 MCM)
        delta_mcm = (inflow_cumec - outflow_cumec) * (3600.0 * dt_hours) / 1_000_000.0
        new_storage = max(50.0, min(curr.max_safe_storage_mcm * 1.35, curr.current_storage_mcm + delta_mcm))
        utilization = (new_storage / curr.max_safe_storage_mcm) * 100.0

        # Backwater head surcharge when downstream tidal level exceeds 2.0m MSL
        backwater_head = max(0.0, (downstream_water_level_m - 1.50) * 0.45)

        updated = ChannelStorageState(
            reach_id=curr.reach_id,
            reach_name=curr.reach_name,
            current_storage_mcm=round(new_storage, 1),
            max_safe_storage_mcm=curr.max_safe_storage_mcm,
            capacity_utilization_pct=round(utilization, 1),
            reach_travel_time_hours=round(max(6.0, 18.0 * (1.0 - (utilization / 200.0))), 1),
            backwater_head_m=round(backwater_head, 2)
        )
        self._current_state.channel_storage = updated
        return updated

    def update_barrage_operations(
        self,
        barrage_updates: List[Dict[str, Any]]
    ) -> BarrageOperationState:
        """
        Updates gate statuses and discharge rates across delta barrages.
        """
        curr_structures = {b.structure_id: b for b in self._current_state.barrage_operations.structures}
        
        for upd in barrage_updates:
            s_id = upd.get("structure_id")
            if s_id in curr_structures:
                struct = curr_structures[s_id]
                if "open_gates" in upd:
                    struct.open_gates = upd["open_gates"]
                if "discharge_cumec" in upd:
                    struct.discharge_cumec = upd["discharge_cumec"]
                if "upstream_stage_m" in upd:
                    struct.upstream_stage_m = upd["upstream_stage_m"]
                if "status" in upd:
                    struct.status = upd["status"]

        total_inflow = sum(b.discharge_cumec for b in curr_structures.values() if "MUNDALI" in b.structure_id)
        total_outflow = sum(b.discharge_cumec for b in curr_structures.values() if "JOBRA" in b.structure_id or "NARAJ" in b.structure_id)

        updated = BarrageOperationState(
            structures=list(curr_structures.values()),
            total_delta_inflow_cumec=round(total_inflow, 1),
            total_delta_outflow_cumec=round(total_outflow, 1)
        )
        self._current_state.barrage_operations = updated
        return updated

    def update_tidal_boundary(
        self,
        base_time: datetime,
        storm_surge_m: float = 0.45
    ) -> TidalBoundaryState:
        """
        Computes astronomical tide harmonic + storm surge residual at Paradip Estuary.
        """
        # Semi-diurnal M2 harmonic approximation (12.42 hour period)
        hours_since_epoch = base_time.timestamp() / 3600.0
        tide_phase_rad = (2.0 * math.pi * (hours_since_epoch % 12.42)) / 12.42
        
        # Mean sea level + 1.25m tidal amplitude
        astro_tide = 1.0 + 1.25 * math.sin(tide_phase_rad)
        total_level = astro_tide + storm_surge_m

        # Tidal phase name
        cos_rate = math.cos(tide_phase_rad)
        if cos_rate > 0.3:
            phase = "FLOOD_TIDE"
        elif cos_rate < -0.3:
            phase = "EBB_TIDE"
        elif math.sin(tide_phase_rad) > 0:
            phase = "HIGH_WATER_SLACK"
        else:
            phase = "LOW_WATER_SLACK"

        # Estuarine backwater length in km
        backwater_dist = max(5.0, min(50.0, 20.0 + total_level * 6.5))

        updated = TidalBoundaryState(
            station_id="TIDE-PARADIP-01",
            station_name="Paradip Port Estuary Gauge",
            astronomical_tide_m=round(astro_tide, 2),
            storm_surge_residual_m=round(storm_surge_m, 2),
            total_water_level_m=round(total_level, 2),
            tidal_phase=phase,
            backwater_propagation_km=round(backwater_dist, 1)
        )
        self._current_state.tidal_boundary = updated
        return updated

    def compute_full_digital_twin_step(
        self,
        fused_rain_mm_hr: float,
        inflow_cumec: float,
        outflow_cumec: float,
        storm_surge_m: float,
        base_time: datetime
    ) -> DigitalBasinState:
        """
        Advances the entire digital basin twin state by 1 step.
        """
        soil = self.update_soil_moisture(fused_rain_mm_hr=fused_rain_mm_hr)
        tide = self.update_tidal_boundary(base_time=base_time, storm_surge_m=storm_surge_m)
        channel = self.update_channel_storage(
            inflow_cumec=inflow_cumec,
            outflow_cumec=outflow_cumec,
            downstream_water_level_m=tide.total_water_level_m
        )

        # Compute aggregate hydraulic risk index (0 to 100)
        risk_index = min(100.0, (
            soil.saturation_index * 25.0 +
            (channel.capacity_utilization_pct / 100.0) * 45.0 +
            (tide.total_water_level_m / 3.50) * 30.0
        ))

        self._current_state.version += 1
        self._current_state.timestamp = base_time.isoformat()
        self._current_state.basin_hydraulic_risk_index = round(risk_index, 1)
        return self._current_state

# Global singleton instance
digital_basin_engine = DigitalBasinEngine()
