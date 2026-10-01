"""
Geographic matching and driver proximity logic for PaveX.

This module intentionally has no database dependency. API and CRUD layers call
these helpers to compute distances, approximate road segments, compare headings,
and decide whether a hazard is relevant to a moving driver.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

EARTH_RADIUS_METERS = 6_371_000
DEFAULT_DEDUP_RADIUS_METERS = 25.0

SEVERITY_WARNING_DISTANCE_METERS = {
    "low": 120.0,
    "medium": 220.0,
    "high": 360.0,
    "critical": 520.0,
}


@dataclass(frozen=True)
class DriverLocation:
    driver_id: str
    latitude: float
    longitude: float
    speed_kmph: float = 0.0
    heading_degrees: float | None = None
    accuracy_meters: float | None = None


def haversine_distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Return great-circle distance between two GPS points in meters."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return compass bearing from point A to point B in degrees."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def heading_delta_degrees(a: float, b: float) -> float:
    """Return smallest absolute angular difference between two headings."""
    return abs((a - b + 180) % 360 - 180)


def direction_from_heading(heading: float | None) -> str:
    if heading is None:
        return "unknown"

    headings = [
        ("north", 337.5, 360.0),
        ("north", 0.0, 22.5),
        ("northeast", 22.5, 67.5),
        ("east", 67.5, 112.5),
        ("southeast", 112.5, 157.5),
        ("south", 157.5, 202.5),
        ("southwest", 202.5, 247.5),
        ("west", 247.5, 292.5),
        ("northwest", 292.5, 337.5),
    ]
    normalized = heading % 360
    for name, start, end in headings:
        if start <= normalized < end:
            return name
    return "unknown"


def approximate_road_segment_id(latitude: float, longitude: float, heading: float | None = None) -> str:
    """
    Produce a stable local road-segment key without an external map-matching API.

    Coordinates are rounded to roughly 55m cells and paired with heading bucket.
    It is not a replacement for real road names, but it gives dedup/proximity
    deterministic same-road behavior while the app is offline/API-key-free.
    """
    lat_bucket = round(latitude, 4)
    lon_bucket = round(longitude, 4)
    direction = direction_from_heading(heading)
    return f"seg:{lat_bucket:.4f}:{lon_bucket:.4f}:{direction}"


def warning_distance_meters(severity: str, speed_kmph: float) -> float:
    """Dynamic warning radius combining severity zone and speed stopping cushion."""
    base = SEVERITY_WARNING_DISTANCE_METERS.get((severity or "low").lower(), 120.0)
    speed_cushion = max(0.0, speed_kmph) * 2.2
    return base + speed_cushion


def is_same_road(driver_segment_id: str | None, hazard_segment_id: str | None) -> bool:
    if not driver_segment_id or not hazard_segment_id:
        return True
    if driver_segment_id.startswith("seg:") or hazard_segment_id.startswith("seg:"):
        return True
    return driver_segment_id == hazard_segment_id


def is_driver_approaching_hazard(
    driver_latitude: float,
    driver_longitude: float,
    hazard_latitude: float,
    hazard_longitude: float,
    driver_heading_degrees: float | None,
    max_delta_degrees: float = 70.0,
) -> bool:
    """True when the hazard lies generally ahead of the driver's heading."""
    if driver_heading_degrees is None:
        return True

    target_bearing = bearing_degrees(
        driver_latitude,
        driver_longitude,
        hazard_latitude,
        hazard_longitude,
    )
    return heading_delta_degrees(driver_heading_degrees, target_bearing) <= max_delta_degrees


def hazard_alert_payload(hazard: Any, distance_meters: float, warning_radius_meters: float) -> dict[str, Any]:
    hazard_type = getattr(hazard, "hazard_type", None)
    severity = getattr(hazard, "severity", None)
    direction = getattr(hazard, "direction", None)
    hazard_type_value = hazard_type.value if hasattr(hazard_type, "value") else hazard_type
    severity_value = severity.value if hasattr(severity, "value") else severity
    direction_value = direction.value if hasattr(direction, "value") else direction

    speed = getattr(hazard, "recommended_speed_kmph", None)
    return {
        "id": str(getattr(hazard, "id")),
        "hazard_id": str(getattr(hazard, "id")),
        "hazard_type": hazard_type_value,
        "severity": severity_value,
        "latitude": getattr(hazard, "latitude"),
        "longitude": getattr(hazard, "longitude"),
        "location": {
            "latitude": getattr(hazard, "latitude"),
            "longitude": getattr(hazard, "longitude"),
        },
        "distance": round(distance_meters, 1),
        "warning_radius_meters": round(warning_radius_meters, 1),
        "recommended_speed_kmph": speed,
        "road_name": getattr(hazard, "road_name", None),
        "road_segment_id": getattr(hazard, "road_segment_id", None),
        "direction": direction_value,
        "message": (
            f"{str(severity_value).upper()} {str(hazard_type_value).replace('_', ' ')} "
            f"{round(distance_meters)}m ahead. Slow to {round(speed or 30)} km/h."
        ),
    }

