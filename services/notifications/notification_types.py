"""
Domain Models and Type Definitions for Public Notifications in JALDRISHTI AI.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class NotificationChannel(str, Enum):
    SMS = "SMS"
    PUSH = "PUSH"
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"

class NotificationDeliveryStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class NotificationSeverityPolicy(str, Enum):
    INFO = "INFO"
    WATCH = "WATCH"
    WARNING = "WARNING"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"
    RESOLVED = "RESOLVED"

class GeofenceMatch(str, Enum):
    IN_AREA = "IN_AREA"
    NEAR_AREA = "NEAR_AREA"
    OUTSIDE_AREA = "OUTSIDE_AREA"

class UserPreferences(BaseModel):
    sms_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True
    email_enabled: bool = False
    minimum_severity: NotificationSeverityPolicy = NotificationSeverityPolicy.WATCH
    preferred_language: str = "en" # "en", "hi", "or"
    quiet_mode: bool = False
    quiet_hours_start_utc: Optional[int] = None # e.g. 22 (10pm)
    quiet_hours_end_utc: Optional[int] = None # e.g. 6 (6am)

class LocationSubscription(BaseModel):
    subscription_id: str = Field(default_factory=lambda: f"SUB-{uuid.uuid4().hex[:6]}")
    user_id: str
    label: str = "HOME" # "HOME", "WORK", "FAMILY", "FARMLAND"
    locality_name: str
    latitude: float
    longitude: float
    geohash: Optional[str] = None
    radius_km: float = Field(default=10.0, ge=1.0, le=100.0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    preferences: Optional[UserPreferences] = None

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"USR-{uuid.uuid4().hex[:8]}")
    phone_number: str
    phone_hash: str
    phone_verified: bool = False
    preferred_language: str = "en"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "ACTIVE"
    fcm_device_tokens: List[str] = Field(default_factory=list)
    subscriptions: List[LocationSubscription] = Field(default_factory=list)
    global_preferences: UserPreferences = Field(default_factory=UserPreferences)

class NotificationProvenance(BaseModel):
    alert_id: str
    risk_state_id: Optional[str] = None
    forecast_run_id: str
    inundation_run_id: Optional[str] = None
    impact_run_id: Optional[str] = None
    user_region: str
    channel: NotificationChannel
    template_id: str
    data_state: str = "OBSERVED_CWC"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class NotificationMessage(BaseModel):
    notification_id: str = Field(default_factory=lambda: f"NOTIF-{uuid.uuid4().hex[:8]}")
    user_id: str
    subscription_id: Optional[str] = None
    channel: NotificationChannel
    severity: NotificationSeverityPolicy
    title: str
    body: str
    recipient: str # phone or device token or user_id
    locality: str
    deeplink_url: str = "/public-portal"
    issued_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    provenance: NotificationProvenance
    status: NotificationDeliveryStatus = NotificationDeliveryStatus.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    provider_name: Optional[str] = None
    provider_message_id: Optional[str] = None
    delivery_latency_ms: Optional[float] = None
    error_message: Optional[str] = None

class DeliveryRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: f"DELIV-{uuid.uuid4().hex[:6]}")
    notification_id: str
    user_id: str
    channel: NotificationChannel
    provider: str
    status: NotificationDeliveryStatus
    attempt_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    response_code: Optional[int] = None
    latency_ms: float = 0.0
    error_details: Optional[str] = None
