"""
Automated Tests for Hydrology Forecasting Models (L0 to L4).
"""

from ml.streamflow.persistence import PersistenceStreamflowBaseline
from ml.streamflow.xgboost_forecast import XGBoostStreamflowNowcaster
from ml.streamflow.lstm_forecast import SequenceLSTMStreamflowModel
from ml.streamflow.tft_model import TemporalFusionTransformerStreamflow
from ml.streamflow.graph_model import RiverGraphStreamflowModel

def test_persistence_baseline_execution():
    model = PersistenceStreamflowBaseline()
    res = model.predict_multi_horizon(26.15, 0.08, 14200.0)
    assert res["model_id"] == "STREAMFLOW_L0_PERSISTENCE"
    assert len(res["stage_p50"]) == 7
    assert res["uncertainty_method"] == "RULE_BASED_UNCERTAINTY"

def test_xgboost_nowcaster_execution():
    model = XGBoostStreamflowNowcaster()
    features = [45.0, 140.0, 0.85, 26.15, 25.9, 0.08, 18500.0]
    res = model.predict_multi_horizon(features)
    assert res["model_id"] == "STREAMFLOW_L1_XGBOOST"
    assert len(res["stage_p50"]) == 7
    assert len(res["discharge_p50"]) == 7
    assert res["uncertainty_method"] == "QUANTILE_GRADIENT_BOOSTING"

def test_lstm_sequence_model_execution():
    model = SequenceLSTMStreamflowModel()
    seq = [{"rain_mm": 18.0, "stage_m": 26.15, "discharge_cumec": 14200.0}] * 24
    res = model.predict_sequence(seq, [30.0]*24)
    assert "STREAMFLOW_L2" in res["model_id"]
    assert len(res["stage_p50"]) == 7

def test_tft_model_execution():
    model = TemporalFusionTransformerStreamflow()
    res = model.predict({"catchment_area_km2": 132100.0}, [{"stage_m": 26.15}], [25.0]*24)
    assert res["model_id"] == "STREAMFLOW_L3_NWP_ANALYTICAL"
    assert len(res["stage_p50"]) == 7

def test_river_graph_model_execution():
    model = RiverGraphStreamflowModel()
    res = model.predict_node(
        "CWC_MUNDALI",
        {"current_stage_m": 26.15, "rain_24h_mm": 120.0},
        {"CWC_TIKERPARA": {"discharge_cumec": 18500.0}}
    )
    assert res["model_id"] == "STREAMFLOW_L4_RIVER_ROUTING_ANALYTICAL"
    assert len(res["stage_p50"]) == 7
