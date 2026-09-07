-- =========================================================================
-- JALDRISHTI AI — PostgreSQL + PostGIS Production Relational Schema
-- High-throughput, normalized spatial data model for disaster alerting
-- =========================================================================

-- Enable PostGIS geospatial extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Schema Migrations Ledger
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(32) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Citizens / Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    phone_hash VARCHAR(64) NOT NULL UNIQUE,
    phone_masked VARCHAR(16) NOT NULL,
    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    preferred_language VARCHAR(8) NOT NULL DEFAULT 'en' CHECK(preferred_language IN ('en', 'hi', 'or', 'bn', 'as', 'ml')),
    role VARCHAR(16) NOT NULL DEFAULT 'PUBLIC_USER' CHECK(role IN ('PUBLIC_USER', 'OPERATOR', 'ANALYST', 'ADMIN')),
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'SUSPENDED', 'DEACTIVATED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_phone_hash ON users(phone_hash);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- 3. OTP & Phone Verification State (Salted Hashes Only)
CREATE TABLE IF NOT EXISTS user_verifications (
    verification_id VARCHAR(36) PRIMARY KEY,
    phone_hash VARCHAR(64) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    hashed_otp VARCHAR(64) NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
    max_attempts INTEGER NOT NULL DEFAULT 3,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_verifications_phone_hash ON user_verifications(phone_hash);
CREATE INDEX IF NOT EXISTS idx_verifications_expires_at ON user_verifications(expires_at);

-- 4. Location Subscriptions Table with PostGIS Point Geometry
CREATE TABLE IF NOT EXISTS location_subscriptions (
    subscription_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    label VARCHAR(32) NOT NULL DEFAULT 'HOME' CHECK(label IN ('HOME', 'WORK', 'FAMILY', 'FARMLAND', 'OTHER')),
    locality_name VARCHAR(128) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK(latitude BETWEEN -90.0 AND 90.0),
    longitude DOUBLE PRECISION NOT NULL CHECK(longitude BETWEEN -180.0 AND 180.0),
    geom geometry(Point, 4326),
    geohash VARCHAR(12),
    radius_km DOUBLE PRECISION NOT NULL DEFAULT 10.0 CHECK(radius_km BETWEEN 1.0 AND 100.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON location_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_geohash ON location_subscriptions(geohash);
CREATE INDEX IF NOT EXISTS idx_subscriptions_geom ON location_subscriptions USING GIST(geom);

-- 5. User Notification Preferences
CREATE TABLE IF NOT EXISTS notification_preferences (
    preference_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    sms_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    minimum_severity VARCHAR(16) NOT NULL DEFAULT 'WATCH' CHECK(minimum_severity IN ('INFO', 'WATCH', 'WARNING', 'HIGH_RISK', 'CRITICAL', 'RESOLVED')),
    preferred_language VARCHAR(8) NOT NULL DEFAULT 'en',
    quiet_mode BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Device & Push Tokens
CREATE TABLE IF NOT EXISTS device_push_tokens (
    token_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    device_token TEXT NOT NULL UNIQUE,
    platform VARCHAR(16) NOT NULL DEFAULT 'WEB' CHECK(platform IN ('ANDROID', 'IOS', 'WEB')),
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'INVALID', 'EXPIRED')),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_tokens_user_id ON device_push_tokens(user_id);

-- 7. Notifications Log & Provenance
CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subscription_id VARCHAR(36) REFERENCES location_subscriptions(subscription_id) ON DELETE SET NULL,
    alert_id VARCHAR(64) NOT NULL,
    forecast_run_id VARCHAR(64) NOT NULL,
    risk_state_id VARCHAR(64),
    severity VARCHAR(16) NOT NULL,
    channel VARCHAR(16) NOT NULL CHECK(channel IN ('SMS', 'PUSH', 'IN_APP', 'EMAIL', 'CAP_BROADCAST')),
    title VARCHAR(160) NOT NULL,
    body TEXT NOT NULL,
    locality VARCHAR(128) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'QUEUED' CHECK(status IN ('QUEUED', 'SENT', 'DELIVERED', 'FAILED', 'SUPPRESSED')),
    deeplink_url VARCHAR(256),
    template_id VARCHAR(64) NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_alert_id ON notifications(alert_id);
CREATE INDEX IF NOT EXISTS idx_notifications_issued_at ON notifications(issued_at);

-- 8. Notification Deliveries Tracking
CREATE TABLE IF NOT EXISTS notification_deliveries (
    delivery_id VARCHAR(36) PRIMARY KEY,
    notification_id VARCHAR(36) NOT NULL REFERENCES notifications(notification_id) ON DELETE CASCADE,
    channel VARCHAR(16) NOT NULL,
    provider_name VARCHAR(64) NOT NULL,
    provider_message_id VARCHAR(128),
    status VARCHAR(16) NOT NULL CHECK(status IN ('QUEUED', 'SENT', 'DELIVERED', 'FAILED', 'SUPPRESSED')),
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    latency_ms DOUBLE PRECISION,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_deliveries_notification_id ON notification_deliveries(notification_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON notification_deliveries(status);

-- 9. Immutable Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    actor_id VARCHAR(64),
    actor_role VARCHAR(16),
    ip_address VARCHAR(45),
    target_resource VARCHAR(128),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);
