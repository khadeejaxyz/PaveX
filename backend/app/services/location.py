"""
Location Service for PaveX
Provides real-time geographic coordinates for hazard detections.
"""

import time
import math
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(
        self,
        mode: str = "external",  # changed default
        base_lat: float = 12.9716,
        base_lon: float = 77.5946,
        movement_speed: float = 0.0001,
        movement_pattern: str = "linear"
    ):
        self.mode = mode
        self.base_lat = base_lat
        self.base_lon = base_lon
        self.movement_speed = movement_speed
        self.movement_pattern = movement_pattern

        self.start_time = time.time()
        self.current_lat = base_lat
        self.current_lon = base_lon

        self._frame_location_cache: Optional[Tuple[float, float, float]] = None
        self._cache_timestamp: float = 0

        logger.info(f"LocationService initialized in {mode} mode")

    def get_current_location(
        self,
        use_cache: bool = True,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Tuple[float, float]:

        # ✅ PRIORITY: external coordinates (from frontend)
        if latitude is not None and longitude is not None:
            self.current_lat = latitude
            self.current_lon = longitude
            return latitude, longitude

        # fallback (if nothing passed)
        return self.current_lat, self.current_lon

    def enrich_detection(
        self,
        detection: Dict[str, Any],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        use_cached_location: bool = True
    ) -> Dict[str, Any]:

        lat, lon = self.get_current_location(
            use_cache=use_cached_location,
            latitude=latitude,
            longitude=longitude
        )

        detection['latitude'] = lat
        detection['longitude'] = lon
        detection['location_mode'] = self.mode
        detection['location_timestamp'] = datetime.utcnow().isoformat()

        return detection

    def enrich_detections(
        self,
        detections: list[Dict[str, Any]],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> list[Dict[str, Any]]:

        if not detections:
            return detections

        lat, lon = self.get_current_location(
            latitude=latitude,
            longitude=longitude
        )

        location_timestamp = datetime.utcnow().isoformat()

        enriched = []
        for detection in detections:
            detection['latitude'] = lat
            detection['longitude'] = lon
            detection['location_mode'] = self.mode
            detection['location_timestamp'] = location_timestamp
            enriched.append(detection)

        return enriched


# Global service instance
_location_service: Optional[LocationService] = None


def get_location_service() -> LocationService:
    global _location_service

    if _location_service is None:
        _location_service = LocationService()

    return _location_service


def initialize_location_service(
    mode: str = "external",
    base_lat: float = 12.9716,
    base_lon: float = 77.5946,
    **kwargs
) -> LocationService:

    global _location_service

    _location_service = LocationService(
        mode=mode,
        base_lat=base_lat,
        base_lon=base_lon,
        **kwargs
    )

    return _location_service


def get_current_coordinates(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Tuple[float, float]:

    service = get_location_service()
    return service.get_current_location(latitude=latitude, longitude=longitude)


def enrich_detection_with_location(
    detection: Dict[str, Any],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:

    service = get_location_service()
    return service.enrich_detection(
        detection,
        latitude=latitude,
        longitude=longitude
    )


def enrich_detections_with_location(
    detections: list[Dict[str, Any]],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> list[Dict[str, Any]]:

    service = get_location_service()
    return service.enrich_detections(
        detections,
        latitude=latitude,
        longitude=longitude
    )