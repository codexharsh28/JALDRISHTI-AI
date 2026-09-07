"""
5-Layer Hydrometeorological Anomaly Detector for JALDRISHTI AI.
Executes physical limits, temporal continuity jumps, robust Z-score (MAD), EWMA dynamic volatility,
and spatial cross-corroboration to reliably distinguish valid extreme weather from sensor failures.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import math
import logging

from services.anomaly.anomaly_types import AnomalyState, AnomalyClassification, AnomalyRecord
from services.anomaly.baselines import (
    PHYSICAL_BOUNDS,
    MAX_JUMP_RATES_1H,
    baseline_tracker
)
from services.anomaly.spatial_consistency import spatial_consistency_engine

logger = logging.getLogger(__name__)

class HydrometAnomalyDetector:
    """
    Multi-level real-time anomaly detection pipeline.
    """

    def evaluate_observation(
        self,
        station_id: str,
        variable: str,
        value: Optional[float],
        previous_value: Optional[float] = None,
        all_recent_observations: Optional[Dict[str, Dict[str, Any]]] = None,
        satellite_qpe: Optional[float] = None,
        nwp_forecast: Optional[float] = None,
        obs_time: Optional[datetime] = None,
        data_state: str = "LIVE",
        provider: str = "UNKNOWN"
    ) -> AnomalyRecord:
        """
        Evaluates an individual hydrometeorological observation across all 5 detection levels.
        """
        all_recent = all_recent_observations or {}
        layers_triggered: List[str] = []
        scores: List[float] = []
        reasons: List[str] = []

        # =========================================================================
        # 0. Missingness Check
        # =========================================================================
        if value is None or math.isnan(value):
            return AnomalyRecord(
                station_id=station_id,
                variable=variable,
                observed_value=None,
                expected_range=[0.0, 100.0],
                baseline_value=None,
                anomaly_score=0.85,
                anomaly_state=AnomalyState.ANOMALOUS,
                classification=AnomalyClassification.LIKELY_SENSOR_ERROR,
                reason=f"Missing observation value (telemetry dropout) for variable '{variable}'",
                layers_triggered=["LEVEL_0_MISSING"],
                data_state=data_state,
                provider=provider
            )

        # Retrieve robust baseline statistics for this specific station & variable
        stats = baseline_tracker.get_baseline_stats(station_id, variable, obs_time)
        med = stats["median"]
        mad = stats["mad"]
        ewma_m = stats["ewma_mean"]
        ewma_s = stats["ewma_std"]
        p10 = stats["p10"]
        p90 = stats["p90"]

        # =========================================================================
        # LEVEL 0: Physical Limits & Plausibility Bounds
        # =========================================================================
        bounds = PHYSICAL_BOUNDS.get(variable)
        if bounds:
            min_bound, max_bound = bounds
            if value < min_bound or value > max_bound:
                layers_triggered.append("LEVEL_0_PHYSICAL_BOUNDS")
                scores.append(1.0)
                reasons.append(f"Value {value:.2f} violates physical bounds [{min_bound}, {max_bound}]")
            expected_range = [min_bound, max_bound]
        else:
            expected_range = [max(0.0, med - 3.5 * mad), med + 3.5 * mad]

        # =========================================================================
        # LEVEL 1: Temporal Continuity, Jump Rates & Flatline / Freeze
        # =========================================================================
        max_jump = MAX_JUMP_RATES_1H.get(variable)
        if previous_value is not None and max_jump is not None and not math.isnan(previous_value):
            jump = abs(value - previous_value)
            if jump > max_jump:
                layers_triggered.append("LEVEL_1_TEMPORAL_JUMP")
                score_jump = min(1.0, 0.6 + 0.4 * (jump / (2.0 * max_jump)))
                scores.append(score_jump)
                reasons.append(f"Temporal jump {jump:.2f} exceeds 1h maximum plausible rate ({max_jump:.2f})")

        # Flatline / Frozen sensor detection (identical reading for >= 5 consecutive timesteps)
        repeat_count = baseline_tracker.get_flatline_count(station_id, variable)
        if repeat_count >= 5 and variable in ["river_stage", "river_stage_m", "water_level", "discharge", "temperature", "temperature_c"]:
            layers_triggered.append("LEVEL_1_FROZEN_SENSOR")
            scores.append(0.85)
            reasons.append(f"Sensor flatline/freeze detected: identical reading ({value:.2f}) for {repeat_count + 1} consecutive timesteps")

        # =========================================================================
        # LEVEL 2: Robust Z-Score (Median Absolute Deviation with 0.6745 normalizer)
        # =========================================================================
        if mad > 0:
            z_robust = 0.6745 * (abs(value - med) / mad)
            if z_robust > 4.5:
                layers_triggered.append("LEVEL_2_ROBUST_ZSCORE")
                score_z = min(1.0, 0.5 + 0.08 * (z_robust - 4.5))
                scores.append(score_z)
                reasons.append(f"Robust Z-score ({z_robust:.2f}) exceeds 4.5 threshold (Med: {med:.2f}, MAD: {mad:.2f})")
            elif z_robust > 3.0:
                scores.append(0.35)

        # =========================================================================
        # LEVEL 3: EWMA Dynamic Volatility Band
        # =========================================================================
        ewma_upper = max(ewma_m + 3.5 * ewma_s, p90)
        ewma_lower = max(0.0, ewma_m - 3.5 * ewma_s)
        if value > ewma_upper or (value < ewma_lower and ewma_lower > 0):
            layers_triggered.append("LEVEL_3_EWMA_DEVIATION")
            scores.append(0.65)
            reasons.append(f"Value deviates from EWMA dynamic volatility band [{ewma_lower:.2f}, {ewma_upper:.2f}]")

        # =========================================================================
        # LEVEL 4: Rolling Statistical Baseline (P10 - P90)
        # =========================================================================
        if value > p90 * 2.5 and value > 25.0:
            layers_triggered.append("LEVEL_4_ROLLING_BASELINE")
            scores.append(0.50)
            reasons.append(f"Value {value:.2f} exceeds 2.5x 90th percentile baseline ({p90:.2f})")

        # =========================================================================
        # SPATIAL CROSS-CORROBORATION (Valid Extremes vs Sensor Failure)
        # =========================================================================
        spatial_disagreement, spatial_classification, spatial_evidence = spatial_consistency_engine.evaluate_spatial_consistency(
            station_id=station_id,
            variable=variable,
            observed_value=value,
            all_recent_observations=all_recent,
            satellite_qpe=satellite_qpe,
            nwp_forecast=nwp_forecast
        )

        raw_score = max(scores) if scores else 0.0

        # Synthesis & Safety Classification
        if "LEVEL_0_PHYSICAL_BOUNDS" in layers_triggered:
            final_score = 1.0
            anomaly_state = AnomalyState.LIKELY_SENSOR_ERROR
            classification = AnomalyClassification.OUT_OF_BOUNDS
            primary_reason = "; ".join(reasons)
        elif spatial_classification == AnomalyClassification.VALID_EXTREME:
            # Corroborated meteorological extreme event: discount anomaly score to WATCH/NORMAL
            final_score = min(raw_score * 0.40, 0.40)
            anomaly_state = AnomalyState.WATCH if final_score > 0.20 else AnomalyState.NORMAL
            classification = AnomalyClassification.VALID_EXTREME
            agr_pct = int(spatial_evidence.get("agreement_ratio", 1.0) * 100)
            primary_reason = f"VALID EXTREME METEOROLOGICAL EVENT: High intensity confirmed by surrounding stations/satellite ({agr_pct}% agreement)."
        elif "LEVEL_1_FROZEN_SENSOR" in layers_triggered:
            final_score = max(raw_score, 0.85)
            anomaly_state = AnomalyState.LIKELY_SENSOR_ERROR
            classification = AnomalyClassification.LIKELY_SENSOR_ERROR
            primary_reason = "; ".join(reasons)
        elif "LEVEL_1_TEMPORAL_JUMP" in layers_triggered and spatial_classification == AnomalyClassification.LIKELY_SENSOR_ERROR:
            final_score = max(raw_score, 0.90)
            anomaly_state = AnomalyState.LIKELY_SENSOR_ERROR
            classification = AnomalyClassification.LIKELY_SENSOR_ERROR
            primary_reason = f"Isolated uncorroborated temporal jump spike: {'; '.join(reasons)}"
        elif "LEVEL_1_TEMPORAL_JUMP" in layers_triggered:
            final_score = max(raw_score, 0.75)
            anomaly_state = AnomalyState.ANOMALOUS
            classification = AnomalyClassification.TEMPORAL_JUMP
            primary_reason = "; ".join(reasons)
        elif spatial_classification == AnomalyClassification.LIKELY_SENSOR_ERROR and raw_score >= 0.5:
            final_score = max(raw_score, 0.85)
            anomaly_state = AnomalyState.LIKELY_SENSOR_ERROR
            classification = AnomalyClassification.LIKELY_SENSOR_ERROR
            primary_reason = f"Uncorroborated sensor surge: {'; '.join(reasons) if reasons else 'No spatial neighbor or satellite consensus'}"
        elif raw_score >= 0.6:
            final_score = raw_score
            anomaly_state = AnomalyState.ANOMALOUS
            classification = AnomalyClassification.POSSIBLE_ANOMALY
            primary_reason = "; ".join(reasons)
        elif raw_score >= 0.3:
            final_score = raw_score
            anomaly_state = AnomalyState.WATCH
            classification = AnomalyClassification.POSSIBLE_ANOMALY
            primary_reason = "; ".join(reasons)
        else:
            final_score = max(raw_score, 0.05)
            anomaly_state = AnomalyState.NORMAL
            classification = AnomalyClassification.VALID_EXTREME if value > 0 else AnomalyClassification.INSUFFICIENT_CONTEXT
            primary_reason = "Observation within normal statistical limits"

        # Record accepted observations to dynamic baseline tracker (excluding unphysical errors)
        if "LEVEL_0_PHYSICAL_BOUNDS" not in layers_triggered and not math.isnan(value):
            baseline_tracker.record_observation(station_id, variable, value, obs_time)

        return AnomalyRecord(
            station_id=station_id,
            variable=variable,
            observed_value=value,
            expected_range=expected_range,
            baseline_value=round(med, 2),
            anomaly_score=round(final_score, 3),
            anomaly_state=anomaly_state,
            classification=classification,
            reason=primary_reason,
            layers_triggered=layers_triggered,
            neighbor_comparison=spatial_evidence,
            source_agreement={
                "spatial_disagreement": round(spatial_disagreement, 2),
                "agreement_ratio": spatial_evidence.get("agreement_ratio")
            },
            data_state=data_state,
            provider=provider
        )

# Global anomaly detector singleton
hydromet_anomaly_detector = HydrometAnomalyDetector()
