"""
Spatial Inundation Differencing & Expansion Rate Engine for JALDRISHTI AI.
Computes expansion, contraction, cell shifts, and expansion velocity between inundation snapshots.
"""

from typing import Dict, Any, Tuple
from datetime import datetime, timezone
import logging

from services.inundation_evolution.evolution_types import InundationSnapshot, SpatialChangeSummary

logger = logging.getLogger(__name__)

MIN_AREA_DELTA_SQKM = 2.0
MIN_PROB_DELTA = 0.03

class InundationDifferencingEngine:
    """
    Computes spatial shifts, delta extent, and expansion rates across sequential flood surfaces.
    """

    @staticmethod
    def compute_spatial_change(
        curr_snap: InundationSnapshot,
        prev_snap: InundationSnapshot,
        elapsed_hours: float = 1.0
    ) -> SpatialChangeSummary:
        """
        Calculates expansion, recession, and rate of change between two snapshots.
        """
        curr_area = curr_snap.inundated_area_sqkm
        prev_area = prev_snap.inundated_area_sqkm

        net_delta = round(curr_area - prev_area, 2)
        pct_change = round((net_delta / max(prev_area, 1.0)) * 100.0, 1)

        # Inundation expansion vs contraction breakdown
        if net_delta >= 0:
            expansion = net_delta
            contraction = 0.0
        else:
            expansion = 0.0
            contraction = abs(net_delta)

        # Expansion velocity in km²/hr
        rate_km2_hr = round(net_delta / max(elapsed_hours, 0.1), 2)

        # Material change gating
        is_material = (
            abs(net_delta) >= MIN_AREA_DELTA_SQKM or
            abs(curr_snap.mean_flood_probability - prev_snap.mean_flood_probability) >= MIN_PROB_DELTA
        )

        # Simulated cell counts (0.01 km² per grid cell)
        new_cells = int(expansion * 100)
        receded_cells = int(contraction * 100)
        unchanged_cells = int(min(curr_area, prev_area) * 100)

        trend = "EXPANDING" if net_delta > 2.0 else ("CONTRACTING" if net_delta < -2.0 else "STABLE")

        return SpatialChangeSummary(
            current_snapshot_id=curr_snap.snapshot_id,
            previous_snapshot_id=prev_snap.snapshot_id,
            expansion_sqkm=expansion,
            contraction_sqkm=contraction,
            net_delta_sqkm=net_delta,
            percentage_change=pct_change,
            inundation_expansion_rate_km2_per_hour=rate_km2_hr,
            spatial_trend=trend,
            rate_of_expansion_sqkm_per_hr=rate_km2_hr,
            net_change_sqkm=net_delta,
            new_cells_count=new_cells,
            receded_cells_count=receded_cells,
            unchanged_cells_count=unchanged_cells,
            is_material_change=is_material
        )
