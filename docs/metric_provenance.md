# Metric Provenance & Resolution Harmonization Register
## JALDRISHTI AI (SIH26071)

This register provides complete end-to-end traceability for every primary metric presented across the frontend operations center.

---

## 1. End-to-End Metric Provenance Matrix

| Metric Name | Frontend View | API Endpoint | Backend Service | Engine / Model Layer | Data Storage / Origin | Source Provenance & Classification |
|---|---|---|---|---|---|---|
| **Current Fused Rainfall** (mm/h) | Overview, Rainfall Nowcast | `GET /api/v1/rainfall/nowcast` | `PrecipitationFusionEngine` | Quality-Weighted Multi-Source Fusion with G/R Bias Correction | `services/fusion/precipitation.py` | `DOPPLER_RADAR_PARADIP` (1km) + `IMD_AWS` (point) + `INSAT_3DR` (4km) + `IMERG` (10km) + `NWP` (28km). **[SIMULATED DATASET]** |
| **6h Rainfall Accumulation** (mm) | Overview, Rainfall Nowcast | `GET /api/v1/rainfall/nowcast` | `FeatureStore` | Sum of hourly fused rainfall vector ($T_{-6\text{h}} \dots T_0$) | `services/preprocessing/features.py` | Computed accumulation over 2.5km computational model grid. **[SIMULATED DATASET]** |
| **Current River Stage** (m) | Overview, River Forecast, Stations | `GET /api/v1/hydrology/forecast?station_id=STN-03` | `CWCHydrologyAdapter` | Quality-Controlled Gauge Telemetry | `basin_config.yaml` / CWC sensor feed | `CWC_TELEMETRY_MAHANADI` point gauge (Naraj/Cuttack). **[SIMULATED TELEMETRY]** |
| **Predicted 24h Peak Stage** (m) | Overview, River Forecast | `GET /api/v1/hydrology/forecast?station_id=STN-03` | `HydrologyForecastSuite` | Sequence LSTM with River Network Graph routing ($p10, p50, p90$) | `ml/streamflow/discharge_models.py` | Physics-informed Gamma hydrograph convolution + upstream catchment lag. **[SIMULATED METRIC]** |
| **Flood Probability** (%) | Overview, River Forecast, Alerts | `GET /api/v1/alerts`, `GET /api/v1/hydrology/forecast` | `AlertEngine`, `HydrologyForecastSuite` | Probabilistic Quantile Surcharge & Platt Sigmoid Calibration | `ml/uncertainty/engine.py` | Calculated from stage exceeding bankfull/danger marks. **[SIMULATED METRIC]** |
| **Inundated Area** ($\text{km}^2$) | Overview, Inundation, Replay | `GET /api/v1/inundation/forecast?lead_time_hours=12` | `HydraulicSurrogateModel` | 2D Hydrodynamic Surrogate (UNet / Random Forest) | `ml/inundation/hydraulic_surrogate.py` | Surcharge over Copernicus GLO-30 DEM slope & HAND depression grid. **[SIMULATED SURROGATE]** |
| **Depth Classes** (0–0.3m, 0.3–1m, 1–2m, >2m) | Inundation | `GET /api/v1/inundation/forecast` | `HydraulicSurrogateModel` | 4-tier depth threshold summation ($6.25\text{ km}^2/\text{cell}$) | `ml/inundation/hydraulic_surrogate.py` | Hydrodynamic water surface elevation minus topographic elevation. **[SIMULATED SURROGATE]** |
| **Population Exposure** (count) | Overview, Impact | `GET /api/v1/impacts` | `ImpactAssessmentEngine` | Spatial intersection with 100m WorldPop demographic grid | `services/impact/impact_engine.py` | Zonal demographic sum within inundation boundary. **[SYNTHETIC POPULATION]** |
| **Critical Assets at Risk** | Overview, Impact | `GET /api/v1/impacts` | `ImpactAssessmentEngine` | Geospatial point-in-polygon & elevation vulnerability filter | `geospatial/assets/critical_infrastructure.geojson` | OpenStreetMap + OSDMA infrastructure registry. **[SYNTHETIC ASSETS]** |
| **Why Did Risk Change?** (%) | Overview, Alerts | `GET /api/v1/alerts` | `UncertaintyAndExplainabilityEngine` | SHAP-style normalized feature sensitivity attribution | `ml/uncertainty/engine.py` | Relative weighting of 24h rain, upstream discharge, rate of rise, and soil saturation. **[SIMULATED EXPLANATION]** |
| **Data Confidence** (HIGH/MED/DEGRADED) | Header, Data Health, Alerts | `GET /api/v1/data-health` | `AdapterRegistry`, `UncertaintyAndExplainabilityEngine` | Sensor latency, missingness, and staleness auditor | `services/models.py` | Evaluated across all 9 data providers. **[SYSTEM METRIC]** |
| **Model Benchmark Metrics** (NSE, KGE, CSI, IoU) | Models, Rainfall Nowcast, River | `GET /api/v1/models` | `RainfallNowcastSuite`, `HydrologyForecastSuite`, `HydraulicSurrogateModel` | Standalone Python holdout evaluation runner | `ml/evaluation/run.py` | Event-holdout benchmark evaluation on synthetic dataset. **[BENCHMARK EVALUATION]** |

---

## 2. Spatial Resolution & Grid Harmonization Rules

> **IMPORTANT PRINCIPLE:**  
> **Native data sources vary in spatial resolution from point observations to 28 km NWP fields.**  
> Coarse satellite (INSAT 4km, IMERG 10km) and numerical weather prediction (ECMWF 28km) datasets do **not** intrinsically provide 30-meter rainfall data.

- **Model Grid:** The 2.5 km computational grid ($50 \times 86$ cells) over the Mahanadi Delta ($14,250\text{ km}^2$) serves as the spatial harmonization plane for multi-source precipitation fusion.
- **Topographic Surrogate Grid:** Hydraulic surrogates utilize 30m DEM elevation and HAND terrain indices to map river overflow surcharges into localized depth classifications without making false claims about the native resolution of satellite precipitation estimates.
