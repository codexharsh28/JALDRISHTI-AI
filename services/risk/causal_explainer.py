"""
Causal Explainability & "Why Did Risk Change?" Decomposition Engine for JALDRISHTI AI.
Decomposes material risk score shifts into exact additive subcomponent contributions.
"""

from typing import Dict, Any, List, Optional
from services.risk.risk_types import RiskContributor

class CausalRiskExplainer:
    """
    Decomposes risk deltas into causal factors based on actual model input changes.
    """

    @staticmethod
    def explain_risk_change(
        prev_inputs: Dict[str, Any],
        new_inputs: Dict[str, Any],
        prev_subscores: Dict[str, float],
        new_subscores: Dict[str, float],
        total_delta: float
    ) -> List[RiskContributor]:
        """
        Decomposes total risk delta into additive causal contributors:
        Delta Risk = Sum(Delta_i)
        """
        contributors: List[RiskContributor] = []

        # 1. Rainfall Accumulation & Intensity Contribution
        prev_rain = prev_inputs.get("rain_24h_mm", 0.0)
        new_rain = new_inputs.get("rain_24h_mm", 0.0)
        met_delta = round(new_subscores.get("meteorological", 0.0) - prev_subscores.get("meteorological", 0.0), 1)
        if abs(met_delta) >= 0.5 or abs(new_rain - prev_rain) >= 5.0:
            dir_str = "INCREASING_RISK" if met_delta > 0 else "DECREASING_RISK"
            contributors.append(RiskContributor(
                factor_name="Rainfall Accumulation & Intensity",
                delta_score=met_delta,
                direction=dir_str,
                category="PRECIPITATION",
                evidence_value=f"{new_rain:.1f} mm/24h (Intensity: {new_inputs.get('fused_rain_mm_hr', 0):.1f} mm/hr)",
                baseline_value=f"{prev_rain:.1f} mm/24h",
                explanation=f"{'+' if met_delta > 0 else ''}{met_delta:.1f} pts due to 24h rainfall change ({prev_rain:.1f} -> {new_rain:.1f} mm)"
            ))

        # 2. Hydrology & River Stage Rise Contribution
        prev_stage = prev_inputs.get("river_stage_m", 0.0)
        new_stage = new_inputs.get("river_stage_m", 0.0)
        hydro_delta = round(new_subscores.get("hydrological", 0.0) - prev_subscores.get("hydrological", 0.0), 1)
        if abs(hydro_delta) >= 0.5 or abs(new_stage - prev_stage) >= 0.1:
            dir_str = "INCREASING_RISK" if hydro_delta > 0 else "DECREASING_RISK"
            contributors.append(RiskContributor(
                factor_name="River Stage & Discharge Surge",
                delta_score=hydro_delta,
                direction=dir_str,
                category="HYDROLOGY",
                evidence_value=f"{new_stage:.2f} m ({new_inputs.get('discharge_cumec', 0):.0f} m³/s)",
                baseline_value=f"{prev_stage:.2f} m",
                explanation=f"{'+' if hydro_delta > 0 else ''}{hydro_delta:.1f} pts from hydraulic surge ({prev_stage:.2f}m -> {new_stage:.2f}m)"
            ))

        # 3. Inundation Extent & Probability Expansion Contribution
        prev_prob = prev_inputs.get("flood_prob", 0.0)
        new_prob = new_inputs.get("flood_prob", 0.0)
        prev_area = prev_inputs.get("inundated_area_sqkm", 0.0)
        new_area = new_inputs.get("inundated_area_sqkm", 0.0)
        inun_delta = round(new_subscores.get("inundation", 0.0) - prev_subscores.get("inundation", 0.0), 1)
        if abs(inun_delta) >= 0.5 or abs(new_area - prev_area) >= 2.0:
            dir_str = "INCREASING_RISK" if inun_delta > 0 else "DECREASING_RISK"
            contributors.append(RiskContributor(
                factor_name="Inundation Extent & Floodplain Surcharge",
                delta_score=inun_delta,
                direction=dir_str,
                category="INUNDATION",
                evidence_value=f"{new_area:.1f} km² ({new_prob*100:.0f}% mean probability)",
                baseline_value=f"{prev_area:.1f} km²",
                explanation=f"{'+' if inun_delta > 0 else ''}{inun_delta:.1f} pts due to floodplain surcharge expansion ({prev_area:.1f} -> {new_area:.1f} km²)"
            ))

        # 4. Critical Asset & Population Exposure Contribution
        prev_assets = prev_inputs.get("critical_assets_exposed", 0)
        new_assets = new_inputs.get("critical_assets_exposed", 0)
        exp_delta = round(new_subscores.get("exposure", 0.0) - prev_subscores.get("exposure", 0.0), 1)
        if abs(exp_delta) >= 0.5 or prev_assets != new_assets:
            dir_str = "INCREASING_RISK" if exp_delta > 0 else "DECREASING_RISK"
            contributors.append(RiskContributor(
                factor_name="Critical Infrastructure & Population Vulnerability",
                delta_score=exp_delta,
                direction=dir_str,
                category="IMPACT",
                evidence_value=f"{new_assets} assets ({new_inputs.get('population_exposed', 0):,} exposed)",
                baseline_value=f"{prev_assets} assets",
                explanation=f"{'+' if exp_delta > 0 else ''}{exp_delta:.1f} pts from infrastructure footprint change ({prev_assets} -> {new_assets} facilities)"
            ))

        # 5. Data Quality & Telemetry Confidence Adjustment
        prev_conf = prev_inputs.get("data_confidence", "HIGH")
        new_conf = new_inputs.get("data_confidence", "HIGH")
        conf_delta = round(new_subscores.get("confidence_adjustment", 0.0) - prev_subscores.get("confidence_adjustment", 0.0), 1)
        if abs(conf_delta) >= 0.5 or prev_conf != new_conf:
            dir_str = "INCREASING_RISK" if conf_delta > 0 else "DECREASING_RISK"
            contributors.append(RiskContributor(
                factor_name="Data Confidence & Telemetry Degradation",
                delta_score=conf_delta,
                direction=dir_str,
                category="CONFIDENCE",
                evidence_value=new_conf,
                baseline_value=prev_conf,
                explanation=f"{'+' if conf_delta > 0 else ''}{conf_delta:.1f} pts uncertainty buffer adjustment (Telemetry status: {prev_conf} -> {new_conf})"
            ))

        # Sort contributors by absolute contribution magnitude
        contributors.sort(key=lambda c: abs(c.delta_score), reverse=True)
        return contributors
