"""
End-to-End Causal Chain Integration Test for JALDRISHTI AI.
Validates the entire pipeline:
Simulate Storm -> Ingestion -> Quality Control -> Multi-Source Fusion ->
0-6h Nowcast -> 6-72h Hydrograph -> 2D Inundation -> Asset/Population Impact ->
Alert Decision Gating -> Frontend Provenance JSON.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from apps.api.main import app
from services.preprocessing.qc import QualityControlEngine
from services.fusion.precipitation import PrecipitationFusionEngine
from ml.rainfall.nowcast_models import RainfallNowcastSuite
from ml.streamflow.discharge_models import HydrologyForecastSuite
from ml.inundation.hydraulic_surrogate import HydraulicSurrogateModel
from services.impact.impact_engine import ImpactAssessmentEngine
from services.alerts.alert_engine import AlertEngine
from services.models import QualityFlag, ConfidenceLevel, AlertSeverity

client = TestClient(app)

def test_full_causal_pipeline_execution():
    base_time = datetime.now(timezone.utc)
    run_id = f"TEST-CAUSAL-{base_time.strftime('%Y%m%d%H%M')}"

    # 1. INGESTION & QUALITY CONTROL
    raw_obs = [
        {"source_id": "DOPPLER_RADAR_PARADIP", "rainfall_1h_mm": 38.5, "lat": 20.29, "lon": 86.60, "timestamp": base_time},
        {"source_id": "IMD_AWS_ARG_ODISHA", "rainfall_1h_mm": 32.0, "lat": 20.46, "lon": 85.88, "timestamp": base_time},
        {"source_id": "MOSDAC_INSAT_3DR_HEM", "rainfall_1h_mm": 28.0, "lat": 20.50, "lon": 86.00, "timestamp": base_time},
        {"source_id": "NASA_GPM_IMERG_EARLY", "rainfall_1h_mm": 25.5, "lat": 20.50, "lon": 86.00, "timestamp": base_time},
        {"source_id": "ECMWF_IFS_OPEN_DATA", "rainfall_1h_mm": 22.0, "lat": 20.50, "lon": 86.00, "timestamp": base_time}
    ]

    qc_obs = []
    for obs in raw_obs:
        q_flag, _ = QualityControlEngine.check_observation(obs)
        assert q_flag == QualityFlag.GOOD
        qc_obs.append({"source_id": obs["source_id"], "value": obs["rainfall_1h_mm"], "quality_flag": q_flag})

    # 2. MULTI-SOURCE PRECIPITATION FUSION
    fused_rate, unc_std, weights, data_conf = PrecipitationFusionEngine.fuse_precipitation(qc_obs, gauge_multiplier_bias=1.08)
    assert fused_rate >= 25.0
    assert data_conf == ConfidenceLevel.HIGH

    # 3. PRECIPITATION NOWCASTING (0-6h)
    nowcast_model = RainfallNowcastSuite()
    nowcast_frames = nowcast_model.predict(
        fused_grid_or_rate=fused_rate,
        features={"cape_jkg": 2200.0, "pwat_mm": 62.0},
        base_time=base_time,
        data_confidence=data_conf.value
    )
    assert len(nowcast_frames) >= 5
    assert nowcast_frames[0].mean_rainfall_mm_hr > 0
    assert nowcast_frames[0].heavy_rain_prob > 0.50

    # 4. HYDROLOGICAL STREAMFLOW ROUTING (6-72h)
    hydro_suite = HydrologyForecastSuite()
    hydro_forecast = hydro_suite.predict(
        station_id="STN-03",
        current_stage_m=24.80,
        warning_level_m=25.40,
        danger_level_m=26.30,
        features={
            "rain_6h": 55.0,
            "rain_24h": 165.0,
            "soil_saturation": 0.92,
            "rate_of_rise_m_hr": 0.32,
            "upstream_discharge": 26500.0
        },
        base_time=base_time,
        forecast_run_id=run_id
    )
    assert hydro_forecast.peak_predicted_level_m >= 26.30  # Exceeds danger level
    assert hydro_forecast.peak_exceeds_danger is True

    # 5. 2D HYDRAULIC INUNDATION SURROGATE
    inundation_model = HydraulicSurrogateModel()
    inundation_res = inundation_model.predict_inundation(
        peak_river_stage_m=hydro_forecast.peak_predicted_level_m,
        danger_level_m=26.30,
        rainfall_accumulation_24h_mm=165.0,
        forecast_run_id=run_id,
        valid_time=hydro_forecast.peak_predicted_time,
        lead_time_hours=14.0
    )
    assert inundation_res.inundated_area_sqkm > 100.0
    assert inundation_res.depth_class_gt_2m_sqkm > 0.0

    # 6. SPATIAL ASSET & POPULATION IMPACT
    impact_engine = ImpactAssessmentEngine()
    impact_res = impact_engine.evaluate_impact(
        inundated_area_sqkm=inundation_res.inundated_area_sqkm,
        depth_gt_1m_sqkm=inundation_res.depth_class_1_2m_sqkm + inundation_res.depth_class_gt_2m_sqkm,
        flood_prob_mean=inundation_res.flood_prob_mean,
        forecast_run_id=run_id,
        valid_time=hydro_forecast.peak_predicted_time
    )
    assert impact_res.population_exposed > 10000
    assert len(impact_res.affected_assets) > 0

    # 7. ALERT DECISION SUPPORT & HUMAN GATING
    alert_engine = AlertEngine()
    alert = alert_engine.evaluate_alert(
        fused_rain_mm_hr=fused_rate,
        rain_24h_mm=165.0,
        river_stage_m=hydro_forecast.peak_predicted_level_m,
        warning_stage_m=25.40,
        danger_stage_m=26.30,
        flood_prob=0.92,
        inundated_area_sqkm=inundation_res.inundated_area_sqkm,
        data_confidence=data_conf,
        model_confidence=ConfidenceLevel.HIGH,
        lead_time_hours=14.0,
        forecast_run_id=run_id,
        base_time=base_time
    )
    assert alert.severity == AlertSeverity.RED
    assert alert.requires_human_review is True
    assert alert.is_acknowledged is False

    # Human Officer Acknowledges Alert
    alert_engine.acknowledge_alert(alert.alert_id, operator_id="State Emergency Officer - Odisha SDMA")
    assert alert_engine.acknowledged_alerts[alert.alert_id]["by"] == "State Emergency Officer - Odisha SDMA"
