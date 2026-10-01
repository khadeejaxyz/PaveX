"""
Hazard API endpoints for PaveX system.

Provides endpoints to:
- Retrieve all hazard records
- Query hazards by geospatial proximity
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.db import crud
from app.db.models import Hazard, HazardStatus, RoadDirection


router = APIRouter(
    prefix="/hazards",
    tags=["Hazards"]
)

stats_router = APIRouter(tags=["Statistics"])


class HazardCreate(BaseModel):
    hazard_type: str | None = None
    hazardType: str | None = None
    severity: str
    confidence: float
    latitude: float | None = None
    longitude: float | None = None
    detected_at: datetime | None = None
    detectedAt: datetime | None = None
    road_name: str | None = None
    road_segment_id: str | None = None
    direction: str | None = None
    heading_degrees: float | None = None
    metadata: dict | None = None


def enum_value(value):
    return value.value if hasattr(value, "value") else value


def serialize_hazard(hazard):
    """
    Convert SQLAlchemy hazard model to JSON-serializable dictionary.
    
    Args:
        hazard: SQLAlchemy ORM hazard object
        
    Returns:
        Dictionary with all hazard fields, with UUIDs converted to strings
    """
    data = hazard.to_dict()

    # Backward-compatible aliases consumed by the current frontend.
    data["speed_recommendation"] = hazard.recommended_speed_kmph
    data["captured_at"] = hazard.last_detected_at.isoformat() if hazard.last_detected_at else None
    data["detectedAt"] = data["captured_at"]
    data["hazardType"] = data["hazard_type"]
    data["report_count"] = hazard.detection_count
    data["verified"] = enum_value(hazard.status) != "unconfirmed"

    return data


def _bbox_area_pct(metadata: dict | None) -> float:
    bbox = (metadata or {}).get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return 0.0

    try:
        x1, y1, x2, y2 = (float(value) for value in bbox)
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        return min(100.0, max(0.0, area / (640.0 * 640.0) * 100.0))
    except (TypeError, ValueError):
        return 0.0


def _db_severity(severity: str) -> str:
    return severity if severity in {"low", "medium", "high", "critical"} else "low"


def _safe_hazard_type(hazard_type: str) -> str:
    normalized = (hazard_type or "").strip().lower().replace(" ", "_")
    return normalized if normalized in {"pothole", "speed_hump", "crack", "debris", "other"} else "other"


def _safe_direction(direction: str) -> RoadDirection:
    try:
        return RoadDirection(direction)
    except ValueError:
        return RoadDirection.UNKNOWN


@router.get("")
def get_all_hazards(
    db: Session = Depends(get_db)
):
    """
    Retrieve all hazard events from the database.
    """
    hazards = crud.get_all_hazards(db)
    # Convert ORM objects to dictionaries
    return [serialize_hazard(hazard) for hazard in hazards]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_hazard(
    payload: HazardCreate,
    db: Session = Depends(get_db),
):
    """
    Persist a frontend-reported hazard detection.
    """
    hazard_type = payload.hazard_type or payload.hazardType
    if not hazard_type:
        raise HTTPException(status_code=400, detail="hazard_type is required")

    detected_at = payload.detected_at or payload.detectedAt or datetime.now(timezone.utc)
    metadata = payload.metadata or {}

    hazard = crud.create_or_confirm_hazard(
        db=db,
        hazard_type=_safe_hazard_type(hazard_type),
        severity=_db_severity(payload.severity),
        confidence=payload.confidence,
        latitude=payload.latitude if payload.latitude is not None else 12.9716,
        longitude=payload.longitude if payload.longitude is not None else 77.5946,
        recommended_speed_kmph=metadata.get("recommended_speed_kmph") or metadata.get("speed_recommendation") or 30,
        risk_level=metadata.get("risk_level"),
        road_name=payload.road_name,
        road_segment_id=payload.road_segment_id,
        direction=payload.direction,
        heading_degrees=payload.heading_degrees,
        metadata={
            **metadata,
            "bbox_area_pct": _bbox_area_pct(metadata),
            "source": "frontend",
            "detected_at": detected_at.isoformat(),
        },
    )

    return {"hazard": serialize_hazard(hazard)}


@router.get("/nearby")
def get_nearby_hazards(
    latitude: float = Query(..., description="Center point latitude"),
    longitude: float = Query(..., description="Center point longitude"),
    radius_meters: float = Query(1000, description="Search radius in meters"),
    db: Session = Depends(get_db)
):
    """
    Retrieve hazards within a specified radius of a location.
    """
    hazards = crud.get_nearby_hazards(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters
    )
    # Convert ORM objects to dictionaries
    return [serialize_hazard(hazard) for hazard in hazards]


@router.get("/{hazard_id}")
def get_hazard(
    hazard_id: UUID,
    db: Session = Depends(get_db),
):
    hazard = db.get(Hazard, hazard_id)
    if hazard is None:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return {"hazard": serialize_hazard(hazard)}


@router.patch("/{hazard_id}")
def update_hazard(
    hazard_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
):
    hazard = db.get(Hazard, hazard_id)
    if hazard is None:
        raise HTTPException(status_code=404, detail="Hazard not found")

    allowed_fields = {
        "hazard_type",
        "hazardType",
        "severity",
        "confidence",
        "latitude",
        "longitude",
        "recommended_speed_kmph",
        "speed_recommendation",
        "risk_level",
        "road_name",
        "road_segment_id",
        "direction",
        "status",
    }
    for key, value in payload.items():
        if key not in allowed_fields:
            continue

        if key == "hazardType":
            key = "hazard_type"
        elif key == "speed_recommendation":
            key = "recommended_speed_kmph"

        if key == "hazard_type":
            value = _safe_hazard_type(value)
        elif key == "severity":
            value = _db_severity(value)
        elif key == "status":
            value = HazardStatus(value)
        elif key == "direction":
            value = _safe_direction(value)

        setattr(hazard, key, value)

    db.commit()
    db.refresh(hazard)
    return {"hazard": serialize_hazard(hazard)}


@router.delete("/{hazard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hazard(
    hazard_id: UUID,
    db: Session = Depends(get_db),
):
    hazard = db.get(Hazard, hazard_id)
    if hazard is None:
        raise HTTPException(status_code=404, detail="Hazard not found")

    db.delete(hazard)
    db.commit()
    return None


@stats_router.get("/statistics")
def get_statistics_endpoint(db: Session = Depends(get_db)):
    return get_statistics(db)


def get_statistics(db: Session) -> dict:
    hazards = crud.get_all_hazards(db)
    today = datetime.now(timezone.utc).date()

    severity_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    hazard_type_distribution = {
        "pothole": 0,
        "speed_hump": 0,
        "crack": 0,
        "debris": 0,
        "other": 0,
    }
    detections_by_hour = [0] * 24
    confidence_total = 0.0
    today_count = 0

    for hazard in hazards:
        severity = enum_value(hazard.severity)
        hazard_type = enum_value(hazard.hazard_type)
        captured_at = hazard.last_detected_at

        if severity in severity_distribution:
            severity_distribution[severity] += 1
        if hazard_type in hazard_type_distribution:
            hazard_type_distribution[hazard_type] += 1

        confidence_total += hazard.confidence or 0.0

        if captured_at:
            if captured_at.tzinfo is None:
                captured_at = captured_at.replace(tzinfo=timezone.utc)
            detections_by_hour[captured_at.hour] += 1
            if captured_at.date() == today:
                today_count += 1

    total = len(hazards)

    return {
        "success": True,
        "statistics": {
            "totalDetections": total,
            "todayDetections": today_count,
            "averageConfidence": confidence_total / total if total else 0,
            "severityDistribution": severity_distribution,
            "hazardTypeDistribution": hazard_type_distribution,
            "detectionsByHour": detections_by_hour,
        },
    }
