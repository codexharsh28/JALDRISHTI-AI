"""
High-Level Inundation Forecasting & SAR Reference Service for JALDRISHTI AI.
Applies rigorous 9-point scientific provenance tracking, model status lifecycle (CANDIDATE default),
extent vs depth decoupling, and temporal SAR matching verification.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from services.models import (
    InundationTileSummary,
    InundationProvenance,
    SARReferenceComparison,
    ModelStatus,
    DepthStatus,
    DepthValidationStatus,
    TemporalMatchStatus,
    ProvenanceMetadata
)
from ml.inundation.hydraulic_surrogate import HydraulicSurrogateModel
from ml.inundation.sar_reference import evaluate_sar_flood_reference, validate_sar_temporal_window

class InundationService:
    def __init__(self, surrogate_model: Optional[HydraulicSurrogateModel] = None):
        self.surrogate = surrogate_model or HydraulicSurrogateModel()

    def generate_inundation_forecast(
        self,
        peak_river_stage_m: float,
        danger_level_m: float,
        rainfall_accumulation_24h_mm: float,
        forecast_valid_time: datetime,
        lead_time_hours: float,
        rainfall_run_id: Optional[str] = None,
        hydrology_run_id: Optional[str] = None,
        sar_reference_record: Optional[Dict[str, Any]] = None
    ) -> InundationTileSummary:
        """
        Executes 2D inundation surrogate forecast and encapsulates full 9-point provenance,
        calibrated probability surfaces, and optional SAR Reference comparison.
        """
        inundation_run_id = f"INUND-RUN-{uuid.uuid4().hex[:8].upper()}"

        tile_summary = self.surrogate.predict_inundation(
            peak_river_stage_m=peak_river_stage_m,
            danger_level_m=danger_level_m,
            rainfall_accumulation_24h_mm=rainfall_accumulation_24h_mm,
            forecast_run_id=inundation_run_id,
            valid_time=forecast_valid_time,
            lead_time_hours=lead_time_hours
        )

        # Build SAR comparison if reference record is provided
        sar_comparison: Optional[SARReferenceComparison] = None
        if sar_reference_record:
            sar_acq_time = sar_reference_record.get("acquisition_time")
            if isinstance(sar_acq_time, str):
                sar_acq_time = datetime.fromisoformat(sar_acq_time.replace("Z", "+00:00"))
            
            time_diff, match_status = validate_sar_temporal_window(
                forecast_time=forecast_valid_time,
                sar_time=sar_acq_time,
                max_tolerance_hours=3.0
            )

            metrics = evaluate_sar_flood_reference(
                observed_extent_sqkm=sar_reference_record["observed_extent_sqkm"],
                predicted_extent_sqkm=tile_summary.inundated_area_sqkm
            )

            sar_comparison = SARReferenceComparison(
                event_id=sar_reference_record.get("event_id", "UNKNOWN-EVENT"),
                forecast_valid_time=forecast_valid_time,
                sar_acquisition_time=sar_acq_time,
                time_difference_hours=round(time_diff, 2),
                temporal_match_status=match_status,
                observed_extent_sqkm=round(sar_reference_record["observed_extent_sqkm"], 1),
                predicted_extent_sqkm=round(tile_summary.inundated_area_sqkm, 1),
                iou=metrics["iou"],
                f1=metrics["f1"],
                csi=metrics["csi"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                depth_status=DepthStatus.MODEL_ESTIMATE,
                depth_validation=DepthValidationStatus.UNAVAILABLE,
                notes="Extent validated against Sentinel-1 SAR Flood Reference. Depth remains unvalidated model estimate."
            )

        provenance = InundationProvenance(
            rainfall_run_id=rainfall_run_id,
            hydrology_run_id=hydrology_run_id,
            inundation_run_id=inundation_run_id,
            model_version=self.surrogate.model_version,
            model_status=self.surrogate.model_status,
            feature_version="v1.0.0",
            dem_version="FABDEM_v1.2",
            reference_version="Sentinel-1_GRD_IW_v2.0",
            forecast_valid_time=forecast_valid_time,
            dataset_state="REAL_HISTORICAL_HINDCAST",
            depth_status=DepthStatus.MODEL_ESTIMATE,
            depth_validation=DepthValidationStatus.UNAVAILABLE,
            sar_reference=sar_comparison
        )

        tile_summary.inundation_provenance = provenance
        tile_summary.sar_flood_reference = sar_comparison
        tile_summary.model_status = self.surrogate.model_status
        tile_summary.depth_status = DepthStatus.MODEL_ESTIMATE
        tile_summary.depth_validation = DepthValidationStatus.UNAVAILABLE

        return tile_summary
