-- =========================================================================
-- JALDRISHTI AI — Public Citizen Notification Normalized Relational Schema
-- Fully compatible with SQLite (WAL mode) and PostgreSQL (PostGIS)
-- =========================================================================

-- 1. Schema Migrations Ledger
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(32) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Citizens / Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    phone_hash VARCHAR(64) NOT NULL UNIQUE,
    phone_masked VARCHAR(16) NOT NULL,
    phone_verified INTEGER NOT NULL DEFAULT 0 CHECK(phone_verified IN (0, 1)),
    preferred_language VARCHAR(8) NOT NULL DEFAULT 'en' CHECK(preferred_language IN ('en', 'hi', 'or', 'bn', 'as', 'ml')),
    role VARCHAR(16) NOT NULL DEFAULT 'PUBLIC_USER' CHECK(role IN ('PUBLIC_USER', 'OPERATOR', 'ANALYST', 'ADMIN')),
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'SUSPENDED', 'DEACTIVATED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_phone_hash ON users(phone_hash);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- 3. OTP & Phone Verification State (Salted Hashes Only, Zero Plaintext)
CREATE TABLE IF NOT EXISTS user_verifications (
    verification_id VARCHAR(36) PRIMARY KEY,
    phone_hash VARCHAR(64) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    hashed_otp VARCHAR(64) NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
    max_attempts INTEGER NOT NULL DEFAULT 3,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_verifications_phone_hash ON user_verifications(phone_hash);
CREATE INDEX IF NOT EXISTS idx_verifications_expires_at ON user_verifications(expires_at);

-- 4. Location Subscriptions Table
CREATE TABLE IF NOT EXISTS location_subscriptions (
    subscription_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    label VARCHAR(32) NOT NULL DEFAULT 'HOME' CHECK(label IN ('HOME', 'WORK', 'FAMILY', 'FARMLAND', 'OTHER')),
    locality_name VARCHAR(128) NOT NULL,
    latitude REAL NOT NULL CHECK(latitude BETWEEN -90.0 AND 90.0),
    longitude REAL NOT NULL CHECK(longitude BETWEEN -180.0 AND 180.0),
    geohash VARCHAR(12),
    radius_km REAL NOT NULL DEFAULT 10.0 CHECK(radius_km BETWEEN 1.0 AND 100.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON location_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_lat_lon ON location_subscriptions(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_subscriptions_geohash ON location_subscriptions(geohash);

-- 5. User Notification Preferences
CREATE TABLE IF NOT EXISTS notification_preferences (
    preference_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    sms_enabled INTEGER NOT NULL DEFAULT 1 CHECK(sms_enabled IN (0, 1)),
    push_enabled INTEGER NOT NULL DEFAULT 1 CHECK(push_enabled IN (0, 1)),
    in_app_enabled INTEGER NOT NULL DEFAULT 1 CHECK(in_app_enabled IN (0, 1)),
    email_enabled INTEGER NOT NULL DEFAULT 0 CHECK(email_enabled IN (0, 1)),
    minimum_severity VARCHAR(16) NOT NULL DEFAULT 'WATCH' CHECK(minimum_severity IN ('INFO', 'WATCH', 'WARNING', 'HIGH_RISK', 'CRITICAL', 'RESOLVED')),
    preferred_language VARCHAR(8) NOT NULL DEFAULT 'en',
    quiet_mode INTEGER NOT NULL DEFAULT 0 CHECK(quiet_mode IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 6. Device & Push Tokens
CREATE TABLE IF NOT EXISTS device_push_tokens (
    token_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    device_token TEXT NOT NULL UNIQUE,
    platform VARCHAR(16) NOT NULL DEFAULT 'WEB' CHECK(platform IN ('ANDROID', 'IOS', 'WEB')),
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'INVALID', 'EXPIRED')),
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_device_tokens_user_id ON device_push_tokens(user_id);

-- 7. Notifications Log & Provenance
CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    subscription_id VARCHAR(36),
    alert_id VARCHAR(64) NOT NULL,
    forecast_run_id VARCHAR(64) NOT NULL,
    risk_state_id VARCHAR(64),
    channel VARCHAR(16) NOT NULL CHECK(channel IN ('SMS', 'PUSH', 'IN_APP', 'EMAIL')),
    severity VARCHAR(16) NOT NULL CHECK(severity IN ('INFO', 'WATCH', 'WARNING', 'HIGH_RISK', 'CRITICAL', 'RESOLVED')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    recipient_masked VARCHAR(64) NOT NULL,
    locality VARCHAR(128) NOT NULL,
    template_id VARCHAR(64) NOT NULL,
    data_state VARCHAR(32) NOT NULL DEFAULT 'OBSERVED_CWC',
    region_id VARCHAR(32) NOT NULL DEFAULT 'MAHANADI_DELTA',
    fingerprint VARCHAR(32) NOT NULL,
    deeplink_url TEXT NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'QUEUED' CHECK(status IN ('QUEUED', 'PROCESSING', 'SENT', 'DELIVERED', 'FAILED', 'RETRYING', 'EXPIRED', 'CANCELLED')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    provider_name VARCHAR(64),
    provider_message_id VARCHAR(128),
    delivery_latency_ms REAL,
    error_message TEXT,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(subscription_id) REFERENCES location_subscriptions(subscription_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_alert_id ON notifications(alert_id);
CREATE INDEX IF NOT EXISTS idx_notifications_fingerprint ON notifications(fingerprint);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(issued_at);

-- 8. Delivery Attempts & Provider Receipts Ledger
CREATE TABLE IF NOT EXISTS notification_deliveries (
    delivery_id VARCHAR(36) PRIMARY KEY,
    notification_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    channel VARCHAR(16) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    response_code INTEGER,
    latency_ms REAL NOT NULL DEFAULT 0.0,
    error_details TEXT,
    attempt_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(notification_id) REFERENCES notifications(notification_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deliveries_notif_id ON notification_deliveries(notification_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON notification_deliveries(status);

-- 9. Security & Operational Audit Log
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(64) NOT NULL DEFAULT 'SYSTEM',
    actor_role VARCHAR(16) NOT NULL DEFAULT 'SYSTEM',
    ip_address VARCHAR(45),
    target_resource VARCHAR(64),
    action VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL CHECK(status IN ('SUCCESS', 'FAILURE', 'DENIED', 'BLOCKED')),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
