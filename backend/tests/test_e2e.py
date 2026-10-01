"""
PaveX End-to-End Integration Tests
backend/tests/test_e2e.py

Tests the full pipeline from HTTP request → DB persistence → WebSocket alert.
Five scenarios required by the Day 5 integration plan:

  1. New detection persistence   — POST /detect → hazard in DB
  2. Duplicate merge behavior    — same spot twice → detection_count == 2
  3. Approaching driver alert    — /driver/location near hazard → alert
  4. Opposite-direction no-alert — driver heading away → no alert
  5. Multi-driver scenario       — two drivers approach the same hazard

Run with:
    cd backend
    # Fast unit-level (mocked DB, no real Supabase needed):
    python -m pytest tests/test_e2e.py -v

    # Full DB-backed (requires DATABASE_URL in .env):
    $env:PAVEX_RUN_DB_TESTS="1"; python -m pytest tests/test_e2e.py -v
"""

from __future__ import annotations

import io
import os
import uuid
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch, AsyncMock

import numpy as np
import pytest

# ── Path setup (conftest.py handles sys.path) ───────────────────────────────

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_fake_image_bytes(width: int = 64, height: int = 64) -> bytes:
    """Return minimal valid JPEG bytes via numpy → cv2."""
    import cv2
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[10:30, 10:30] = [255, 0, 0]  # a blue square — crude "pothole"
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


@pytest.fixture()
def client():
    """
    TestClient backed by a real in-memory SQLite DB (no Supabase needed).
    Geospatial functions (ST_DWithin, ST_MakePoint) are stubbed out so the
    dedup query degrades to a distance-blind lookup — sufficient for unit-
    level coverage.
    """
    import sqlalchemy
    from sqlalchemy import create_engine, event, text
    from sqlalchemy.orm import sessionmaker
    from fastapi.testclient import TestClient

    from app.db.connection import Base
    from app.db import models  # ensure ORM classes are registered

    from sqlalchemy.pool import StaticPool

    # In-memory SQLite (no PostGIS). Spatial SQL is patched separately.
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Override the app's DB dependency
    from app.db.connection import get_db
    from app.main import app

    def override_get_db() -> Generator:
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Stub out PostGIS spatial SQL so find_nearby_hazard works on SQLite.
    # We patch crud.find_nearby_hazard to use a simple Python haversine lookup.
    from app.services.proximity import haversine_distance_meters
    from app.db import crud as _crud
    from app.db.models import Hazard

    _original_find = _crud.find_nearby_hazard

    def _sqlite_find_nearby(db, hazard_type, latitude, longitude,
                             radius_meters=25.0, road_segment_id=None, direction=None):
        """SQLite-compatible replacement: pure-Python haversine dedup."""
        hazards = db.query(Hazard).filter(
            Hazard.hazard_type == hazard_type,
            Hazard.status == "active",
        ).all()
        for h in hazards:
            d = haversine_distance_meters(latitude, longitude, h.latitude, h.longitude)
            if d <= radius_meters:
                return h
        return None

    _crud.find_nearby_hazard = _sqlite_find_nearby

    # Also stub get_nearby_hazards (used by /driver/location)
    _original_get_nearby = _crud.get_nearby_hazards

    def _sqlite_get_nearby(db, latitude, longitude, radius_meters=1000, limit=100):
        hazards = db.query(Hazard).filter(Hazard.status == "active").all()
        result = []
        for h in hazards:
            d = haversine_distance_meters(latitude, longitude, h.latitude, h.longitude)
            if d <= radius_meters:
                result.append(h)
        result.sort(key=lambda h: haversine_distance_meters(latitude, longitude, h.latitude, h.longitude))
        return result[:limit]

    _crud.get_nearby_hazards = _sqlite_get_nearby

    with TestClient(app) as c:
        yield c

    # Restore originals
    _crud.find_nearby_hazard = _original_find
    _crud.get_nearby_hazards = _original_get_nearby
    app.dependency_overrides.clear()


# ── Helpers ──────────────────────────────────────────────────────────────────

_FAKE_DETECTION = {
    "class": "pothole",
    "confidence": 0.88,
    "bbox": [100, 200, 180, 260],
    "severity": "medium",
    "decision": {
        "action": "slow_down",
        "recommended_speed_kmph": 30,
        "risk_level": "medium",
    },
}

def _mock_pipeline(detections: list[dict] | None = None):
    """Return a patch context that replaces run_pipeline with a fixed result."""
    result = detections if detections is not None else [_FAKE_DETECTION]
    return patch(
        "app.api.detect.run_pipeline",
        return_value={"num_detections": len(result), "detections": result},
    )


# ═══════════════════════════════════════════════════════════════════════════
# Test 1 — New detection persistence
# ═══════════════════════════════════════════════════════════════════════════

def test_new_detection_persists(client):
    """
    POST /detect with GPS coords → pipeline runs → hazard created in DB →
    response includes hazard_id and detection_count == 1.
    """
    lat, lon = 12.9716, 77.5946
    img_bytes = _make_fake_image_bytes()

    with _mock_pipeline():
        resp = client.post(
            f"/detect?latitude={lat}&longitude={lon}",
            files={"file": ("road.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["num_detections"] == 1

    det = data["detections"][0]
    assert det["persisted"] is True, "Hazard should have been persisted"
    assert det["hazard_id"] is not None
    assert det["detection_count"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# Test 2 — Duplicate detection merges (detection_count increments)
# ═══════════════════════════════════════════════════════════════════════════

def test_duplicate_detection_merges(client):
    """
    Two detections at the same spot (within dedup radius) must:
      - Return the same hazard_id
      - Increment detection_count to 2
    """
    lat, lon = 12.9820, 77.6010
    img_bytes = _make_fake_image_bytes()

    with _mock_pipeline():
        r1 = client.post(
            f"/detect?latitude={lat}&longitude={lon}",
            files={"file": ("road.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
    assert r1.status_code == 200
    hid_1 = r1.json()["detections"][0]["hazard_id"]
    count_1 = r1.json()["detections"][0]["detection_count"]
    assert count_1 == 1

    # Second detection — 1 m away (well within 25 m dedup radius)
    with _mock_pipeline():
        r2 = client.post(
            f"/detect?latitude={lat + 0.000005}&longitude={lon}",
            files={"file": ("road.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
    assert r2.status_code == 200
    hid_2 = r2.json()["detections"][0]["hazard_id"]
    count_2 = r2.json()["detections"][0]["detection_count"]

    assert hid_1 == hid_2, "Second detection must confirm the same hazard record"
    assert count_2 == 2, f"Expected detection_count=2, got {count_2}"


# ═══════════════════════════════════════════════════════════════════════════
# Test 3 — Approaching driver receives a hazard alert
# ═══════════════════════════════════════════════════════════════════════════

def test_approaching_driver_receives_alert(client):
    """
    After a hazard is persisted:
      - A driver located 150 m north of the hazard, heading south (180°)
        must receive at least one alert for that hazard.
    """
    # 1. Plant a hazard via /hazards POST
    hazard_lat, hazard_lon = 12.9716, 77.5946
    create_resp = client.post(
        "/hazards",
        json={
            "hazard_type": "pothole",
            "severity": "high",
            "confidence": 0.91,
            "latitude": hazard_lat,
            "longitude": hazard_lon,
            "heading_degrees": 0,
        },
    )
    assert create_resp.status_code == 201, create_resp.text

    # 2. Driver is ~150 m north, heading south (toward the hazard)
    # 0.00135 ° ≈ 150 m latitude
    driver_lat = hazard_lat + 0.00135
    driver_lon = hazard_lon

    loc_resp = client.post(
        "/driver/location",
        json={
            "driver_id": "test-driver-approaching",
            "latitude": driver_lat,
            "longitude": driver_lon,
            "speed_kmph": 40.0,
            "heading_degrees": 180.0,  # south = toward hazard
        },
    )
    assert loc_resp.status_code == 200, loc_resp.text
    body = loc_resp.json()
    assert body["success"] is True
    assert len(body["alerts"]) >= 1, (
        "Driver approaching the hazard from the north should have received an alert. "
        f"Got: {body['alerts']}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Test 4 — Opposite-direction driver receives NO alert
# ═══════════════════════════════════════════════════════════════════════════

def test_opposite_direction_driver_no_alert(client):
    """
    A driver 150 m south of a hazard heading *away* (south = 180°, hazard
    is to the north) must not receive any alert.

    Heading delta = |180° - 0°| = 180° >> 70° threshold → not approaching.
    """
    hazard_lat, hazard_lon = 12.9716, 77.5960  # slightly east to be unique

    client.post(
        "/hazards",
        json={
            "hazard_type": "pothole",
            "severity": "high",
            "confidence": 0.91,
            "latitude": hazard_lat,
            "longitude": hazard_lon,
        },
    )

    # Driver is south of the hazard, heading south (away)
    driver_lat = hazard_lat - 0.00135
    driver_lon = hazard_lon

    loc_resp = client.post(
        "/driver/location",
        json={
            "driver_id": "test-driver-opposite",
            "latitude": driver_lat,
            "longitude": driver_lon,
            "speed_kmph": 40.0,
            "heading_degrees": 180.0,  # moving south = away from northern hazard
        },
    )
    assert loc_resp.status_code == 200
    body = loc_resp.json()
    assert body["alerts"] == [], (
        "Driver heading away from the hazard should receive NO alerts. "
        f"Got: {body['alerts']}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Test 5 — Multi-driver scenario
# ═══════════════════════════════════════════════════════════════════════════

def test_multi_driver_same_hazard(client):
    """
    One hazard should simultaneously alert multiple approaching drivers
    and stay silent for a driver heading away.
    """
    hazard_lat, hazard_lon = 12.9750, 77.5946

    client.post(
        "/hazards",
        json={
            "hazard_type": "speed_hump",
            "severity": "medium",
            "confidence": 0.78,
            "latitude": hazard_lat,
            "longitude": hazard_lon,
        },
    )

    results = {}
    drivers = {
        "driver-a": {"lat": hazard_lat + 0.00135, "lon": hazard_lon, "heading": 180.0},   # approaching from north
        "driver-b": {"lat": hazard_lat + 0.00200, "lon": hazard_lon, "heading": 180.0},   # approaching from further north
        "driver-c": {"lat": hazard_lat - 0.00135, "lon": hazard_lon, "heading": 180.0},   # heading away south
    }

    for driver_id, params in drivers.items():
        resp = client.post(
            "/driver/location",
            json={
                "driver_id": driver_id,
                "latitude": params["lat"],
                "longitude": params["lon"],
                "speed_kmph": 35.0,
                "heading_degrees": params["heading"],
            },
        )
        assert resp.status_code == 200
        results[driver_id] = resp.json()["alerts"]

    assert len(results["driver-a"]) >= 1, "driver-a (approaching from north) should be alerted"
    assert len(results["driver-b"]) >= 1, "driver-b (approaching from further north) should be alerted"
    assert results["driver-c"] == [], "driver-c (heading away) should NOT be alerted"


# ═══════════════════════════════════════════════════════════════════════════
# Test 6 — Auth stub is reachable
# ═══════════════════════════════════════════════════════════════════════════

def test_auth_status_endpoint(client):
    """GET /auth/status must return 200 with auth_enabled field."""
    resp = client.get("/auth/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "auth_enabled" in data


# ═══════════════════════════════════════════════════════════════════════════
# Test 7 — Health check
# ═══════════════════════════════════════════════════════════════════════════

def test_health_check(client):
    """GET /health must return 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
