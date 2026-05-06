-- ============================================
-- PaveX Database Schema
-- PostgreSQL 16 + PostGIS
-- Day 10 — Database Setup
-- ============================================

-- Enable PostGIS extension for geospatial operations
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- HAZARD EVENTS TABLE
-- Stores all detected road hazards with geospatial data
-- ============================================

CREATE TABLE IF NOT EXISTS hazard_events (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Hazard classification
    hazard_type VARCHAR(50) NOT NULL CHECK (hazard_type IN ('pothole', 'speed_hump')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    
    -- Detection metrics
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    bbox_area_pct FLOAT NOT NULL CHECK (bbox_area_pct >= 0 AND bbox_area_pct <= 100),
    
    -- Location data (both formats for flexibility)
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    location GEOMETRY(Point, 4326) NOT NULL,
    
    -- Decision output
    speed_recommendation INTEGER NOT NULL CHECK (speed_recommendation >= 0),
    
    -- Metadata
    video_source VARCHAR(255) NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================
-- GEOSPATIAL INDEX
-- Optimizes proximity queries using GiST
-- ============================================

CREATE INDEX idx_hazard_location
ON hazard_events
USING GIST (location);

-- ============================================
-- ADDITIONAL INDEXES
-- Performance optimization for common queries
-- ============================================

-- Index for filtering by hazard type
CREATE INDEX idx_hazard_type
ON hazard_events (hazard_type);

-- Index for filtering by severity
CREATE INDEX idx_hazard_severity
ON hazard_events (severity);

-- Index for time-based queries
CREATE INDEX idx_captured_at
ON hazard_events (captured_at DESC);

-- Composite index for type + time queries
CREATE INDEX idx_hazard_type_time
ON hazard_events (hazard_type, captured_at DESC);

-- ============================================
-- TRIGGER: Auto-sync geometry from lat/lon
-- Ensures location geometry stays in sync
-- ============================================

CREATE OR REPLACE FUNCTION sync_location_geometry()
RETURNS TRIGGER AS $$
BEGIN
    NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_location
BEFORE INSERT OR UPDATE ON hazard_events
FOR EACH ROW
EXECUTE FUNCTION sync_location_geometry();

-- ============================================
-- COMMENTS
-- Documentation for future developers
-- ============================================

COMMENT ON TABLE hazard_events IS 'Stores all detected road hazards with geospatial data';
COMMENT ON COLUMN hazard_events.id IS 'Unique identifier for each hazard event';
COMMENT ON COLUMN hazard_events.hazard_type IS 'Type of hazard: pothole or speed_hump';
COMMENT ON COLUMN hazard_events.severity IS 'Risk severity: low, medium, or high';
COMMENT ON COLUMN hazard_events.confidence IS 'YOLO detection confidence (0-1)';
COMMENT ON COLUMN hazard_events.bbox_area_pct IS 'Bounding box area as percentage of frame (0-100)';
COMMENT ON COLUMN hazard_events.latitude IS 'GPS latitude coordinate';
COMMENT ON COLUMN hazard_events.longitude IS 'GPS longitude coordinate';
COMMENT ON COLUMN hazard_events.location IS 'PostGIS Point geometry for geospatial queries (SRID 4326)';
COMMENT ON COLUMN hazard_events.speed_recommendation IS 'Recommended safe speed in km/h';
COMMENT ON COLUMN hazard_events.video_source IS 'Camera or video stream identifier';
COMMENT ON COLUMN hazard_events.captured_at IS 'Timestamp when hazard was detected';

-- ============================================
-- VERIFICATION QUERIES
-- Run these to verify setup
-- ============================================

-- Verify PostGIS is enabled
-- SELECT PostGIS_Version();

-- Verify table structure
-- \d hazard_events

-- Test geospatial query (example)
-- SELECT id, hazard_type, ST_AsText(location)
-- FROM hazard_events
-- WHERE ST_DWithin(
--     location::geography,
--     ST_SetSRID(ST_MakePoint(77.5946, 12.9716), 4326)::geography,
--     1000
-- );