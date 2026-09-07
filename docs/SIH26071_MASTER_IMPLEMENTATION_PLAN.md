# JALDRISHTI AI — SIH26071 Master Implementation Plan

> **Document Classification:** INTERNAL — ENGINEERING ROADMAP  
> **Version:** 1.0.0  
> **Generated:** 2026-09-01  
> **Authority:** Principal Architect Forensic Audit Reconciliation  
> **Status:** AWAITING APPROVAL — NO IMPLEMENTATION UNTIL APPROVED

---

## 1. Executive Summary

JALDRISHTI AI (SIH26071) is an AI/ML-based Integrated Heavy Rainfall Early Warning and Inundation Prediction System piloted for the Mahanadi Delta, Odisha. A forensic audit identified 25 major findings spanning security, ML production path integrity, scientific claim consistency, data access, and operational readiness.

This document reconciles every forensic finding against the current repository state, establishes verification status, and produces a dependency-aware, risk-prioritized implementation roadmap across 10 phases.

**Critical headline findings confirmed through repository verification:**

| Category | Severity | Summary |
|---|---|---|
| **Security** | P0 | Hardcoded credentials (`admin123`, `operator123`), unsafe auth fallback, hardcoded HMAC secret, unsafe `torch.load()` |
| **ML Integrity** | P0 | Default rainfall production path now routes to genuine ConvLSTM (model param default=`convlstm`), but analytical surrogate remains the "else" branch. Hydrology production path is purely analytical. |
| **Scientific Claims** | P1 | README claims "Deep ConvLSTM", "LSTM River Graph", "UNet Inundation" — production models are analytical surrogates with honest internal labels but external-facing text inconsistency |
| **Data** | P1 | Training datasets are synthetic. GIS assets (DEM=summary only, landcover=empty, population=empty). Real provider access depends on external authorization. |
| **Infrastructure** | P2 | SQLite WAL in production, no requirements.txt/pyproject.toml, no CI/CD, no monitoring, Docker compose lacks PostgreSQL/Redis |

**Roadmap scope:** 10 phases, security-first, preserving demo stability throughout.

---

## 2. Forensic Finding Reconciliation

### Finding F01 — Rainfall Production Path Uses Analytical Surrogate

| Field | Detail |
|---|---|
| **FINDING ID** | F01 |
| **AUDIT CLAIM** | Production rainfall path uses an analytical surrogate instead of genuine ConvLSTM despite ConvLSTM code/checkpoint existing |
| **CURRENT REPOSITORY EVIDENCE** | `main.py:356`: `model: str = Query("convlstm", ...)`. When `model.lower() in ["convlstm", "pytorch", "deep"]` (L408), it imports `ConvLSTMInferenceEngine` and runs genuine PyTorch inference. The `else` branch (L418-427) runs `RainfallNowcastSuite` (analytical surrogate). Default query parameter is `"convlstm"`, meaning the **default API call now routes to genuine ConvLSTM**. However, `nowcast_models.py` L7 labels Level 3 as "Analytical Storm Decay Precipitation Surrogate". The `FORECAST_RUNS` at L108 still lists `"L3_ANALYTICAL_SURROGATE"` as executed model. |
| **STATUS** | **PARTIALLY CONFIRMED** — Default path now routes to ConvLSTM, but startup metadata, `FORECAST_RUNS`, and `source_id_str="PRECIP_FUSION_CONVLSTM"` (L427) in the analytical branch misleadingly suggest ConvLSTM when it is not. |
| **ROOT CAUSE** | The default was changed to `"convlstm"` but residual references to the analytical model remain in startup metadata and error paths. |
| **IMPACT** | **HIGH** — Ambiguity about which model actually produces forecasts undermines scientific reproducibility |
| **RECOMMENDED ACTION** | Clean up `FORECAST_RUNS` metadata to reflect actual model used per request. Ensure `source_id_str` in the analytical branch does NOT say "CONVLSTM". Run shadow comparison before fully committing to ConvLSTM as sole production model. |

---

### Finding F02 — Hydrology Production Path Uses Analytical Behavior

| Field | Detail |
|---|---|
| **FINDING ID** | F02 |
| **AUDIT CLAIM** | Hydrology production path uses analytical behavior instead of deep-learning models |
| **CURRENT REPOSITORY EVIDENCE** | `discharge_models.py`: `HydrologyForecastSuite` version is `"Analytical-Routing-v2.4"`, architecture is "Analytical Hydrograph Extrapolation with Directed River Graph Routing" (L29). L111 provenance `product_name` says "LSTM Probabilistic Hydrograph Forecast" — this is **misleading**. `lstm_forecast.py` is actually `AnalyticalHydrographSurrogate` with alias `SequenceLSTMStreamflowModel = AnalyticalHydrographSurrogate` (L83). LSTM/TFT/Graph models exist as code (`tft_model.py`, `graph_model.py`) but are not in the production path. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Architecture code exists but no trained checkpoints or inference integration for LSTM/TFT/Graph hydrology models. The analytical surrogate was wired as the production model. |
| **IMPACT** | **HIGH** — README claims "LSTM with River Network Graph" with NSE=0.89. Production model is analytical, and the metrics may not apply to it in the same way they would to a trained neural model. |
| **RECOMMENDED ACTION** | Fix provenance label at L111 to NOT say "LSTM". Determine whether trained hydrology checkpoints exist or need to be created. Shadow-test any ML model before promotion. |

---

### Finding F03 — Inundation Implementation Simpler Than Claims

| Field | Detail |
|---|---|
| **FINDING ID** | F03 |
| **AUDIT CLAIM** | Inundation production implementation is simpler than UI/documentation claims |
| **CURRENT REPOSITORY EVIDENCE** | `hydraulic_surrogate.py`: Production model uses grid-based analytical proxy (stage surcharge + elevation proxy + Gaussian dispersion). Named `"UNet-Surrogate-v3.1"` but contains NO neural network — purely NumPy calculations. README L50 claims "Physics-guided UNet / Random Forest surrogate." An RF model exists at `model_registry/inundation_rf_model.joblib` (724KB, verified loadable per `model_checkpoint_audit.json`) but is NOT used in the production `HydraulicSurrogateModel.predict_inundation()`. Internal doc labels `model_status = CANDIDATE` and `depth_validation = UNAVAILABLE`. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Naming convention inherited from aspirational architecture. RF model trained but not integrated into the production inference path. |
| **IMPACT** | **HIGH** — Metric claims (IoU=0.84, F1=0.88) are hardcoded in the response (L121-122) rather than computed from actual inference validation. |
| **RECOMMENDED ACTION** | Rename production model version from "UNet-Surrogate-v3.1" to "AnalyticalSurrogate-v3.1". Remove hardcoded validation metrics from response. Integrate RF model with shadow comparison. |

---

### Finding F04 — Training Datasets Largely Synthetic

| Field | Detail |
|---|---|
| **FINDING ID** | F04 |
| **AUDIT CLAIM** | Training datasets are largely synthetic |
| **CURRENT REPOSITORY EVIDENCE** | `data/simulation/` contains 6 CSV files: `rainfall_events_train.csv` (93KB), `hydrograph_events_train.csv` (101KB), `inundation_samples_train.csv` (75KB) and their validation splits. Model catalog entries show `dataset_state: "SYNTHETIC_HOLDOUT"` for all rainfall models and `"REAL_HISTORICAL_HINDCAST"` for hydrology baselines. `hydrology_datasets.yaml` references CWC real historical data (2018-2024) with checksums, but `state: REAL_HISTORICAL_ANALYSIS` — used for evaluation, not training of the production analytical model. |
| **STATUS** | **CONFIRMED** — Training data is synthetic. Real CWC data used for hindcast evaluation only. |
| **ROOT CAUSE** | System was built with synthetic data for development velocity. Real data access requires CWC/IMD authorization. |
| **IMPACT** | **MEDIUM** — Acceptable for prototype if clearly labeled. Problematic if metrics are presented as real-data performance. |
| **RECOMMENDED ACTION** | Maintain clear `SYNTHETIC` vs `REAL` labels in all model metadata. Plan phased transition to real-data training as access is obtained. |

---

### Finding F05 — README Metric/Architecture Inconsistencies

| Field | Detail |
|---|---|
| **FINDING ID** | F05 |
| **AUDIT CLAIM** | README/model metadata contains metric and architecture inconsistencies |
| **CURRENT REPOSITORY EVIDENCE** | README L121 claims ConvLSTM CSI=0.76, but `model_catalog.json` L80-84 shows ConvLSTM `overall_rmse_mm: 11.25, csi_35mm: 0.712` — different from the `0.76` claimed. The `0.76` belongs to the **analytical surrogate** (model_catalog L58-63), NOT the ConvLSTM. README L33 says "Deep ConvLSTM Nowcast" but production analytical model is not a ConvLSTM. README L128 claims "LSTM with River Network Graph NSE=0.89" but production is analytical. Inundation IoU=0.84 in README but `inundation_checkpoint_meta.json` shows actual IoU=0.5536. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | README metrics were written to match aspirational targets. They were not updated when actual model evaluations produced different numbers. |
| **IMPACT** | **CRITICAL** — A SIH reviewer comparing README claims against actual model artifacts would find irreconcilable discrepancies. |
| **RECOMMENDED ACTION** | Create authoritative metric contract. README must reference only verified, reproducible metrics with dataset provenance. |

---

### Finding F06 — Hardcoded Admin Passwords

| Field | Detail |
|---|---|
| **FINDING ID** | F06 |
| **AUDIT CLAIM** | Hardcoded admin passwords |
| **CURRENT REPOSITORY EVIDENCE** | `main.py:2103-2106`: `valid_admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")`, `valid_op_pass = os.getenv("OPERATOR_PASSWORD", "operator123")`. The fallback values `"admin123"` and `"operator123"` are active when env vars are not set. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Development convenience. No `.env` file is committed; only `.env.example` exists and does NOT contain ADMIN_PASSWORD. |
| **IMPACT** | **CRITICAL (P0)** — Anyone can authenticate as ADMIN with `admin123`. |
| **RECOMMENDED ACTION** | Remove default credentials. Require environment variable. Fail closed if not set. |

---

### Finding F07 — Authentication Fallback Accepting Default Credentials

| Field | Detail |
|---|---|
| **FINDING ID** | F07 |
| **AUDIT CLAIM** | Authentication fallback accepting unsafe default credentials |
| **CURRENT REPOSITORY EVIDENCE** | `main.py:2117-2120`: `elif (password == "admin123" or password == "operator123") and len(username) >= 3: is_valid = True`. This means ANY username >= 3 chars with password `admin123` gets authenticated. Comment says "Development/Demo fallback authorization." |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Intentional demo convenience that became a security vulnerability. |
| **IMPACT** | **CRITICAL (P0)** — Complete authentication bypass. Any 3-character username with known default passwords grants access. |
| **RECOMMENDED ACTION** | Remove fallback entirely. Gate behind `APP_ENV=development` at minimum, or remove completely. |

---

### Finding F08 — Hardcoded HMAC Secret

| Field | Detail |
|---|---|
| **FINDING ID** | F08 |
| **AUDIT CLAIM** | Hardcoded HMAC secret |
| **CURRENT REPOSITORY EVIDENCE** | `security.py:20`: `AUTH_SECRET_KEY = os.getenv("CITIZEN_AUTH_SECRET_KEY", "jaldrishti-citizen-auth-secret-key-2026-delta")`. Fallback is a predictable string committed to source code. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Development convenience. Secret is deterministic and in version control. |
| **IMPACT** | **HIGH (P0)** — Attacker can forge citizen auth tokens by using the known secret. |
| **RECOMMENDED ACTION** | Remove default. Require environment variable. Generate cryptographically random secret. |

---

### Finding F09 — Unsafe torch.load() Semantics

| Field | Detail |
|---|---|
| **FINDING ID** | F09 |
| **AUDIT CLAIM** | `torch.load()` used without `weights_only=True` |
| **CURRENT REPOSITORY EVIDENCE** | `inference.py:63`: `checkpoint = torch.load(str(ckpt_file), map_location=self.device)` — no `weights_only=True`. `test_convlstm_checkpoint.py:19`: same pattern. No occurrences of `weights_only` in entire codebase. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Code written before PyTorch 2.6 enforced safe loading by default. |
| **IMPACT** | **MEDIUM** — Arbitrary code execution if checkpoint file is tampered with. Risk is lower in closed environments but should be fixed. |
| **RECOMMENDED ACTION** | Add `weights_only=True` to all `torch.load()` calls. Restructure checkpoint to separate config from state_dict. |

---

### Finding F10 — Missing Dependency Pinning

| Field | Detail |
|---|---|
| **FINDING ID** | F10 |
| **AUDIT CLAIM** | Missing dependency pinning |
| **CURRENT REPOSITORY EVIDENCE** | No `requirements.txt`, no `pyproject.toml`, no `setup.py`, no `Pipfile`. Dependencies are installed inline via `pip install` in README (L65) and Dockerfile (L14) without version pins. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Project started as prototype without formal dependency management. |
| **IMPACT** | **HIGH** — Builds are non-reproducible. Breaking upstream changes in any dependency will silently break the system. |
| **RECOMMENDED ACTION** | Create `requirements.txt` with pinned versions. Add `requirements-dev.txt` for test dependencies. |

---

### Finding F11 — Missing Production Migration Architecture

| Field | Detail |
|---|---|
| **FINDING ID** | F11 |
| **AUDIT CLAIM** | Missing proper production migration architecture |
| **CURRENT REPOSITORY EVIDENCE** | `connection.py`: Schema applied from `schema.sql` on every startup via `_init_db()`. No migration framework (Alembic, etc.). No version tracking. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | SQLite with auto-init was sufficient for prototype. |
| **IMPACT** | **MEDIUM** — Schema changes require manual intervention. No rollback capability. |
| **RECOMMENDED ACTION** | Introduce Alembic or lightweight migration tracking before PostgreSQL migration. |

---

### Finding F12 — SQLite WAL in Runtime

| Field | Detail |
|---|---|
| **FINDING ID** | F12 |
| **AUDIT CLAIM** | SQLite WAL currently used in runtime |
| **CURRENT REPOSITORY EVIDENCE** | `connection.py:38`: `PRAGMA journal_mode = WAL`. Active WAL file exists: `data/jaldrishti_notifications.db-wal` (2.3MB). `imd_aws_repository.py` also imports `sqlite3`. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | SQLite was chosen for zero-configuration development. WAL mode provides adequate concurrent read performance for single-instance deployment. |
| **IMPACT** | **MEDIUM** — Acceptable for SIH demo. Not suitable for multi-process production deployment. |
| **RECOMMENDED ACTION** | Plan PostgreSQL migration for production. Keep SQLite as development/demo fallback. |

---

### Finding F13 — PostgreSQL/PostGIS Not Active in Runtime

| Field | Detail |
|---|---|
| **FINDING ID** | F13 |
| **AUDIT CLAIM** | PostgreSQL/PostGIS not actually active in runtime |
| **CURRENT REPOSITORY EVIDENCE** | `infra/postgres/` is empty. Docker compose has no PostgreSQL service. API references "PostgreSQL-compatible SQLite" at L2398, L2439 — misleading label. No `psycopg2` or `asyncpg` imports anywhere. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | PostgreSQL was planned but never implemented. |
| **IMPACT** | **LOW** for demo, **HIGH** for any production claim. |
| **RECOMMENDED ACTION** | If production deployment is claimed, implement PostgreSQL. For SIH demo, acknowledge SQLite with migration roadmap. |

---

### Finding F14 — In-Memory Event Bus/Cache/Rate Limiter

| Field | Detail |
|---|---|
| **FINDING ID** | F14 |
| **AUDIT CLAIM** | Event bus, cache, and rate limiter rely on in-memory state |
| **CURRENT REPOSITORY EVIDENCE** | `event_bus.py`: `InMemoryEventBus`. `security.py:103-109`: `MultiDimensionRateLimiter` uses `Dict[str, List[float]]` in memory. `infra/redis/` is empty. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Single-process architecture does not require distributed state. |
| **IMPACT** | **LOW** for SIH demo (single process). **HIGH** for multi-instance production. |
| **RECOMMENDED ACTION** | Accept for SIH. Add Redis migration plan for production scaling. |

---

### Finding F15 — No Complete CI/CD Pipeline

| Field | Detail |
|---|---|
| **FINDING ID** | F15 |
| **AUDIT CLAIM** | No complete CI/CD pipeline |
| **CURRENT REPOSITORY EVIDENCE** | No `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `cloudbuild.yaml`. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Prototype-stage project. |
| **IMPACT** | **MEDIUM** — No automated quality gates. |
| **RECOMMENDED ACTION** | Create GitHub Actions workflow with lint, test, security scan gates. |

---

### Finding F16 — No Mature Monitoring Stack

| Field | Detail |
|---|---|
| **FINDING ID** | F16 |
| **AUDIT CLAIM** | No mature monitoring stack |
| **CURRENT REPOSITORY EVIDENCE** | `infra/monitoring/` is empty. No Prometheus, Grafana, or structured log export configuration. Server uses `structlog` import but no log shipping. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Prototype scope. |
| **IMPACT** | **LOW** for SIH demo. Important for operational deployment. |
| **RECOMMENDED ACTION** | Add structured logging configuration. Add `/metrics` endpoint for Prometheus. Defer full monitoring stack. |

---

### Finding F17 — No Frontend Automated Test Framework

| Field | Detail |
|---|---|
| **FINDING ID** | F17 |
| **AUDIT CLAIM** | No actual frontend automated test framework |
| **CURRENT REPOSITORY EVIDENCE** | No `vitest.config.ts`, no `jest.config`, no `*.test.tsx` or `*.spec.tsx` files in `apps/web/`. 141 Python tests exist in `tests/` but zero frontend component tests. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Development focus was on backend/ML. |
| **IMPACT** | **LOW** for SIH demo. |
| **RECOMMENDED ACTION** | Add Vitest + React Testing Library. Prioritize critical path tests only. |

---

### Finding F18 — No Real Load/Performance Testing

| Field | Detail |
|---|---|
| **FINDING ID** | F18 |
| **AUDIT CLAIM** | No real load/performance testing |
| **CURRENT REPOSITORY EVIDENCE** | No k6, Locust, or artillery configuration. Some latency assertions in tests (`test_realtime_latency.py`) but these are unit-level, not load tests. |
| **STATUS** | **CONFIRMED** |
| **IMPACT** | **LOW** for SIH demo. |
| **RECOMMENDED ACTION** | Create baseline performance benchmarks. Defer production load testing. |

---

### Finding F19 — No Fuzz Testing

| Field | Detail |
|---|---|
| **FINDING ID** | F19 |
| **AUDIT CLAIM** | No fuzz testing |
| **CURRENT REPOSITORY EVIDENCE** | No Hypothesis, AFL, or fuzz testing framework present. |
| **STATUS** | **CONFIRMED** |
| **IMPACT** | **LOW** |
| **RECOMMENDED ACTION** | OPTIONAL. Add Hypothesis for input validation testing only if time permits. |

---

### Finding F20 — Incomplete GIS/Raster Assets

| Field | Detail |
|---|---|
| **FINDING ID** | F20 |
| **AUDIT CLAIM** | DEM/HAND/land-cover/population/SAR raster assets incomplete |
| **CURRENT REPOSITORY EVIDENCE** | `geospatial/dem/` contains only `terrain_summary.json` (175KB, derived summary, no actual raster). `geospatial/landcover/` is empty. `geospatial/population/` is empty. `geospatial/drainage/` has `basin_boundary.geojson` and `subbasins.geojson` (vector, not raster). `geospatial/assets/` has `critical_infrastructure.geojson`. No SAR reference data present. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Full rasters are too large for Git repository. Download/processing pipeline not implemented. |
| **IMPACT** | **HIGH** — Inundation model uses proxy terrain values instead of real DEM/HAND. |
| **RECOMMENDED ACTION** | Create download/processing scripts for FABDEM, HAND, ESA WorldCover. Track metadata only in Git. |

---

### Finding F21 — IMD AWS Integration Depends on External Authorization

| Field | Detail |
|---|---|
| **FINDING ID** | F21 |
| **AUDIT CLAIM** | IMD AWS integration exists but actual provider access depends on external authorization/IP whitelisting |
| **CURRENT REPOSITORY EVIDENCE** | `live_adapters.py`: Full `IMDLiveAdapter` implementation with client, QC, normalization, basin filtering. `imd_aws_repository.py` (13KB): SQLite-backed observation store. `.env.example` has `IMD_API_KEY=` (empty). Extensive IMD test suite (12+ test files). |
| **STATUS** | **CONFIRMED** — Integration code is comprehensive. Live access depends on IMD providing API key and IP whitelist authorization. |
| **IMPACT** | **MEDIUM** — System operates in verified fallback mode without live IMD data. |
| **RECOMMENDED ACTION** | Pursue formal IMD data access agreement. Document LIVE vs FALLBACK state clearly. |

---

### Finding F22 — CWC Access May Be Incomplete

| Field | Detail |
|---|---|
| **FINDING ID** | F22 |
| **AUDIT CLAIM** | CWC real client access may be incomplete |
| **CURRENT REPOSITORY EVIDENCE** | `hydrology_datasets.yaml` references CWC India-WRIS with `source_url: https://indiawris.gov.in/wris/#/riverMonitoring`. `.env.example` has `CWC_WRIS_TOKEN=` (empty). Historical CWC data appears to exist for evaluation. Live real-time CWC telemetry access status is unclear. |
| **STATUS** | **PARTIALLY CONFIRMED** — Historical data available for evaluation. Live telemetry access unverified. |
| **IMPACT** | **MEDIUM** |
| **RECOMMENDED ACTION** | Document which CWC data is historical vs live. Clarify access requirements. |

---

### Finding F23 — Radar Access May Be Unavailable

| Field | Detail |
|---|---|
| **FINDING ID** | F23 |
| **AUDIT CLAIM** | Radar access may be unavailable |
| **CURRENT REPOSITORY EVIDENCE** | Adapter registry includes radar source. Live adapter for radar exists in `live_adapters.py`. No radar credentials in `.env.example`. No radar data files in repository. |
| **STATUS** | **UNABLE TO VERIFY** — Code exists but no evidence of successful radar data retrieval. |
| **IMPACT** | **MEDIUM** — Nowcasting quality degrades without radar. System handles degraded mode. |
| **RECOMMENDED ACTION** | Document radar as PLANNED. Acknowledge radar-absent uncertainty expansion in model docs. |

---

### Finding F24 — Limited Live Operational Evidence

| Field | Detail |
|---|---|
| **FINDING ID** | F24 |
| **AUDIT CLAIM** | Demo works in simulation/replay but live operational evidence is limited |
| **CURRENT REPOSITORY EVIDENCE** | `SIMULATION_MODE=true` in docker-compose, `.env.example`. `is_simulation=True` throughout model responses. Live scheduler and poll infrastructure exists but no logs/evidence of successful live operation. |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | System was developed and demonstrated in simulation mode. Live mode requires external data provider access. |
| **IMPACT** | **MEDIUM** — Acceptable for SIH prototype if clearly stated. |
| **RECOMMENDED ACTION** | Do NOT claim live operational status. Label as "simulation-validated with live infrastructure ready." |

---

### Finding F25 — Implementation vs External Claim Consistency

| Field | Detail |
|---|---|
| **FINDING ID** | F25 |
| **AUDIT CLAIM** | Implementation quality is strong, but implementation vs external claim consistency must be corrected |
| **CURRENT REPOSITORY EVIDENCE** | Internal code has honest labels: `"L3_ANALYTICAL_SURROGATE"`, `model_status=CANDIDATE`, `is_simulation=True`. But README, API provenance strings, and some response metadata create inconsistency (e.g., provenance says "LSTM Probabilistic Hydrograph" for analytical model). |
| **STATUS** | **CONFIRMED** |
| **ROOT CAUSE** | Documentation was written aspirationally while code was implemented incrementally with honest internal labels. |
| **IMPACT** | **HIGH** — SIH technical reviewers will check code against claims. |
| **RECOMMENDED ACTION** | Reconcile ALL external-facing text with actual model types and statuses. |

---

## 3. Current Verified State

| Component | Current State | Assessment |
|---|---|---|
| **Backend API** | FastAPI, 2677-line monolithic `main.py`, functional | Needs router decomposition |
| **Frontend** | React+Vite, 16 views, no routing, no tests | Functional but fragile |
| **Rainfall ML** | ConvLSTM checkpoint exists (1.3MB), genuine PyTorch model, default API path routes to it. Analytical surrogate as fallback. | ConvLSTM needs validation before full promotion |
| **Hydrology ML** | Analytical surrogate only in production. LSTM/TFT/Graph code exists but untrained. | Needs honest labeling |
| **Inundation ML** | Analytical grid model in production. RF model trained but not integrated. | Needs RF integration + validation |
| **Database** | SQLite WAL, 528KB + 2.3MB WAL | Adequate for demo |
| **Auth** | Hardcoded passwords + unsafe fallback | **CRITICAL** |
| **GIS Data** | Terrain summary JSON, basin/subbasin GeoJSON, infrastructure GeoJSON | Missing actual rasters |
| **Data Providers** | Full adapter code for IMD/CWC/IMERG/INSAT/NWP/Radar. All in fallback mode. | Depends on external access |
| **Tests** | 141 Python test files, comprehensive coverage | No frontend tests |
| **Docker** | Basic docker-compose, no PostgreSQL/Redis | Minimal |
| **CI/CD** | None | Must add |
| **Monitoring** | None | Must add basics |
| **Demo** | Fully functional simulation/replay | **MUST PRESERVE** |

---

## 4. P0 Security Remediation

### 4.1 Hardcoded Admin Credentials (F06)

| Item | Detail |
|---|---|
| **Affected File** | `apps/api/main.py` (L2103-2106) |
| **Affected API** | `POST /api/v1/admin/login` |
| **Required Change** | Remove `"admin123"` and `"operator123"` default values. Require `ADMIN_PASSWORD` and `OPERATOR_PASSWORD` environment variables. If unset, refuse to start (fail closed) in production mode; in development mode, generate a random password and print to console on first startup. |
| **Migration Concern** | `.env` files must be created/updated on all deployment targets before this change. |
| **Compatibility Concern** | Anyone currently relying on default credentials will be locked out. |
| **Test Strategy** | 1. Test that missing env vars in production mode causes startup failure. 2. Test that default passwords are rejected. 3. Test that valid env-var credentials work. |
| **Rollback Strategy** | Revert to previous `main.py`. No data migration needed. |

### 4.2 Unsafe Authentication Fallback (F07)

| Item | Detail |
|---|---|
| **Affected File** | `apps/api/main.py` (L2117-2120) |
| **Affected API** | `POST /api/v1/admin/login` |
| **Required Change** | **Delete lines 2117-2120 entirely.** The fallback that accepts `admin123`/`operator123` for any username >= 3 chars must be removed unconditionally. |
| **Migration Concern** | None — this is a bug fix. |
| **Compatibility Concern** | Demo scripts that rely on arbitrary usernames will need updating. |
| **Test Strategy** | 1. Test that arbitrary username + `admin123` is rejected. 2. Test that only exact configured credentials succeed. |
| **Rollback Strategy** | Revert line deletion. |

### 4.3 Hardcoded HMAC Secret (F08)

| Item | Detail |
|---|---|
| **Affected File** | `services/notifications/security.py` (L20) |
| **Affected API** | All citizen token operations |
| **Required Change** | Remove default string `"jaldrishti-citizen-auth-secret-key-2026-delta"`. Require `CITIZEN_AUTH_SECRET_KEY` env var. In development, generate using `secrets.token_hex(32)` and warn. In production, fail if not set. |
| **Migration Concern** | Existing citizen tokens become invalid when secret changes. This is acceptable since the system is pre-production. |
| **Test Strategy** | 1. Test missing env var causes failure in production. 2. Test token creation and verification with proper secret. 3. Test that old tokens with old secret are rejected. |
| **Rollback Strategy** | Revert `security.py`. Existing tokens already invalidated. |

### 4.4 Unsafe torch.load() (F09)

| Item | Detail |
|---|---|
| **Affected Files** | `ml/rainfall/deep/inference.py` (L63), `tests/test_convlstm_checkpoint.py` (L19) |
| **Required Change** | Add `weights_only=True` to all `torch.load()` calls. Restructure checkpoint loading to: 1. Load `model_config` from a separate JSON file. 2. Load `model_state_dict` with `weights_only=True`. 3. Load `normalization_config` from separate JSON. |
| **Migration Concern** | Existing checkpoint format must be re-exported with separated config. |
| **Test Strategy** | 1. Save checkpoint in new format. 2. Load with `weights_only=True`. 3. Verify inference produces identical output. |
| **Rollback Strategy** | Keep old checkpoint file. Add flag to toggle loading mode. |

---

## 5. Authentication & Secret Migration

### 5.1 Authentication Architecture

**Target State:**

```
User Request -> Rate Limiter -> Credential Validation -> JWT Issuance -> Role-Based Access
```

**Roles preserved:** `PUBLIC_USER`, `OPERATOR`, `ADMIN` (add `ANALYST` per security.yaml)

**Required changes:**

| Component | Current | Target |
|---|---|---|
| Credential store | Hardcoded in main.py | Environment variables (Phase B), database-backed (Phase F) |
| Password storage | Plaintext comparison | bcrypt hash comparison |
| Token type | Custom HMAC | JWT with HS256 (already configured in security.yaml) |
| Token expiry | 24h citizen tokens | 24h access + 30-day refresh (per security.yaml L50-51) |
| Session management | Stateless tokens only | Add token revocation list (in-memory for demo, Redis for production) |
| Audit logging | Partial (auth events logged) | Complete (all admin actions) |

**Environment-specific configuration:**

| Setting | Development | Staging | Production |
|---|---|---|---|
| Default credentials | Generate random, print to console | Require env vars | Require env vars, fail closed |
| HMAC secret | Auto-generated per session | Env var required | Env var required, min 32 bytes |
| Token expiry | 72 hours | 24 hours | 24 hours |
| Rate limiting | Relaxed (100/min) | Standard | Standard (per security.yaml) |
| Audit logging | Console | File + console | Structured JSON + file |

### 5.2 Secret Management

**Secrets inventory:**

| Secret | Current Location | Target |
|---|---|---|
| `ADMIN_PASSWORD` | `main.py` default `"admin123"` | Environment variable, no default |
| `OPERATOR_PASSWORD` | `main.py` default `"operator123"` | Environment variable, no default |
| `ADMIN_USERNAME` | `main.py` default `"admin"` | Environment variable |
| `CITIZEN_AUTH_SECRET_KEY` | `security.py` default string | Environment variable, min 32 bytes |
| `IMD_API_KEY` | `.env.example` (empty) | Environment variable |
| `CWC_WRIS_TOKEN` | `.env.example` (empty) | Environment variable |
| `MOSDAC_API_KEY` | `.env.example` (empty) | Environment variable |
| `NASA_EARTHDATA_TOKEN` | `.env.example` (empty) | Environment variable |

**Generation and rotation:**
- All signing secrets: `python -c "import secrets; print(secrets.token_hex(32))"`
- Rotation: Generate new secret, deploy, old tokens expire naturally (24h)
- Local development: `.env` file (gitignored)
- Production: Environment variables from deployment platform

---

## 6. Scientific Claim Reconciliation

### 6.1 Claims vs Reality Matrix

| Claim Location | Claim | Actual | Discrepancy | Action |
|---|---|---|---|---|
| README L33 | "Deep ConvLSTM Nowcast" | Default API routes to ConvLSTM, but startup metadata and analytical fallback create confusion | **PARTIAL** | Clarify that ConvLSTM is default but EXPERIMENTAL status |
| README L121 | ConvLSTM CSI=0.76 | ConvLSTM actual CSI=0.712 (model_catalog.json). 0.76 belongs to analytical surrogate | **WRONG** | Fix: report 0.712 for ConvLSTM, 0.76 for analytical |
| README L128 | "LSTM with River Network Graph" NSE=0.89 | Production is analytical model. NSE=0.89 is for analytical model, not LSTM. | **MISLEADING** | Change to "Analytical Hydrograph with River Network Graph Routing" |
| README L50 | "Physics-guided UNet / Random Forest" | Production is analytical NumPy. RF model exists but not in production path | **MISLEADING** | Label as "Physics-Guided Analytical Surrogate" |
| README L131 | IoU=0.84, F1=0.88 | Actual RF IoU=0.5536, F1=0.7127 (inundation_checkpoint_meta.json). 0.84 is hardcoded in production response. | **WRONG** | Fix metrics to match verified evaluations |
| `discharge_models.py` L111 | `product_name="LSTM Probabilistic Hydrograph Forecast"` | Model is `"Analytical-Routing-v2.4"` | **MISLEADING** | Change to "Analytical Probabilistic Hydrograph Forecast" |
| `hydraulic_surrogate.py` L26 | `model_version="UNet-Surrogate-v3.1"` | No UNet architecture present | **MISLEADING** | Change to "AnalyticalSurrogate-v3.1" |

### 6.2 Model Status Framework

Every model must declare:

```
MODEL_TYPE: [ANALYTICAL | ML_TRADITIONAL | DEEP_LEARNING]
TRAINING_DATA: [SYNTHETIC | REAL_HISTORICAL | MIXED]
VALIDATION_DATA: [SYNTHETIC_HOLDOUT | REAL_EVENT_HOLDOUT | NONE]
STATUS: [BASELINE | CANDIDATE | BEST_VALIDATED_MODEL | EXPERIMENTAL | DEPRECATED]
UNCERTAINTY_METHOD: [ANALYTICAL_PARAMETRIC | ENSEMBLE | CONFORMAL | NONE]
LIMITATIONS: [free text]
```

---

## 7. ML Production Path

### 7.1 Rainfall ConvLSTM Production Activation Plan

The API default already routes to ConvLSTM (`model="convlstm"`). The ConvLSTM checkpoint exists (`convlstm_nowcast.pt`, 1.3MB, 108K parameters). However, the model's validated metrics (RMSE=11.25mm, CSI=0.712) are **worse** than the analytical surrogate's claimed metrics (RMSE=4.8mm, CSI=0.76).

**Phased plan:**

| Phase | Action | Acceptance Criteria |
|---|---|---|
| 1. Verify Checkpoint | Load checkpoint, verify architecture matches `ConvLSTMEncoderDecoder`, verify parameter count matches 108065 | Checkpoint loads without error, param count matches |
| 2. Verify Feature Schema | Confirm input shape [4, 1, 16, 24] matches inference code expectations | Shape assertions pass |
| 3. Verify Normalization | Check `normalization_config` mean=15.0, std=12.0 against training data statistics | Normalization values are physically reasonable for mm/hr |
| 4. Verify Inference Path | Run end-to-end inference from API with `model=convlstm` | Non-NaN output, physically reasonable values |
| 5. Baseline Comparison | Run both ConvLSTM and analytical on identical inputs, record outputs | Outputs differ but both are physically reasonable |
| 6. Validate Latency | Benchmark ConvLSTM inference time on CPU | Less than 500ms for single forecast |
| 7. Validate Accuracy | Run hindcast evaluation on held-out events | Document actual CSI, RMSE with provenance |
| 8. Shadow Mode | Route 100% traffic to analytical, log ConvLSTM shadow predictions | 48h shadow run without errors |
| 9. Controlled Promotion | Route 10% then 50% then 100% traffic to ConvLSTM | No regression in system stability |
| 10. Production Activation | Set ConvLSTM as sole default, deprecate analytical as fallback only | Metrics recorded in model registry |

**Rollback mechanism:** Query parameter `model=analytical` always available. Feature flag `RAINFALL_MODEL=convlstm|analytical` in environment.

**CRITICAL DECISION:** ConvLSTM's actual metrics (CSI=0.712, RMSE=11.25) are **worse** than analytical claims. Before promotion, either:
- a) Accept lower metrics with honest reporting, OR
- b) Retrain ConvLSTM with more data/epochs (current: only 5 epochs per checkpoint metadata)

---

## 8. Real-Data Training Strategy

### 8.1 Current Training Data State

| Dataset | Type | Size | Location |
|---|---|---|---|
| `rainfall_events_train.csv` | SYNTHETIC | 93KB | `data/simulation/` |
| `rainfall_events_val.csv` | SYNTHETIC | 23KB | `data/simulation/` |
| `hydrograph_events_train.csv` | SYNTHETIC | 101KB | `data/simulation/` |
| `hydrograph_events_val.csv` | SYNTHETIC | 25KB | `data/simulation/` |
| `inundation_samples_train.csv` | SYNTHETIC | 75KB | `data/simulation/` |
| `inundation_samples_val.csv` | SYNTHETIC | 19KB | `data/simulation/` |
| CWC historical telemetry | REAL | Referenced only | `hydrology_datasets.yaml` |

### 8.2 Transition Plan

**Immediate (no external access required):**
1. Process CWC historical data (already referenced with checksums) into training format
2. Create proper temporal split: Train <= 2022, Validate 2023, Test 2024
3. Implement whole-event holdout: entire flood events are either train OR test, never split
4. Ensure normalization statistics computed ONLY on training set

**Upon IMD data access:**
1. Download historical IMD AWS observations for Odisha
2. Apply same QC pipeline used in live ingestion
3. Create paired rainfall-discharge event datasets
4. Spatial separation: hold out 2-3 stations entirely for spatial generalization test

**Data quality controls:**
- No future leakage: strictly temporal ordering
- No test rebalancing: maintain natural class distribution
- Versioned splits with manifest files and checksums
- Reproducible: seed all random operations

---

## 9. Hydrology Model Strategy

### 9.1 Model Disposition

| Model | File | Status | Training Data | Trained Checkpoint | Decision | Reasoning |
|---|---|---|---|---|---|---|
| Autoregressive Persistence | (inline) | BASELINE | N/A | N/A | **KEEP** | Necessary baseline |
| XGBoost Discharge | `xgboost_forecast.py` | VALIDATED | `streamflow_gb_model.joblib` exists | Yes (298KB) | **KEEP + VALIDATE** | Verified loadable, useful ensemble member |
| LSTM Sequence | `lstm_forecast.py` | Code only | No checkpoint | No | **SHADOW** | Rename from misleading "LSTM" alias. Train on real CWC data before considering. |
| TFT Model | `tft_model.py` | Code only | No checkpoint | No | **DEPRECATE** until data available | Architecture code exists but no training infrastructure |
| Graph Model | `graph_model.py` | Code only | No checkpoint | No | **DEPRECATE** until data available | Promising but requires substantial training |
| Analytical Routing | `discharge_models.py` | CANDIDATE | N/A (analytical) | N/A | **KEEP as production + rename** | Currently production. Must fix misleading "LSTM" provenance label. |

### 9.2 Production Path

**Short term:** Keep analytical routing as production model. Fix all labels to say "Analytical" not "LSTM". Report metrics honestly.

**Medium term:** Train XGBoost discharge model on real CWC data. Shadow compare against analytical. Promote if NSE improves.

**Long term:** Train LSTM on real CWC data if sufficient temporal coverage (>= 3 monsoon seasons) becomes available.

---

## 10. Inundation Model Strategy

### 10.1 Current State

- Production: `HydraulicSurrogateModel` — purely analytical (NumPy grid math)
- Named "UNet-Surrogate-v3.1" — no UNet present
- RF model trained (`inundation_rf_model.joblib`, 724KB) but not integrated
- Hardcoded metrics in response: IoU=0.84, F1=0.88
- Actual RF metrics: IoU=0.5536, F1=0.7127

### 10.2 Progression Plan

| Phase | Model | Validated Metric Source | Depth Capability |
|---|---|---|---|
| **Current** | Analytical grid surrogate | None (hardcoded) | MODEL_ESTIMATE |
| **Phase 1** | Integrate RF model as shadow | `inundation_checkpoint_meta.json` | MODEL_ESTIMATE |
| **Phase 2** | RF promoted to production | Held-out event validation | MODEL_ESTIMATE |
| **Phase 3** | Add real DEM/HAND terrain inputs | Validation against SAR reference | MODEL_ESTIMATE |
| **Phase 4** | Calibrated operational model | Multi-event validation | MODEL_ESTIMATE with calibration |

### 10.3 Critical Distinctions

- **Extent validation:** Possible via Sentinel-1 SAR binary flood masks. This is what IoU measures.
- **Depth validation:** NOT possible without in-situ depth gauges. Current `DepthValidationStatus.UNAVAILABLE` is honest and must remain.
- **DEM requirement:** Current model uses proxy elevation. Real FABDEM/HAND needed for Phase 3+.

---

## 11. GIS Data Acquisition

| Asset | Required | Source | Format | Resolution | Current State | Action |
|---|---|---|---|---|---|---|
| DEM | Yes | FABDEM (free, academic) | GeoTIFF | 30m | `terrain_summary.json` only | Download + clip to basin |
| HAND | Yes | Derived from DEM + drainage | GeoTIFF | 30m | Missing | Compute from DEM using pyflwdir or TauDEM |
| Land Cover | Yes | ESA WorldCover 2021 | GeoTIFF | 10m | Empty directory | Download + clip to basin |
| Population | Yes | WorldPop/GHSL | GeoTIFF | 100m-1km | Empty directory | Download + clip to basin |
| SAR Reference | For validation | Sentinel-1 GRD IW | GeoTIFF | 10m | Missing | Download for specific flood events via Copernicus |
| Basin Boundary | Done | In repository | GeoJSON | — | `drainage/basin_boundary.geojson` | Complete |
| Subbasins | Done | In repository | GeoJSON | — | `drainage/subbasins.geojson` | Complete |
| Infrastructure | Done | In repository | GeoJSON | — | `assets/critical_infrastructure.geojson` | Complete |

**License considerations:** FABDEM requires academic license agreement. ESA WorldCover is CC-BY-4.0. WorldPop is CC-BY-4.0. Sentinel-1 is free and open. All are compatible with SIH use.

---

## 12. Provider Integration Strategy

| Provider | Current State | Blocker | Fallback | Data Type | Target |
|---|---|---|---|---|---|
| **IMD AWS** | Full adapter code, SQLite repo | API key + IP whitelist from IMD | Simulation data | LIVE OBSERVED | Operational live polling |
| **CWC** | Historical data referenced | WRIS token access | Historical replays | HISTORICAL OBSERVED + possible LIVE | Live telemetry |
| **IMERG** | Adapter code exists | NASA Earthdata token | Simulated rainfall | MODELED/OBSERVED SATELLITE | Near-real-time satellite precipitation |
| **INSAT-3DR** | Adapter code exists | MOSDAC API key | Simulated | OBSERVED SATELLITE | Cloud imagery + derived products |
| **Radar** | Adapter code exists | Unknown access path | Degraded mode (no radar) | LIVE OBSERVED | Paradip DWR scans |
| **NWP/ECMWF** | Adapter code exists | `ECMWF_OPEN_DATA_ENABLED=false` | Forecast features removed | FORECAST | NWP inputs for longer lead times |
| **GloFAS** | Documentation exists | Copernicus CDS API | Local analytical | FORECAST | Global flood forecasting fallback |
| **Bhuvan** | Reference registry exists | ISRO Bhuvan API | None | REFERENCE | Satellite imagery overlay |
| **Sentinel-1** | Reference in inundation model | Copernicus CDSE | None | REFERENCE | SAR flood extent validation |

---

## 13. IMD AWS Operationalization

### 13.1 Specific Requirements

| Requirement | Detail |
|---|---|
| **Access protocol** | REST API via `city.imd.gov.in` or equivalent IMD open data gateway |
| **IP whitelisting** | Server's public IP must be registered with IMD |
| **Connection verification** | Handshake test: GET single station observation, verify schema match |
| **Station discovery** | Query all Odisha AWS stations, filter by basin bounding box (19.80-21.05 N, 84.80-87.20 E) |
| **Normalization** | Map IMD field names to internal schema (`StationObservation` model) |
| **QC** | Apply `QualityControlEngine`: physical bounds, spike detection, staleness |
| **Freshness** | Mark observation `STALE` if >30 min old, `OFFLINE` if >120 min |
| **Persistence** | Store in SQLite/PostgreSQL via `imd_aws_repository` |
| **Event bus** | Emit `NEW_OBSERVATION` event on fresh data arrival |
| **WebSocket** | Broadcast observation update to connected clients |
| **Dashboard** | Display station markers with color-coded freshness |
| **Failure state** | Log failure, continue with last known observation, mark `DATA_DEGRADED` |

### 13.2 Acceptance Criterion for LIVE_OBSERVED

```
LIVE_OBSERVED = (
    api_key IS SET
    AND connection_test PASSES
    AND at_least_3_stations RETURN data
    AND freshness < 30_minutes
    AND qc_pass_rate > 80%
    AND data_matches_schema
)
```

---

## 14. Database Migration

### 14.1 Migration Path: SQLite to PostgreSQL + PostGIS

**Current SQLite usage:**
1. Notifications database: `data/jaldrishti_notifications.db` (528KB + 2.3MB WAL)
2. IMD AWS repository: separate SQLite usage in `imd_aws_repository.py`

**Migration sequence:**

| Step | Action | Risk | Rollback |
|---|---|---|---|
| 1 | Create PostgreSQL schema matching current SQLite schema | None | Drop new schema |
| 2 | Add Alembic migration framework | None | Remove Alembic |
| 3 | Create database abstraction layer (interface over SQLite/PostgreSQL) | Low | Revert to direct SQLite |
| 4 | Configure PostgreSQL in Docker compose | None | Remove service |
| 5 | Data migration: export SQLite, import PostgreSQL | Low | Keep SQLite as backup |
| 6 | Add PostGIS extension for spatial queries | None | Use standard geometry |
| 7 | Update connection strings via environment variable | Low | Revert env var |
| 8 | Dual-read testing: both databases, compare results | None | — |
| 9 | Switch reads to PostgreSQL | Medium | Switch back to SQLite |
| 10 | Switch writes to PostgreSQL | Medium | Switch back to SQLite |
| 11 | Remove SQLite code paths | Low | Keep as fallback |

**Connection pooling:** Use `asyncpg` with pool size 5-10 (adequate for SIH scale).

**Redis requirement determination:** Redis is needed IF:
- Multi-process deployment is planned: YES for rate limiting, session storage
- Distributed event bus is needed: YES for pub/sub
- Caching layer is needed: NOT NECESSARY for SIH demo scale

**Recommendation:** Add Redis to docker-compose but make it **OPTIONAL** for initial deployment. In-memory fallback remains for single-process mode.

---

## 15. Distributed State

### 15.1 Component Analysis

| Component | Current | Must Distribute? | Reasoning | Target |
|---|---|---|---|---|
| Event Bus | `InMemoryEventBus` | **NO** for SIH | Single process is sufficient | Keep in-memory; add Redis adapter interface for future |
| Rate Limiter | In-memory dict | **NO** for SIH | Single process adequate | Keep in-memory; Redis adapter for production |
| Forecast Cache | In-memory | **NO** for SIH | Cache invalidation on single process is trivial | Keep in-memory |
| Session/Token Revocation | None currently | **OPTIONAL** | Short-lived tokens (24h) reduce revocation need | In-memory revocation list, Redis if multi-instance |
| Notification Queue | In-memory async queue | **NO** for SIH | Single worker adequate | Keep in-memory |

**Decision:** Do NOT introduce Redis as a hard requirement for SIH demo. Prepare adapter interfaces that allow Redis to be plugged in.

---

## 16. API Architecture

### 16.1 Router Decomposition Plan

Current: `main.py` = 2677 lines, all routes in single file.

**Proposed decomposition (additive, not rewrite):**

| Router Module | Routes to Extract | Estimated Lines |
|---|---|---|
| `routers/health.py` | `/health`, `/ready`, `/info` | ~80 |
| `routers/basins.py` | `/basins`, `/stations` | ~150 |
| `routers/rainfall.py` | `/rainfall/*` | ~200 |
| `routers/hydrology.py` | `/hydrology/*` | ~200 |
| `routers/inundation.py` | `/inundation/*` | ~150 |
| `routers/alerts.py` | `/alerts/*` | ~300 |
| `routers/data_health.py` | `/data-health/*` | ~100 |
| `routers/replay.py` | `/replay/*` | ~150 |
| `routers/notifications.py` | `/notifications/*`, `/public/*` | ~400 |
| `routers/admin.py` | `/admin/*` | ~500 |
| `routers/forecast.py` | `/forecast/*` | ~150 |
| `routers/demo.py` | `/demo/*` | ~200 |
| `main.py` | App init, middleware, WebSocket, singleton setup | ~400 |

**Migration sequence:** Extract one router at a time, starting with lowest-risk (health) and ending with highest-risk (admin). Each extraction must preserve all existing routes and response schemas.

---

## 17. Event Bus

### 17.1 Current State

- `InMemoryEventBus` with typed `EventType` enum and `EventPriority`
- `EventStore` for persisted event history
- `EventDispatcher` bridges to WebSocket broadcast

### 17.2 Improvements (Conservative)

| Improvement | Complexity | Value | Priority |
|---|---|---|---|
| Add event schema validation (Pydantic) | Low | High — prevents malformed events | SHOULD HAVE |
| Add idempotency keys | Low | Medium — prevents duplicate processing | SHOULD HAVE |
| Add event ordering guarantees | Medium | Low — single process already ordered | OPTIONAL |
| Add retry with exponential backoff | Low | Medium — resilient handler execution | SHOULD HAVE |
| Add dead-letter logging | Low | Medium — debuggability | SHOULD HAVE |
| Distributed Redis pub/sub | High | Low for SIH | OPTIONAL |

---

## 18. Real-Time Architecture

### 18.1 Target Pipeline

```
SOURCE -> INGESTION -> QC -> EVENT -> STATE -> MODEL -> RISK -> ALERT -> NOTIFICATION -> WEBSOCKET -> UI
```

| Stage | Current State | Latency | Failure Mode | Target |
|---|---|---|---|---|
| SOURCE | Simulation adapters | N/A | Fixed data | Live polling (when access granted) |
| INGESTION | `IMDLiveAdapter` + others | ~10s (simulated) | Timeout then fallback | Real HTTP with retry |
| QC | `QualityControlEngine` | <10ms | Pass-through on error | Same, add anomaly flag |
| EVENT | `InMemoryEventBus` | <1ms | Silent drop | Add error logging |
| STATE | `CurrentStateManager` | <5ms | Stale state | Add staleness indicator |
| MODEL | ConvLSTM / Analytical | <500ms | Fallback to analytical | Shadow mode |
| RISK | `RiskService` | <10ms | Previous risk level | Same |
| ALERT | `AlertEngine` | <10ms | No alert | Same |
| NOTIFICATION | Queue then providers | Variable | Mock delivery | Real SMS/push when configured |
| WEBSOCKET | Direct broadcast | <50ms | Client disconnect | Same |
| UI | React state update | <100ms | Stale display | Same |

### 18.2 Realistic SLO Goals

| Metric | Target | Measurement |
|---|---|---|
| End-to-end ingestion to UI update | < 5 seconds | Timestamp diff |
| Model inference (rainfall) | < 1 second | Timer |
| WebSocket broadcast latency | < 200ms | Timer |
| Data source freshness indicator | Accurate within 1 minute | Comparison |

---

## 19. Frontend Engineering

### 19.1 Current Assessment

- 16 views, no client-side routing (uses `switch/case` in `App.tsx`)
- No error boundaries
- No component tests
- Large view components (AdminSecurityView = 63KB)
- WebSocket with graceful degradation (good)
- Multi-language support (en/hi) (good)
- Theme support (good)

### 19.2 Plan

| Task | Priority | Effort |
|---|---|---|
| Add React Router for URL-based navigation | SHOULD HAVE | Medium |
| Add React Error Boundaries around each view | MUST HAVE | Low |
| Add loading states for all API-dependent views | SHOULD HAVE | Low |
| Add empty/error states for failed fetches | SHOULD HAVE | Low |
| Extract AdminSecurityView into sub-components | SHOULD HAVE | Medium |
| Add Vitest + React Testing Library | SHOULD HAVE | Medium |
| Write tests for critical paths (login, alert display, replay) | SHOULD HAVE | Medium |
| Cosmetic redesign | OPTIONAL | N/A |

---

## 20. Map / GIS UX

### 20.1 Layer Plan

| Layer | Type | Default | Source |
|---|---|---|---|
| Base map (OSM) | Raster tiles | ON | OpenStreetMap |
| Basin boundary | Vector (GeoJSON) | ON | `drainage/basin_boundary.geojson` |
| Station markers | Point markers | ON | API `/stations` |
| Alert polygons | Vector | ON (if active) | API `/alerts` |
| Inundation flood extent | Vector polygons | ON (if active) | API `/inundation/forecast` |
| Subbasin boundaries | Vector | OFF | `drainage/subbasins.geojson` |
| Critical infrastructure | Point/polygon | OFF | `assets/critical_infrastructure.geojson` |
| Depth grid heatmap | Raster overlay | OFF | Inundation depth grid |
| River network | Line | OFF | Derived from basin config |

### 20.2 Performance

- Use vector tiles for large polygon layers
- Simplify polygon geometries for zoom levels < 10
- Lazy-load advanced layers
- Cluster station markers when >20 visible

---

## 21. Alert Safety

### 21.1 Current Strengths (Preserve)

- Human-in-the-loop review for RED alerts
- Hysteresis (prevents rapid oscillation)
- Deduplication
- Severity thresholds
- Geofencing for targeted alerts
- Audit logging

### 21.2 Improvements

| Improvement | Detail |
|---|---|
| **Stale-data behavior** | If ALL data sources are >2h stale, suppress new alerts and display "DATA UNAVAILABLE" warning |
| **Source degradation** | If <50% of expected sources available, auto-downgrade alert confidence |
| **False-alert suppression** | Require minimum 2 consecutive forecast cycles agreeing before issuing new RED alert |
| **Alert explainability** | Already implemented via `WhyRiskChangedCard`. Ensure it is populated in every alert. |
| **Auditability** | Already implemented via `alert_audit_logger`. Ensure all state transitions are logged. |

---

## 22. Citizen Notification

### 22.1 Pipeline

```
Alert (approved) -> Geofence Match -> Policy Check -> Template Render -> Queue -> Provider -> Delivery
```

### 22.2 Current Implementation Review

- `MockSMSSink` and `MockPushSink` for development
- `MSG91Provider` and `TwilioSMSProvider` for real SMS
- `FCMPushProvider` for real push
- `InAppNotificationProvider` for in-app
- Geofence engine
- Policy engine
- Template engine
- Delivery tracking

### 22.3 Safety Requirements

| Requirement | Current State | Action |
|---|---|---|
| MOCK vs LIVE separation | Mock providers used when credentials absent | Add explicit `MOCK_DELIVERY` flag in response |
| Outside-geofence filtering | Geofence engine checks containment | Adequate |
| Duplicate prevention | Notification dedup exists | Adequate |
| Rate limiting per user | In-memory rate limiter | Adequate for single instance |
| Delivery audit trail | SQLite-backed audit | Adequate |

---

## 23. Admin Portal

### 23.1 Current 10 Sections

The AdminSecurityView (63KB) contains: Overview, Alert Operations, Data Sources, Security, Database, Event Bus, WebSocket, Notifications, Models, Audit.

### 23.2 Assessment

| Section | Status | Action |
|---|---|---|
| Overview | Functional | No change |
| Alert Operations | Functional | No change |
| Data Sources | Functional | No change |
| Security | Shows auth config, rate limits | Add credential rotation indicators |
| Database | Shows SQLite stats | Update labels post-PostgreSQL migration |
| Event Bus | Shows event counts | No change |
| WebSocket | Shows connection count | No change |
| Notifications | Shows delivery stats | No change |
| Models | Shows model registry | Fix metrics to match verified values |
| Audit | Shows audit trail | No change |

**Decision:** No rebuild necessary. Fix model metrics display and credential indicators only.

---

## 24. Model Registry & Metric Contract

### 24.1 Authoritative Metric Contract

Every metric MUST have:

| Field | Description |
|---|---|
| `model_id` | Unique model identifier |
| `version` | Semantic version |
| `dataset_id` | Which dataset was used for evaluation |
| `dataset_state` | SYNTHETIC / REAL_HISTORICAL / MIXED |
| `partition` | TRAIN / VALIDATION / TEST / HOLDOUT |
| `horizon` | Lead time range this metric applies to |
| `metric_name` | Standard name (CSI, NSE, RMSE, IoU, F1, etc.) |
| `metric_value` | Numeric value |
| `metric_unit` | Unit (mm, hours, %, dimensionless) |
| `aggregation` | Mean / Median / Event-weighted |
| `computed_at` | Timestamp of evaluation |
| `artifact_path` | Path to evaluation output file |

### 24.2 Current Discrepancies to Fix

| Model | Metric | README | model_catalog.json | checkpoint_meta.json | Correct Value |
|---|---|---|---|---|---|
| ConvLSTM | CSI (>35mm) | 0.76 | 0.712 | — | **0.712** (from catalog) |
| ConvLSTM | RMSE | 4.8mm | 11.25mm | — | **11.25mm** (from catalog) |
| Analytical L3 | CSI | — | 0.76 | — | 0.76 (belongs to analytical, NOT ConvLSTM) |
| Inundation RF | IoU | 0.84 | 0.796 | 0.5536 | **0.5536** (from checkpoint meta, most authoritative) |
| Inundation RF | F1 | 0.88 | 0.887 | 0.7127 | **0.7127** (from checkpoint meta) |
| Hydrology Analytical | NSE | 0.89 | 0.89 | — | 0.89 (but must label as ANALYTICAL, not LSTM) |

---

## 25. Validation & Leakage

### 25.1 Current Safeguards (Preserve)

- Temporal split enforcement
- Whole-event holdout
- Training-only normalization statistics
- No test rebalancing
- Leakage detection tests (`test_convlstm_leakage.py`, `test_hydrology_leakage.py`)
- `ml/inundation/leakage.py` leakage audit module

### 25.2 Strengthen

| Area | Current | Improvement |
|---|---|---|
| Spatial isolation | Not explicitly tested | Add test that no station appears in both train and spatial-holdout |
| Feature leakage | Basic checks | Add assertion that no future-timestamped feature enters model input |
| Normalization verification | Mean/std from config | Add test that normalization stats match training-set-only computation |

---

## 26. Testing Strategy

### 26.1 Current Test Suite

141 Python test files covering: backend API, ML models, security, alerts, events, notifications, replay, demo, hydrology, inundation, risk, probabilistic forecasting, IMD AWS, real-time systems.

### 26.2 Testing Pyramid

| Level | Current | Target | Gap |
|---|---|---|---|
| **Unit** | 141 files (extensive) | Maintain + add normalization tests | Minimal gap |
| **Integration** | Partial (API endpoint tests) | Add database integration tests | Medium gap |
| **API** | httpx-based endpoint tests exist | Add schema validation tests | Small gap |
| **Frontend** | Zero | Add Vitest + 5-10 critical path tests | **Large gap** |
| **E2E** | Demo scenario tests exist | Add Playwright/Cypress for UI flows | OPTIONAL |
| **Performance** | `test_realtime_latency.py` (unit-level) | Add k6/Locust load test script | Medium gap |
| **Security** | 11 security test files | Add credential-rotation test | Small gap |
| **Data Validation** | Model honesty + leakage tests | Add metric consistency test | Small gap |

### 26.3 Minimum High-Value New Tests

| Test | Value | Effort |
|---|---|---|
| Test that default credentials are rejected when env vars set | P0 | 15 min |
| Test ConvLSTM vs analytical output consistency | P1 | 1 hour |
| Test metric contract: all README metrics match model_catalog | P1 | 30 min |
| Frontend: login flow renders and submits | P2 | 2 hours |
| Frontend: alert panel displays when alerts active | P2 | 2 hours |
| Load test: 50 concurrent API requests | P2 | 2 hours |

---

## 27. Performance Strategy

### 27.1 Baseline Benchmarks to Establish

| Benchmark | Target | Method |
|---|---|---|
| `/api/v1/rainfall/nowcast` response time | < 1s (analytical), < 2s (ConvLSTM) | httpx timer |
| `/api/v1/hydrology/forecast` response time | < 500ms | httpx timer |
| `/api/v1/inundation/forecast` response time | < 500ms | httpx timer |
| WebSocket broadcast to 10 clients | < 200ms | Timer |
| ConvLSTM single inference | < 500ms on CPU | PyTorch timer |
| SQLite query (notification lookup) | < 50ms | Timer |
| Full forecast pipeline (all models) | < 3s | End-to-end timer |

### 27.2 Approach

**Rule: Do not optimize before measuring.** Establish baselines first. Optimize only if baselines exceed target by >2x.

---

## 28. Observability

### 28.1 Metrics

| Metric | Type | Collection |
|---|---|---|
| Data source freshness (per provider) | Gauge | Emit on ingestion cycle |
| API request latency (per endpoint) | Histogram | Middleware timer |
| ML inference duration (per model) | Histogram | Model wrapper |
| Event bus queue depth | Gauge | Periodic sample |
| WebSocket connected clients | Gauge | ConnectionManager |
| Notification delivery success rate | Counter | Provider callback |
| Database query latency | Histogram | Connection wrapper |
| Alert state transitions | Counter | Alert engine |

### 28.2 Structured Logging

- Use `structlog` (already imported) consistently
- Log format: JSON with `timestamp`, `level`, `event`, `context`
- **REDACT:** Phone numbers, tokens, credentials in all log output
- Add request ID tracking via `X-Request-ID` header

---

## 29. CI/CD

### 29.1 GitHub Actions Pipeline

```yaml
# Proposed workflow structure (DO NOT IMPLEMENT YET)
jobs:
  lint:
    # Python: flake8 + black --check
    # Frontend: eslint
  
  test:
    # Python: pytest tests/ -v
    # Frontend: vitest (once tests exist)
  
  security:
    # bandit (Python security linter)
    # pip-audit (dependency vulnerabilities)
    # Check for hardcoded secrets (trufflehog or custom)
  
  build:
    # Docker build API image
    # Docker build Web image
  
  deploy:
    # Only on main branch
    # Only after all gates pass
    # Manual approval for production
```

### 29.2 Quality Gates

| Gate | Blocks Deploy? | Threshold |
|---|---|---|
| Python tests pass | Yes | 100% pass |
| No hardcoded secrets detected | Yes | Zero findings |
| No critical security vulnerabilities | Yes | Zero critical |
| Docker build succeeds | Yes | Clean build |
| Frontend lint passes | No (warning only initially) | — |

---

## 30. Deployment

### 30.1 Environment Stages

| Stage | Purpose | Infrastructure | Database |
|---|---|---|---|
| **LOCAL** | Developer machine | Python + npm dev servers | SQLite |
| **DEV** | Integration testing | Docker compose (no PostgreSQL) | SQLite |
| **STAGING** | Pre-production validation | Docker compose + PostgreSQL + Redis | PostgreSQL |
| **PRODUCTION** | Live deployment | Docker compose + PostgreSQL + Redis + TLS | PostgreSQL |

### 30.2 Docker Compose Enhancement

Current docker-compose.yml has only `api` and `web` services.

**Target addition (when needed):**
```yaml
services:
  api: # existing, enhanced
  web: # existing
  postgres: # new, when migrated
  redis: # new, optional
```

### 30.3 Current State

**DO NOT claim production deployment.** Current system is validated for LOCAL + DEV stages only.

---

## 31. Backup & Disaster Recovery

### 31.1 Current State

- SQLite database: file-system backup only
- No automated backup schedule
- No documented restore procedure

### 31.2 Plan

| Component | RPO | RTO | Backup Method |
|---|---|---|---|
| SQLite database (pre-migration) | 1 hour | 10 minutes | Cron job: `sqlite3 .backup` to timestamped file |
| PostgreSQL (post-migration) | 1 hour | 30 minutes | `pg_dump` to compressed archive |
| Model checkpoints | N/A (version controlled) | 5 minutes | Git repository |
| Configuration | N/A (version controlled) | 5 minutes | Git repository |
| User data (registrations) | 1 hour | 30 minutes | Database backup |

---

## 32. Cost / Complexity Control

### 32.1 Technology Assessment

| Component | Value | Complexity | Cost | Necessity |
|---|---|---|---|---|
| PostgreSQL | High (spatial queries, concurrency) | Medium | Free (open source) | **SHOULD HAVE** |
| Redis | Medium (rate limiting, pub/sub) | Low | Free (open source) | **OPTIONAL** for SIH |
| Alembic migrations | High (schema safety) | Low | Free | **SHOULD HAVE** |
| GitHub Actions CI | High (quality gates) | Low | Free (public repos) | **MUST HAVE** |
| Prometheus + Grafana | Medium (observability) | Medium | Free | **OPTIONAL** for SIH |
| Kubernetes | Low (overkill for SIH) | High | Variable | **NOT RECOMMENDED** |
| GPU infrastructure | Low (108K params, CPU adequate) | High | Expensive | **NOT RECOMMENDED** |
| Message queue (RabbitMQ/Kafka) | Low (in-memory adequate) | High | Free but complex | **NOT RECOMMENDED** |
| Microservices architecture | Low (monolith adequate) | Very High | N/A | **NOT RECOMMENDED** |
| Additional AI/ML models | Low (focus on existing) | High | N/A | **NOT RECOMMENDED** |

### 32.2 Principle

This is a student/SIH prototype. Every infrastructure addition must pass the test:

> "Does this solve a problem that would be visible in an SIH technical review?"

If not, it is OPTIONAL at best.

---

## 33. Dependency Graph

```
Phase A: P0 Security
  |
  v
Phase B: Auth & Secrets
  |
  v
Phase C: Scientific Claim Reconciliation
  |
  v
Phase D: Real ML Production Paths ---------> Phase L: Model Registry & Metrics
  |                                                        |
  v                                                        v
Phase E: Dependency Pinning                  Phase M: Final SIH Validation
  |
  v
Phase F: Real Data & GIS
  |
  v
Phase G: Database Migration
  |
  v
Phase H: API Architecture
  |
  v
Phase I: Real-Time & Event Bus
  |
  v
Phase J: Frontend Quality
  |
  v
Phase K: Testing & Observability
  |
  v
Phase L: CI/CD & Deployment
  |
  v
Phase M: Final SIH Validation
```

**Critical Path:** A -> B -> C -> D -> L -> M

**Parallel Track 1:** E -> G -> H -> I -> J -> K -> L  
**Parallel Track 2:** F (data acquisition, parallel with other tracks)

---

## 34. Implementation Phases

### Phase A — P0 Security (IMMEDIATE)

| Field | Detail |
|---|---|
| **OBJECTIVE** | Eliminate all P0 security vulnerabilities |
| **WHY NOW** | Any security review will immediately fail the project |
| **DEPENDENCIES** | None |
| **FILES AFFECTED** | `apps/api/main.py`, `services/notifications/security.py`, `ml/rainfall/deep/inference.py`, `tests/test_convlstm_checkpoint.py` |
| **DATABASE IMPACT** | None |
| **API IMPACT** | Login endpoint behavior changes (rejects default creds) |
| **FRONTEND IMPACT** | Login with `admin123` will stop working |
| **ML IMPACT** | Checkpoint loading becomes safer |
| **SECURITY IMPACT** | Eliminates credential bypass, token forgery, code execution risk |
| **RISK** | Demo login scripts break. Mitigate by providing `.env.example` with instructions. |
| **ROLLBACK PLAN** | Revert affected files |
| **TEST PLAN** | Run existing `test_security_*` tests. Add test for credential rejection. |
| **ACCEPTANCE CRITERIA** | 1. No default passwords accepted. 2. Fallback auth removed. 3. HMAC requires env var. 4. torch.load uses weights_only. |
| **DEFINITION OF DONE** | All security tests pass. Manual verification of login rejection with default credentials. |

---

### Phase B — Authentication & Secret Migration

| Field | Detail |
|---|---|
| **OBJECTIVE** | Implement proper credential management and secret rotation |
| **WHY NOW** | Phase A removes defaults; Phase B provides the replacement |
| **DEPENDENCIES** | Phase A |
| **FILES AFFECTED** | `apps/api/main.py`, `services/notifications/security.py`, `.env.example`, NEW: `services/auth/` module |
| **DATABASE IMPACT** | None initially (credentials in env vars) |
| **API IMPACT** | Login flow unchanged externally; internally uses bcrypt |
| **FRONTEND IMPACT** | None |
| **ML IMPACT** | None |
| **SECURITY IMPACT** | Proper password hashing, secret generation |
| **RISK** | Low — additive changes |
| **ROLLBACK PLAN** | Revert auth module, restore previous credential check |
| **TEST PLAN** | `test_security_auth.py` updated for bcrypt. New tests for secret generation. |
| **ACCEPTANCE CRITERIA** | 1. Passwords hashed with bcrypt. 2. HMAC secret >= 32 bytes. 3. `.env.example` documents all required secrets. |
| **DEFINITION OF DONE** | Auth tests pass. Documentation updated. |

---

### Phase C — Scientific Claim Reconciliation

| Field | Detail |
|---|---|
| **OBJECTIVE** | Align all external-facing claims with verified implementation |
| **WHY NOW** | Must be done before SIH review |
| **DEPENDENCIES** | None (can be done in parallel with A/B) |
| **FILES AFFECTED** | `README.md`, `model_registry/model_catalog.json`, `ml/streamflow/discharge_models.py` (provenance label), `ml/inundation/hydraulic_surrogate.py` (model version name), `apps/api/main.py` (FORECAST_RUNS metadata) |
| **DATABASE IMPACT** | None |
| **API IMPACT** | Model version strings in API responses change |
| **FRONTEND IMPACT** | Model names displayed may change |
| **ML IMPACT** | No model behavior change — labels only |
| **SECURITY IMPACT** | None |
| **RISK** | Very low — text changes only |
| **ROLLBACK PLAN** | Revert text changes |
| **TEST PLAN** | Run `test_model_honesty.py`. Add metric consistency test. |
| **ACCEPTANCE CRITERIA** | 1. README metrics match model_catalog verified values. 2. No provenance label says "LSTM" for analytical model. 3. No "UNet" label for analytical surrogate. |
| **DEFINITION OF DONE** | `test_model_honesty.py` passes. README review confirms accuracy. |

---

### Phase D — Real ML Production Paths

| Field | Detail |
|---|---|
| **OBJECTIVE** | Validate ConvLSTM production path. Fix hydrology/inundation model labels. |
| **WHY NOW** | Core scientific credibility |
| **DEPENDENCIES** | Phase C (labels must be correct before model promotion) |
| **FILES AFFECTED** | `ml/rainfall/deep/inference.py`, `ml/rainfall/nowcast_models.py`, `ml/streamflow/discharge_models.py`, `ml/inundation/hydraulic_surrogate.py`, `apps/api/main.py` |
| **DATABASE IMPACT** | None |
| **API IMPACT** | Rainfall endpoint output may change numerically (ConvLSTM vs analytical) |
| **FRONTEND IMPACT** | Displayed forecasts may change |
| **ML IMPACT** | ConvLSTM validated and shadow-tested |
| **SECURITY IMPACT** | None |
| **RISK** | Medium — model output changes. Mitigate with shadow mode. |
| **ROLLBACK PLAN** | Feature flag `RAINFALL_MODEL=analytical` reverts to old behavior |
| **TEST PLAN** | Shadow comparison test. Hindcast evaluation on held-out events. |
| **ACCEPTANCE CRITERIA** | 1. ConvLSTM produces physically reasonable output. 2. Shadow comparison documented. 3. Feature flag works bidirectionally. |
| **DEFINITION OF DONE** | ConvLSTM validation report produced. Feature flag tested. |

---

### Phase E — Dependency Pinning

| Field | Detail |
|---|---|
| **OBJECTIVE** | Create reproducible build environment |
| **WHY NOW** | Blocks CI/CD and reproducible deployment |
| **DEPENDENCIES** | None |
| **FILES AFFECTED** | NEW: `requirements.txt`, `requirements-dev.txt` |
| **RISK** | Low |
| **ACCEPTANCE CRITERIA** | `pip install -r requirements.txt` succeeds from clean venv. `pip freeze` matches expected versions. |
| **DEFINITION OF DONE** | Both requirements files exist. CI can use them. |

---

### Phase F — Real Data & GIS Acquisition

| Field | Detail |
|---|---|
| **OBJECTIVE** | Download and process real GIS raster assets |
| **WHY NOW** | Required for honest inundation modeling |
| **DEPENDENCIES** | Phase D (model paths must be clean before adding real data) |
| **FILES AFFECTED** | NEW: `scripts/download_dem.py`, `scripts/process_hand.py`, `geospatial/dem/`, `geospatial/landcover/`, `geospatial/population/` |
| **DATABASE IMPACT** | None |
| **API IMPACT** | None initially (data processing offline) |
| **ML IMPACT** | Enables terrain-aware model features |
| **RISK** | Low — additive, offline processing |
| **ACCEPTANCE CRITERIA** | 1. FABDEM raster clipped to basin. 2. HAND raster computed. 3. Land cover classified. |
| **DEFINITION OF DONE** | GIS assets present and validated. |

---

### Phase G — Database Migration

| Field | Detail |
|---|---|
| **OBJECTIVE** | Introduce Alembic. Prepare PostgreSQL path. |
| **WHY NOW** | Foundation for production deployment |
| **DEPENDENCIES** | Phase E (dependency pinning must include alembic, psycopg2) |
| **FILES AFFECTED** | `services/notifications/db/connection.py`, `services/ingestion/imd_aws_repository.py`, NEW: `alembic/`, `infra/docker/docker-compose.yml` |
| **DATABASE IMPACT** | Schema formalized with migrations |
| **RISK** | Medium — database changes are inherently risky. Mitigate with backups. |
| **ROLLBACK PLAN** | Keep SQLite as fallback via DATABASE_URL env var |
| **ACCEPTANCE CRITERIA** | 1. Alembic migration creates schema. 2. SQLite still works with env var. 3. PostgreSQL works in Docker. |
| **DEFINITION OF DONE** | Both database backends functional. |

---

### Phase H — API Architecture (Router Decomposition)

| Field | Detail |
|---|---|
| **OBJECTIVE** | Extract routers from monolithic main.py |
| **WHY NOW** | Reduces merge conflicts, improves maintainability |
| **DEPENDENCIES** | Phase G (database abstraction should be done first) |
| **FILES AFFECTED** | `apps/api/main.py`, NEW: `apps/api/routers/*.py` |
| **API IMPACT** | Zero — all routes preserved exactly |
| **RISK** | Medium — routing errors possible. Mitigate with existing API tests. |
| **ROLLBACK PLAN** | Revert to single main.py |
| **ACCEPTANCE CRITERIA** | All existing API tests pass with identical results. |
| **DEFINITION OF DONE** | main.py < 500 lines. All routes in routers. |

---

### Phase I — Real-Time & Event Bus Improvements

| Field | Detail |
|---|---|
| **OBJECTIVE** | Add schema validation, retry, dead-letter to event bus |
| **DEPENDENCIES** | Phase H |
| **FILES AFFECTED** | `services/events/event_bus.py`, `services/events/dispatcher.py` |
| **RISK** | Low — internal improvements, no API change |
| **ACCEPTANCE CRITERIA** | Event bus tests pass. Dead-letter events logged. |

---

### Phase J — Frontend Quality

| Field | Detail |
|---|---|
| **OBJECTIVE** | Add error boundaries, routing, basic tests |
| **DEPENDENCIES** | Phase H (API stability) |
| **FILES AFFECTED** | `apps/web/src/App.tsx`, `apps/web/src/views/*`, NEW: `apps/web/vitest.config.ts`, `apps/web/src/**/*.test.tsx` |
| **RISK** | Low — additive |
| **ACCEPTANCE CRITERIA** | Error boundaries present. At least 5 component tests pass. |

---

### Phase K — Testing & Observability

| Field | Detail |
|---|---|
| **OBJECTIVE** | Add metric consistency tests, structured logging, basic metrics endpoint |
| **DEPENDENCIES** | Phase J |
| **FILES AFFECTED** | NEW: `tests/test_metric_contract.py`, logging configuration |
| **ACCEPTANCE CRITERIA** | Metric contract test passes. Structured logs emitted. |

---

### Phase L — CI/CD & Deployment

| Field | Detail |
|---|---|
| **OBJECTIVE** | Create CI pipeline with quality gates |
| **DEPENDENCIES** | Phase K |
| **FILES AFFECTED** | NEW: `.github/workflows/ci.yml`, `infra/docker/docker-compose.yml` |
| **ACCEPTANCE CRITERIA** | CI runs on push. All gates pass on main branch. |

---

### Phase M — Final SIH Validation

| Field | Detail |
|---|---|
| **OBJECTIVE** | End-to-end system validation for SIH technical review |
| **DEPENDENCIES** | All previous phases |
| **ACCEPTANCE CRITERIA** | 1. All security tests pass. 2. All scientific claims match code. 3. Demo runs without errors. 4. Documentation is accurate. |

---

## 35. File-Level Change Plan

### Phase A (Security)

| Action | File |
|---|---|
| MODIFY | `apps/api/main.py` — Remove default passwords (L2103-2106), remove fallback auth (L2117-2120) |
| MODIFY | `services/notifications/security.py` — Remove default HMAC key (L20) |
| MODIFY | `ml/rainfall/deep/inference.py` — Add `weights_only=True` (L63) |
| MODIFY | `tests/test_convlstm_checkpoint.py` — Add `weights_only=True` (L19) |
| MODIFY | `.env.example` — Add required credential variables |

### Phase C (Scientific Claims)

| Action | File |
|---|---|
| MODIFY | `README.md` — Fix metric table, architecture labels |
| MODIFY | `model_registry/model_catalog.json` — Reconcile metrics |
| MODIFY | `ml/streamflow/discharge_models.py` — Fix provenance label (L111) |
| MODIFY | `ml/inundation/hydraulic_surrogate.py` — Fix model version name (L26), remove hardcoded metrics (L121-122) |
| MODIFY | `apps/api/main.py` — Fix FORECAST_RUNS metadata (L108), fix analytical source_id (L427) |

### Phase D (ML Paths)

| Action | File |
|---|---|
| MODIFY | `ml/rainfall/deep/inference.py` — Add validation logging |
| MODIFY | `apps/api/main.py` — Add feature flag for model selection |
| CREATE | `ml/evaluation/convlstm_shadow_report.json` — Shadow comparison results |

### Phase E (Dependencies)

| Action | File |
|---|---|
| CREATE | `requirements.txt` — Pinned Python dependencies |
| CREATE | `requirements-dev.txt` — Test/dev dependencies |

### Phase G (Database)

| Action | File |
|---|---|
| CREATE | `alembic.ini` — Alembic configuration |
| CREATE | `alembic/env.py` — Migration environment |
| CREATE | `alembic/versions/001_initial.py` — Initial schema migration |
| MODIFY | `services/notifications/db/connection.py` — Add PostgreSQL driver support |
| MODIFY | `infra/docker/docker-compose.yml` — Add PostgreSQL service |

### Phase H (API)

| Action | File |
|---|---|
| CREATE | `apps/api/routers/health.py` |
| CREATE | `apps/api/routers/rainfall.py` |
| CREATE | `apps/api/routers/hydrology.py` |
| CREATE | `apps/api/routers/inundation.py` |
| CREATE | `apps/api/routers/alerts.py` |
| CREATE | `apps/api/routers/admin.py` |
| CREATE | `apps/api/routers/notifications.py` |
| CREATE | `apps/api/routers/replay.py` |
| MODIFY | `apps/api/main.py` — Include routers, remove extracted routes |

---

## 36. Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation | Rollback |
|---|---|---|---|---|---|
| R01 | Removing default credentials breaks demo scripts | High | Medium | Document new credential setup in README. Provide `.env.demo` | Revert auth changes |
| R02 | ConvLSTM produces worse metrics than analytical | Medium | High | Keep analytical as fallback. Feature flag. | `RAINFALL_MODEL=analytical` |
| R03 | PostgreSQL migration loses data | Low | High | Full SQLite backup before migration. Dual-write period. | Revert to SQLite |
| R04 | Router decomposition breaks existing routes | Medium | Medium | Run full API test suite after each router extraction. | Revert to single main.py |
| R05 | GIS data download fails (network/license) | Medium | Medium | Track metadata only. Process rasters offline. | Use existing proxy terrain |
| R06 | IMD data access never granted | High | High | Maintain simulation mode. Document as external dependency. | Continue with simulation |
| R07 | torch.load(weights_only=True) fails with existing checkpoint | Low | Medium | Re-export checkpoint separating config from weights. | Revert to unsafe load |
| R08 | SIH reviewer finds remaining claim inconsistency | Medium | High | Automated metric consistency test. README review. | Immediate text fix |
| R09 | Demo scenario breaks during migration | Low | Critical | **NEVER modify demo data without full replay test.** | Preserve demo branch |

---

## 37. Rollback Strategy

### General Principle

For all major changes:

```
OBSERVE -> SHADOW -> COMPARE -> VALIDATE -> SWITCH -> MONITOR -> ROLLBACK (if needed)
```

### Specific Strategies

| Change | Rollback Method |
|---|---|
| **Security (Phase A)** | Git revert on `main.py` + `security.py` |
| **ML model switch** | Feature flag `RAINFALL_MODEL=analytical` in env |
| **Database migration** | `DATABASE_URL=sqlite:///data/jaldrishti_notifications.db` env var |
| **Router decomposition** | Git revert, restore monolithic `main.py` |
| **Dependency pinning** | Remove `requirements.txt` constraint |

### Demo Preservation

**DEMO-MAHANADI-STORM-01 must remain runnable at all times.** Before any phase that could affect demo:

1. Run full demo scenario test
2. Record expected output
3. After changes, re-run and diff against expected output
4. If diff exceeds tolerance, rollback before proceeding

---

## 38. Definition of Done

### Per-Phase Completion Criteria

| Criterion | Required |
|---|---|
| All existing tests pass | Yes |
| No new security vulnerabilities introduced | Yes |
| API response schema unchanged (unless explicitly planned) | Yes |
| Demo scenario runs without error | Yes |
| Documentation updated for changes made | Yes |
| Rollback tested | Yes (for Medium+ risk changes) |

### Final Project Completion Criteria

| Criterion | Verification Method |
|---|---|
| Zero P0 security findings | Automated security test suite + manual review |
| All external claims match implementation | `test_model_honesty.py` + README audit |
| ConvLSTM validated with documented metrics | Hindcast evaluation report |
| All models correctly labeled | Model catalog review |
| Demo runs end-to-end | Full scenario replay |
| Dependencies pinned | `pip install` from clean environment |
| CI pipeline active | GitHub Actions green on main branch |

---

## 39. Final SIH26071 Readiness Roadmap

### Readiness Scoring

| Dimension | Current | After Phase A (Security) | After Phase C (Claims) | After Full Roadmap |
|---|---|---|---|---|
| **Security** | 3/10 | 8/10 | 8/10 | 9/10 |
| **Scientific Integrity** | 4/10 | 4/10 | 8/10 | 9/10 |
| **ML Production Correctness** | 5/10 | 5/10 | 6/10 | 8/10 |
| **Data Validity** | 4/10 | 4/10 | 5/10 | 7/10 |
| **Reliability** | 6/10 | 6/10 | 6/10 | 8/10 |
| **Real-Time Correctness** | 5/10 | 5/10 | 5/10 | 7/10 |
| **Deployment Maturity** | 3/10 | 3/10 | 3/10 | 7/10 |
| **UX/Frontend** | 6/10 | 6/10 | 6/10 | 7/10 |
| **Documentation Accuracy** | 3/10 | 4/10 | 8/10 | 9/10 |
| **Overall SIH Readiness** | **4.3/10** | **5.0/10** | **6.1/10** | **7.9/10** |

### What the Scores Mean

- **Current (4.3/10):** Strong implementation quality but vulnerable to any security or scientific integrity review. Demo works but claims are inconsistent.
- **After Phase A (5.0/10):** Security vulnerabilities eliminated. System no longer has trivially exploitable credentials.
- **After Phase C (6.1/10):** All external claims match internal implementation. README is truthful. Metrics are verified.
- **After Full Roadmap (7.9/10):** Production-ready prototype with honest claims, validated ML models, proper database, CI/CD, and reproducible deployment. Remaining 2.1 points depend on external factors (real data access, IMD authorization, SAR validation data).

### Final Acceptance Matrix

| SIH Requirement | Current Status | Target Status | Phase | Verification |
|---|---|---|---|---|
| Multi-source data integration | Code exists, simulation mode | Live when access granted | E, F, K | Provider connection test |
| Rainfall nowcasting 0-6h | ConvLSTM + analytical surrogate | ConvLSTM validated + production | D | Hindcast evaluation |
| Flood/discharge forecasting 6-72h | Analytical model (mislabeled LSTM) | Analytical model (correctly labeled) + XGBoost candidate | C, D | Model registry audit |
| Inundation prediction | Analytical proxy (mislabeled UNet) | Analytical + RF shadow | C, D | Shadow comparison |
| Uncertainty quantification | Implemented (analytical parametric) | Same, correctly documented | C | API response validation |
| Impact assessment | Implemented | Same | — | API test |
| Alerting with human review | Implemented with safety gates | Same, enhanced stale-data handling | — | Alert test suite |
| Decision support dashboard | 16-view React UI | Same + error boundaries | J | Manual + automated |
| Historical replay | 11-stage deterministic replay | Same, preserved through migration | All | Demo test |
| Security | **FAILING** — hardcoded credentials | Proper auth + secrets | A, B | Security test suite |
| Data provenance | Implemented | Same, labels corrected | C | Model honesty tests |
| Pilot: Mahanadi Delta | Configured | Same | — | Basin config review |

---

> **This document is the authoritative repair roadmap for JALDRISHTI AI (SIH26071).**  
> **No implementation shall begin without explicit approval of this plan.**  
> **The next engineering phase will execute these phases in order, with phase-gate reviews at each transition.**

---

*Document generated from forensic audit reconciliation against repository state as of 2026-09-01.*  
*All findings verified against actual source code, not inferred from documentation.*
