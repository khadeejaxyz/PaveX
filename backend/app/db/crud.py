from sqlalchemy.orm import Session
from sqlalchemy import and_
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_SetSRID, ST_MakePoint
from datetime import datetime, timedelta
from typing import Optional, List

from app.db.models import HazardEvent, HazardType, SeverityLevel


# Deduplication parameters
DEDUP_RADIUS_METERS = 8  # 8 meters radius
DEDUP_TIME_WINDOW_SECONDS = 5  # 5 seconds window


def create_hazard(
    db: Session,
    hazard_type: str,
    severity: str,
    confidence: float,
    bbox_area_pct: float,
    latitude: float,
    longitude: float,
    speed_recommendation: Optional[int],
    video_source: str,
    captured_at: datetime
) -> Optional[HazardEvent]:
    """
    Create a new hazard event with deduplication.
    
    Returns None if duplicate exists, otherwise returns the created HazardEvent.
    """
    # Check for duplicates
    time_threshold = captured_at - timedelta(seconds=DEDUP_TIME_WINDOW_SECONDS)
    
    # Create point geometry for the new detection
    new_point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    
    # Query for duplicates: same type, nearby location, recent time
    duplicate = db.query(HazardEvent).filter(
        and_(
            HazardEvent.hazard_type == hazard_type,
            HazardEvent.captured_at >= time_threshold,
            ST_DWithin(
                HazardEvent.location.cast(Geography),
                new_point.cast(Geography),
                DEDUP_RADIUS_METERS,
            )
        )
    ).first()
    
    # If duplicate exists, return None
    if duplicate:
        return None
    
    # Create new hazard event
    hazard = HazardEvent(
        hazard_type=HazardType(hazard_type),
        severity=SeverityLevel(severity),
        confidence=confidence,
        bbox_area_pct=bbox_area_pct,
        latitude=latitude,
        longitude=longitude,
        location=f"SRID=4326;POINT({longitude} {latitude})",
        speed_recommendation=speed_recommendation,
        video_source=video_source,
        captured_at=captured_at
    )
    
    db.add(hazard)
    db.commit()
    db.refresh(hazard)
    
    return hazard


def get_all_hazards(db: Session) -> List[HazardEvent]:
    """
    Retrieve all hazard events from the database.
    """
    return db.query(HazardEvent).all()


def get_nearby_hazards(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000
) -> List[HazardEvent]:
    """
    Retrieve hazards within a specified radius of a location.
    
    Args:
        db: Database session
        latitude: Center point latitude
        longitude: Center point longitude
        radius_meters: Search radius in meters (default: 1000m = 1km)
    
    Returns:
        List of HazardEvent objects within the radius
    """
    point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    
    nearby = db.query(HazardEvent).filter(
        ST_DWithin(
            HazardEvent.location.cast(Geography),
            point.cast(Geography),
            radius_meters,
        )
    ).all()
    
    return nearby
