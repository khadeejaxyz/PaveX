-- PaveX Hazard Database Schema
-- Run this in the Supabase SQL editor (or via psql against your Postgres instance).

-- Enable PostGIS for geospatial queries (nearby-hazard search, dedup radius checks)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum types -----------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE hazard_type_enum AS ENUM ('pothole', 'speed_hump', 'crack', 'debris', 'other');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE severity_enum AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE hazard_status_enum AS ENUM ('active', 'unconfirmed', 'resolved', 'archived');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE road_direction_enum AS ENUM ('north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest', 'unknown');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- Core hazards table -----------------------------------------------------

CREATE TABLE IF NOT EXISTS hazards (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- What
    hazard_type         hazard_type_enum NOT NULL,
    severity            severity_enum NOT NULL,
    confidence          REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    risk_level          TEXT,
    recommended_speed_kmph REAL,

    -- Where
    latitude            DOUBLE PRECISION NOT NULL,
    longitude           DOUBLE PRECISION NOT NULL,
    geom                GEOGRAPHY(Point, 4326) GENERATED ALWAYS AS (
                            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
                        ) STORED,
    road_name           TEXT,
    road_segment_id     TEXT,
    direction           road_direction_enum DEFAULT 'unknown',

    -- Lifecycle (Day 2 dedup depends on these)
    first_detected_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_detected_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    detection_count     INTEGER NOT NULL DEFAULT 1,
    status              hazard_status_enum NOT NULL DEFAULT 'active',

    -- Raw detection metadata (bbox, image ref, model version, etc.)
    metadata            JSONB DEFAULT '{}'::jsonb,
    severity_timeline   JSONB DEFAULT '[]'::jsonb,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE hazards ADD COLUMN IF NOT EXISTS road_name TEXT;
ALTER TABLE hazards ADD COLUMN IF NOT EXISTS road_segment_id TEXT;
ALTER TABLE hazards ADD COLUMN IF NOT EXISTS direction road_direction_enum DEFAULT 'unknown';
ALTER TABLE hazards ADD COLUMN IF NOT EXISTS severity_timeline JSONB DEFAULT '[]'::jsonb;

-- Indexes -----------------------------------------------------------

-- Fast nearby-hazard lookups (used by Day 2 dedup + Day 3 proximity engine)
CREATE INDEX IF NOT EXISTS idx_hazards_geom ON hazards USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_hazards_status ON hazards (status);
CREATE INDEX IF NOT EXISTS idx_hazards_severity ON hazards (severity);
CREATE INDEX IF NOT EXISTS idx_hazards_road_segment ON hazards (road_segment_id);

-- Auto-update updated_at ---------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_hazards_updated_at ON hazards;
CREATE TRIGGER trg_hazards_updated_at
    BEFORE UPDATE ON hazards
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
