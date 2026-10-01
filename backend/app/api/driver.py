"""
Driver location API and proximity alert trigger.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.db import crud
from app.services.alerts import alert_manager
from app.services.location import store_driver_location
from app.services.proximity import (
    approximate_road_segment_id,
    hazard_alert_payload,
    haversine_distance_meters,
    is_driver_approaching_hazard,
    is_same_road,
    warning_distance_meters,
)


router = APIRouter(prefix="/driver", tags=["Driver"])


class DriverLocationPayload(BaseModel):
    driver_id: str = Field(default="default-driver")
    latitude: float
    longitude: float
    speed_kmph: float = 0.0
    heading_degrees: float | None = None
    accuracy_meters: float | None = None
    alert_radius_meters: float | None = None


@router.post("/location")
async def update_driver_location(
    payload: DriverLocationPayload,
    db: Session = Depends(get_db),
):
    """
    Store latest driver state and return/push currently relevant hazards.
    """
    location = store_driver_location(
        driver_id=payload.driver_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed_kmph=payload.speed_kmph,
        heading_degrees=payload.heading_degrees,
        accuracy_meters=payload.accuracy_meters,
    )

    max_radius = payload.alert_radius_meters or warning_distance_meters("critical", payload.speed_kmph)
    driver_segment = approximate_road_segment_id(
        payload.latitude,
        payload.longitude,
        payload.heading_degrees,
    )
    nearby = crud.get_nearby_hazards(
        db,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_meters=max_radius,
    )

    alerts = []
    for hazard in nearby:
        distance = haversine_distance_meters(
            payload.latitude,
            payload.longitude,
            hazard.latitude,
            hazard.longitude,
        )
        severity = hazard.severity.value if hasattr(hazard.severity, "value") else hazard.severity
        warning_radius = warning_distance_meters(severity, payload.speed_kmph)
        if distance > warning_radius:
            continue
        if not is_same_road(driver_segment, hazard.road_segment_id):
            continue
        if not is_driver_approaching_hazard(
            payload.latitude,
            payload.longitude,
            hazard.latitude,
            hazard.longitude,
            payload.heading_degrees,
        ):
            continue

        alerts.append(hazard_alert_payload(hazard, distance, warning_radius))

    for alert in alerts:
        await alert_manager.send_to_driver(payload.driver_id, "hazard_alert", alert)

    return {
        "success": True,
        "driver_id": payload.driver_id,
        "location": {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "speed_kmph": location.speed_kmph,
            "heading_degrees": location.heading_degrees,
            "accuracy_meters": location.accuracy_meters,
            "updated_at": location.updated_at,
            "road_segment_id": driver_segment,
        },
        "alerts": alerts,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

