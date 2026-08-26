-- ============================================================================
-- SMART-SHIELD v3.0 Database Schema
-- Database: PostgreSQL 14+ with TimescaleDB Extension (or standard PostgreSQL)
-- ============================================================================

-- Enable TimescaleDB extension if available
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 1. Persistent Targets Master Table
CREATE TABLE IF NOT EXISTS targets (
    target_id VARCHAR(32) PRIMARY KEY,
    first_detected TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_detected TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    classification VARCHAR(32) NOT NULL DEFAULT 'Unknown', -- 'Drone', 'Quadcopter', 'Fixed-Wing', 'Unknown'
    initial_distance_m FLOAT NOT NULL,
    max_threat_score FLOAT NOT NULL DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' -- 'ACTIVE', 'NEUTRALIZED', 'LOST', 'DISMISSED'
);

-- 2. Timeseries Target Kinematic Telemetry Table
CREATE TABLE IF NOT EXISTS target_telemetry (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_id VARCHAR(32) NOT NULL REFERENCES targets(target_id) ON DELETE CASCADE,
    x_pos_m FLOAT NOT NULL,
    y_pos_m FLOAT NOT NULL,
    z_pos_m FLOAT DEFAULT 0.0,
    distance_m FLOAT NOT NULL,
    azimuth_deg FLOAT NOT NULL,
    elevation_deg FLOAT DEFAULT 0.0,
    speed_ms FLOAT NOT NULL,
    heading_deg FLOAT DEFAULT 0.0,
    optical_confidence FLOAT NOT NULL,
    radar_snr FLOAT NOT NULL,
    threat_score FLOAT NOT NULL,
    threat_level VARCHAR(10) NOT NULL -- 'LOW', 'MEDIUM', 'HIGH'
);

-- Create optimized index for fast spatial-temporal queries
CREATE INDEX IF NOT EXISTS idx_telemetry_time_target ON target_telemetry (timestamp DESC, target_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_threat ON target_telemetry (threat_score DESC);

-- Convert to hypertable if TimescaleDB is loaded
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('target_telemetry', 'timestamp', if_not_exists => TRUE);
    END IF;
END $$;

-- 3. Cyber-Defence & RF Spectrum Incident Log Table
CREATE TABLE IF NOT EXISTS cyber_rf_events (
    event_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(32) NOT NULL, -- 'JAMMING_ATTEMPT', 'SIGNAL_SPOOFING', 'UNAUTHORIZED_C2', 'FREQ_ANOMALY'
    frequency_mhz FLOAT NOT NULL,
    rssi_dbm FLOAT NOT NULL,
    noise_floor_delta_db FLOAT NOT NULL,
    severity VARCHAR(10) NOT NULL DEFAULT 'WARNING', -- 'INFO', 'WARNING', 'CRITICAL'
    countermeasure_taken VARCHAR(64) DEFAULT NULL, -- 'CHANNEL_HOP_CH11', 'ANTENNA_HARDENING', 'ALERT_OPERATOR'
    resolved_at TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_rf_events_time ON cyber_rf_events (timestamp DESC);

-- 4. System Health & Hardware Audit Logs Table
CREATE TABLE IF NOT EXISTS system_audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subsystem VARCHAR(32) NOT NULL, -- 'ESP32', 'LD2450_RADAR', 'GIMBAL_PCA9685', 'AI_ENGINE', 'RF_MONITOR', 'OPERATOR'
    event_message TEXT NOT NULL,
    battery_voltage FLOAT DEFAULT 12.6,
    core_temp_c FLOAT DEFAULT 42.0,
    gimbal_pan_deg FLOAT DEFAULT 90.0,
    gimbal_tilt_deg FLOAT DEFAULT 45.0
);

CREATE INDEX IF NOT EXISTS idx_system_logs_time ON system_audit_logs (timestamp DESC);
