"""
Database-backed restart-survival check.

Run with:
    $env:PAVEX_RUN_DB_TESTS="1"; python -m pytest backend/tests/test_restart_survival.py
"""

import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="DATABASE_URL is required")
def test_hazard_persists_and_detection_count_increments_after_new_session():
    if os.environ.get("PAVEX_RUN_DB_TESTS") != "1":
        pytest.skip("set PAVEX_RUN_DB_TESTS=1 to exercise the real database")

    from app.db.connection import SessionLocal
    from app.db import crud

    lat = 12.9716 + (uuid.uuid4().int % 1000) / 10_000_000
    lon = 77.5946 + (uuid.uuid4().int % 1000) / 10_000_000

    first_session = SessionLocal()
    try:
        first = crud.create_or_confirm_hazard(
            first_session,
            hazard_type="pothole",
            severity="medium",
            confidence=0.82,
            latitude=lat,
            longitude=lon,
            heading_degrees=0,
        )
        hazard_id = str(first.id)
        assert first.detection_count == 1
    finally:
        first_session.close()

    second_session = SessionLocal()
    try:
        second = crud.create_or_confirm_hazard(
            second_session,
            hazard_type="pothole",
            severity="high",
            confidence=0.91,
            latitude=lat + 0.00001,
            longitude=lon + 0.00001,
            heading_degrees=0,
        )
        assert str(second.id) == hazard_id
        assert second.detection_count == 2
        assert second.severity.value == "high"
    finally:
        second_session.close()
