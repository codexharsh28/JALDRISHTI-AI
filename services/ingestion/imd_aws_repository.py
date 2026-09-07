"""
IMD Automatic Weather Station (AWS) Database Repository.
Manages station catalogs, observation persistence, deduplication, and geospatial queries.
"""

import os
import sqlite3
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from services.notifications.db.connection import db_manager

class IMDAWSStation(BaseModel):
    call_sign: str
    station_id: str
    station_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    inside_basin: bool = False
    distance_to_basin_km: float = 0.0
    subbasin_id: Optional[str] = None
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "ACTIVE"

class IMDAWSObservation(BaseModel):
    observation_id: str
    call_sign: str
    station_id: str
    station_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: float
    longitude: float
    observation_time: datetime
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    air_temperature_c: Optional[float] = None
    dew_point_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    wind_speed_mps: Optional[float] = None
    min_temp_c: Optional[float] = None
    max_temp_c: Optional[float] = None
    rainfall_mm: Optional[float] = None  # None if absent from provider payload
    weather_code: Optional[str] = None
    nebulosity: Optional[float] = None
    feel_like_c: Optional[float] = None
    quality_state: str = "GOOD"
    data_state: str = "OBSERVED_IMD_AWS"
    provider: str = "IMD_AWS"
    is_observed_telemetry: bool = True
    inside_basin: bool = False
    distance_to_basin_km: float = 0.0
    subbasin_id: Optional[str] = None
    ingestion_run_id: str
    raw_payload_hash: str

class IMDAWSRepository:
    """Repository for storing and querying IMD AWS stations and observations."""

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Initializes tables for IMD AWS stations and observations."""
        with db_manager.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imd_aws_stations (
                    call_sign TEXT PRIMARY KEY,
                    station_id TEXT NOT NULL,
                    station_name TEXT NOT NULL,
                    district TEXT,
                    state TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    elevation_m REAL,
                    inside_basin INTEGER DEFAULT 0,
                    distance_to_basin_km REAL DEFAULT 0.0,
                    subbasin_id TEXT,
                    last_seen TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'ACTIVE'
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_imd_aws_stations_state ON imd_aws_stations(state);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_imd_aws_stations_basin ON imd_aws_stations(inside_basin);")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imd_aws_observations (
                    observation_id TEXT PRIMARY KEY,
                    call_sign TEXT NOT NULL,
                    station_id TEXT NOT NULL,
                    station_name TEXT NOT NULL,
                    district TEXT,
                    state TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    observation_time TIMESTAMP NOT NULL,
                    retrieved_at TIMESTAMP NOT NULL,
                    air_temperature_c REAL,
                    dew_point_c REAL,
                    relative_humidity_pct REAL,
                    pressure_hpa REAL,
                    wind_direction_deg REAL,
                    wind_speed_mps REAL,
                    min_temp_c REAL,
                    max_temp_c REAL,
                    rainfall_mm REAL,
                    weather_code TEXT,
                    nebulosity REAL,
                    feel_like_c REAL,
                    quality_state TEXT NOT NULL,
                    data_state TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    is_observed_telemetry INTEGER DEFAULT 1,
                    inside_basin INTEGER DEFAULT 0,
                    distance_to_basin_km REAL DEFAULT 0.0,
                    subbasin_id TEXT,
                    ingestion_run_id TEXT NOT NULL,
                    raw_payload_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (call_sign) REFERENCES imd_aws_stations(call_sign) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_imd_aws_obs_station ON imd_aws_observations(call_sign, observation_time);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_imd_aws_obs_time ON imd_aws_observations(observation_time);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_imd_aws_obs_basin ON imd_aws_observations(inside_basin);")

    @staticmethod
    def generate_observation_id(call_sign: str, obs_time_str: str) -> str:
        """Deterministic identity preventing duplicate ingestion of identical observations."""
        key = f"IMD_AWS_{call_sign}_{obs_time_str}"
        return f"OBS-{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}"

    def store_station(self, station: IMDAWSStation) -> None:
        """Upserts a station into the catalog."""
        with db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT INTO imd_aws_stations (
                    call_sign, station_id, station_name, district, state,
                    latitude, longitude, elevation_m, inside_basin,
                    distance_to_basin_km, subbasin_id, last_seen, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(call_sign) DO UPDATE SET
                    station_name=excluded.station_name,
                    district=excluded.district,
                    state=excluded.state,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    inside_basin=excluded.inside_basin,
                    distance_to_basin_km=excluded.distance_to_basin_km,
                    subbasin_id=excluded.subbasin_id,
                    last_seen=excluded.last_seen,
                    status=excluded.status
                """,
                (
                    station.call_sign,
                    station.station_id,
                    station.station_name,
                    station.district,
                    station.state,
                    station.latitude,
                    station.longitude,
                    station.elevation_m,
                    1 if station.inside_basin else 0,
                    station.distance_to_basin_km,
                    station.subbasin_id,
                    station.last_seen.isoformat(),
                    station.status
                )
            )

    def store_observation(self, obs: IMDAWSObservation) -> bool:
        """
        Stores an observation. Returns True if inserted as new, False if duplicate already existed.
        """
        # Ensure station exists first
        self.store_station(IMDAWSStation(
            call_sign=obs.call_sign,
            station_id=obs.station_id,
            station_name=obs.station_name,
            district=obs.district,
            state=obs.state,
            latitude=obs.latitude,
            longitude=obs.longitude,
            inside_basin=obs.inside_basin,
            distance_to_basin_km=obs.distance_to_basin_km,
            subbasin_id=obs.subbasin_id,
            last_seen=obs.retrieved_at
        ))

        with db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO imd_aws_observations (
                    observation_id, call_sign, station_id, station_name, district, state,
                    latitude, longitude, observation_time, retrieved_at,
                    air_temperature_c, dew_point_c, relative_humidity_pct, pressure_hpa,
                    wind_direction_deg, wind_speed_mps, min_temp_c, max_temp_c, rainfall_mm,
                    weather_code, nebulosity, feel_like_c, quality_state, data_state,
                    provider, is_observed_telemetry, inside_basin, distance_to_basin_km,
                    subbasin_id, ingestion_run_id, raw_payload_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    obs.observation_id,
                    obs.call_sign,
                    obs.station_id,
                    obs.station_name,
                    obs.district,
                    obs.state,
                    obs.latitude,
                    obs.longitude,
                    obs.observation_time.isoformat(),
                    obs.retrieved_at.isoformat(),
                    obs.air_temperature_c,
                    obs.dew_point_c,
                    obs.relative_humidity_pct,
                    obs.pressure_hpa,
                    obs.wind_direction_deg,
                    obs.wind_speed_mps,
                    obs.min_temp_c,
                    obs.max_temp_c,
                    obs.rainfall_mm,
                    obs.weather_code,
                    obs.nebulosity,
                    obs.feel_like_c,
                    obs.quality_state,
                    obs.data_state,
                    obs.provider,
                    1 if obs.is_observed_telemetry else 0,
                    1 if obs.inside_basin else 0,
                    obs.distance_to_basin_km,
                    obs.subbasin_id,
                    obs.ingestion_run_id,
                    obs.raw_payload_hash,
                    datetime.now(timezone.utc).isoformat()
                )
            )
            return cursor.rowcount > 0

    def get_station(self, call_sign: str) -> Optional[Dict[str, Any]]:
        """Retrieves a station by call sign."""
        with db_manager.transaction() as conn:
            row = conn.execute("SELECT * FROM imd_aws_stations WHERE call_sign = ?", (call_sign,)).fetchone()
            return dict(row) if row else None

    def list_stations(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        inside_basin_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Lists stations matching filter criteria."""
        query = "SELECT * FROM imd_aws_stations WHERE 1=1"
        params = []
        if state:
            query += " AND UPPER(state) = UPPER(?)"
            params.append(state)
        if district:
            query += " AND UPPER(district) = UPPER(?)"
            params.append(district)
        if inside_basin_only:
            query += " AND inside_basin = 1"
        query += " ORDER BY station_name ASC"

        with db_manager.transaction() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_latest_observation(self, call_sign: str) -> Optional[Dict[str, Any]]:
        """Returns the most recent observation for a specific station."""
        with db_manager.transaction() as conn:
            row = conn.execute(
                """
                SELECT * FROM imd_aws_observations
                WHERE call_sign = ?
                ORDER BY observation_time DESC LIMIT 1
                """,
                (call_sign,)
            ).fetchone()
            return dict(row) if row else None

    def list_latest_observations(self, inside_basin_only: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns the latest observation for each active station."""
        query = """
            SELECT o.* FROM imd_aws_observations o
            INNER JOIN (
                SELECT call_sign, MAX(observation_time) as max_time
                FROM imd_aws_observations
                GROUP BY call_sign
            ) latest ON o.call_sign = latest.call_sign AND o.observation_time = latest.max_time
            WHERE 1=1
        """
        params = []
        if inside_basin_only:
            query += " AND o.inside_basin = 1"
        query += " ORDER BY o.station_name ASC LIMIT ?"
        params.append(limit)

        with db_manager.transaction() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_station_count(self) -> int:
        """Returns total unique station count in catalog."""
        with db_manager.transaction() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM imd_aws_stations").fetchone()
            return row["cnt"] if row else 0

imd_aws_repository = IMDAWSRepository()
