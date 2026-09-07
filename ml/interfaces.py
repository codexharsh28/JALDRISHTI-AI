"""
Abstract Replaceable Model Interfaces for JALDRISHTI AI.
Defines strict contracts for Rainfall Nowcasting, Streamflow Forecasting,
Hydrodynamic Inundation Surrogates, Uncertainty Quantification, and Impact Analytics.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class RainfallNowcastModel(ABC):
    @abstractmethod
    def predict(
        self,
        fused_grid_or_rate: Any,
        features: Dict[str, float],
        base_time: datetime,
        horizons_minutes: List[int],
        data_confidence: str
    ) -> List[Any]:
        """Generate multi-horizon rainfall nowcast predictions."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return model metadata, training dataset, and holdout evaluation metrics."""
        pass

    @abstractmethod
    def version(self) -> str:
        """Return semantic model version ID."""
        pass

    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Return schema requirements for input features and grids."""
        pass

    @abstractmethod
    def output_schema(self) -> Dict[str, Any]:
        """Return schema of predicted frames, uncertainty, and probability."""
        pass


class HydrologyForecastModel(ABC):
    @abstractmethod
    def predict(
        self,
        station_id: str,
        current_stage_m: float,
        warning_level_m: float,
        danger_level_m: float,
        features: Dict[str, float],
        base_time: datetime,
        horizons_hours: List[int],
        forecast_run_id: str
    ) -> Any:
        """Generate multi-lead hydrograph forecasts with p10, p50, p90 envelopes."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def version(self) -> str:
        pass


class InundationModel(ABC):
    @abstractmethod
    def predict(
        self,
        peak_river_stage_m: float,
        danger_level_m: float,
        rainfall_accumulation_24h_mm: float,
        forecast_run_id: str,
        valid_time: datetime,
        lead_time_hours: float
    ) -> Any:
        """Generate 2D inundation depth grid and polygon classifications."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def version(self) -> str:
        pass


class UncertaintyModel(ABC):
    @abstractmethod
    def evaluate(
        self,
        source_health_list: List[Dict[str, Any]],
        model_quantile_spread_m: float,
        lead_time_hours: float
    ) -> tuple[str, str, str]:
        """Evaluate (data_confidence, model_confidence, overall_confidence)."""
        pass


class ImpactModel(ABC):
    @abstractmethod
    def evaluate(
        self,
        inundated_area_sqkm: float,
        depth_gt_1m_sqkm: float,
        flood_prob_mean: float,
        forecast_run_id: str,
        valid_time: datetime
    ) -> Any:
        """Evaluate infrastructure exposure, population vulnerability, and composite impact index."""
        pass
