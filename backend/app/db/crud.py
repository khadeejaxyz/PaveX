"""
PaveX Hazard CRUD

Note on dedup: spatial matching (ST_DWithin / ST_Distance) is done via raw
SQL against the DB-generated `geom` column, because that column isn't
writable through the ORM. This is deliberately simple — Day 2 will extend
`find_nearby_hazard` with road-segment + direction matching; for now it's
pure distance-based, which is enough to stop Day 1 from creating duplicate
rows every time the same pothole is detected again.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import Hazard, HazardType, SeverityLevel, HazardStatus, RoadDirection
from app.services.proximity import (
    DEFAULT_DEDUP_RADIUS_METERS,
    approximate_road_segment_id,
    direction_from_heading,
)

logger = logging.getLogger(__name__)

# Same physical pothole is assumed if a new detection of the same hazard_type
# lands within this radius of an existing ACTIVE hazard. Tune this later —
# the 5-day plan suggests 20-30m as a starting point; 25m is the midpoint.
DEDUP_RADIUS_METERS = DEFAULT_DEDUP_RADIUS_METERS


def _utc_now() -> datetime:
    """
    Always return a timezone-AWARE UTC datetime.

    FIX: datetime.utcnow() returns a naive datetime (no tzinfo). When that
    gets serialized to JSON, the resulting ISO string has no 'Z'/offset
    suffix — so the frontend's `new Date(timestamp)` incorrectly treats it
    as LOCAL time instead of UTC, silently shifting every timestamp by
    whatever the viewer's UTC offset is (e.g. -5:30 for IST). Using
    datetime.now(timezone.utc) instead means .isoformat() always includes
    the '+00:00' suffix, so the frontend parses it correctly with no
    workaround needed.
    """
    return datetime.now(timezone.utc)


def find_nearby_hazard(
    db: Session,
    hazard_type: str,
    latitude: float,
    longitude: float,
    radius_meters: float = DEDUP_RADIUS_METERS,
    road_segment_id: str | None = None,
    direction: str | None = None,
) -> Optional[Hazard]:
    """Find the closest active hazard of the same type within radius_meters, if any."""
    sql = text("""
        SELECT id FROM hazards
        WHERE hazard_type = :hazard_type
          AND status = 'active'
          AND (:road_segment_id IS NULL OR road_segment_id IS NULL OR road_segment_id = :road_segment_id)
          AND (:direction IS NULL OR direction = 'unknown' OR direction = :direction)
          AND ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius
              )
        ORDER BY ST_Distance(
            geom,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        ) ASC
        LIMIT 1
    """)
    row = db.execute(
        sql,
        {
            "hazard_type": hazard_type,
            "lon": longitude,
            "lat": latitude,
            "radius": radius_meters,
            "road_segment_id": road_segment_id,
            "direction": direction,
        },
    ).first()

    if not row:
        return None
    return db.query(Hazard).filter(Hazard.id == row.id).first()


def create_or_confirm_hazard(
    db: Session,
    hazard_type: str,
    severity: str,
    confidence: float,
    latitude: float,
    longitude: float,
    recommended_speed_kmph: Optional[float] = None,
    risk_level: Optional[str] = None,
    road_name: Optional[str] = None,
    road_segment_id: Optional[str] = None,
    direction: Optional[str] = None,
    heading_degrees: Optional[float] = None,
    metadata: Optional[dict] = None,
) -> Hazard:
    """
    Core Day 1 + Day 2 entry point: either creates a new hazard, or confirms
    (updates) an existing nearby one. Never silently drops a detection.
    """
    if direction is None:
        direction = direction_from_heading(heading_degrees)
    valid_directions = {item.value for item in RoadDirection}
    if direction not in valid_directions:
        direction = RoadDirection.UNKNOWN.value
    if road_segment_id is None:
        road_segment_id = approximate_road_segment_id(latitude, longitude, heading_degrees)

    existing = find_nearby_hazard(
        db,
        hazard_type,
        latitude,
        longitude,
        road_segment_id=road_segment_id,
        direction=direction,
    )

    if existing:
        existing.last_detected_at = _utc_now()
        existing.detection_count += 1
        # Confidence: keep the strongest signal seen so far
        existing.confidence = max(existing.confidence, confidence)
        # Severity: escalate if this detection is worse, never downgrade automatically
        severity_order = ["low", "medium", "high", "critical"]
        existing_sev = existing.severity.value if hasattr(existing.severity, "value") else existing.severity
        if severity_order.index(severity) > severity_order.index(existing_sev):
            existing.severity = SeverityLevel(severity)
            existing.recommended_speed_kmph = recommended_speed_kmph
            existing.risk_level = risk_level
        timeline = list(existing.severity_timeline or [])
        timeline.append(
            {
                "severity": severity,
                "confidence": confidence,
                "detected_at": existing.last_detected_at.isoformat(),
            }
        )
        existing.severity_timeline = timeline[-100:]
        if existing.road_segment_id is None:
            existing.road_segment_id = road_segment_id
        if getattr(existing.direction, "value", existing.direction) == "unknown":
            existing.direction = RoadDirection(direction)
        db.commit()
        db.refresh(existing)
        logger.info(f"Confirmed existing hazard {existing.id} (count={existing.detection_count})")
        return existing

    now = _utc_now()
    hazard = Hazard(
        hazard_type=HazardType(hazard_type),
        severity=SeverityLevel(severity),
        confidence=confidence,
        risk_level=risk_level,
        recommended_speed_kmph=recommended_speed_kmph,
        latitude=latitude,
        longitude=longitude,
        road_name=road_name,
        road_segment_id=road_segment_id,
        direction=RoadDirection(direction),
        status=HazardStatus.ACTIVE,
        detection_count=1,
        metadata_=metadata or {},
        severity_timeline=[
            {
                "severity": severity,
                "confidence": confidence,
                "detected_at": now.isoformat(),
            }
        ],
    )
    db.add(hazard)
    db.commit()
    db.refresh(hazard)
    logger.info(f"Created new hazard {hazard.id}")
    return hazard


def get_hazard_by_id(db: Session, hazard_id: str) -> Optional[Hazard]:
    return db.query(Hazard).filter(Hazard.id == hazard_id).first()


def get_all_hazards(db: Session, limit: int = 200, status: Optional[str] = None) -> List[Hazard]:
    query = db.query(Hazard)
    if status:
        query = query.filter(Hazard.status == status)
    return query.order_by(Hazard.last_detected_at.desc()).limit(limit).all()


def get_nearby_hazards(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000,
    limit: int = 100,
) -> List[Hazard]:
    sql = text("""
        SELECT id FROM hazards
        WHERE status = 'active'
          AND ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius
              )
        ORDER BY ST_Distance(
            geom,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        ) ASC
        LIMIT :limit
    """)
    rows = db.execute(
        sql, {"lon": longitude, "lat": latitude, "radius": radius_meters, "limit": limit}
    ).fetchall()

    if not rows:
        return []
    ids = [r.id for r in rows]
    hazards = db.query(Hazard).filter(Hazard.id.in_(ids)).all()
    # preserve distance order from the raw query
    order = {str(hid): i for i, hid in enumerate(ids)}
    hazards.sort(key=lambda h: order[str(h.id)])
    return hazards


def update_hazard_status(db: Session, hazard_id: str, status: str) -> Optional[Hazard]:
    hazard = get_hazard_by_id(db, hazard_id)
    if not hazard:
        return None
    hazard.status = HazardStatus(status)
    db.commit()
    db.refresh(hazard)
    return hazard


def delete_hazard(db: Session, hazard_id: str) -> bool:
    hazard = get_hazard_by_id(db, hazard_id)
    if not hazard:
        return False
    db.delete(hazard)
    db.commit()
    return True