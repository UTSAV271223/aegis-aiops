-- Aegis AIOps Core Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$ BEGIN
    CREATE TYPE incident_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE incident_status AS ENUM (
        'DETECTED', 
        'ANALYZING', 
        'SELF_HEALING', 
        'RESOLVED', 
        'CRITICAL_HUMAN_REQUIRED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    container_name VARCHAR(255) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    severity incident_severity NOT NULL DEFAULT 'MEDIUM',
    raw_log TEXT,
    llm_diagnosis TEXT,
    recommended_fix TEXT,
    action_taken VARCHAR(255),
    retry_count INT DEFAULT 0,
    status incident_status NOT NULL DEFAULT 'DETECTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS container_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    container_name VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'RUNNING',
    cpu_usage_pct NUMERIC(5, 2) DEFAULT 0.00,
    memory_usage_mb NUMERIC(8, 2) DEFAULT 0.00,
    last_ping TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_container_health_name ON container_health(container_name);

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_incidents_modtime ON incidents;
CREATE TRIGGER update_incidents_modtime
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();