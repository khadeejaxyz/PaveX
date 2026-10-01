"""
PaveX Database Models
SQLAlchemy ORM mapping for the `hazards` table.

Note: `geom` is a DB-generated column (see schema.sql) — it is intentionally
NOT mapped here as a writable field. Spatial queries (nearby search, dedup)
go through raw SQL in crud.py against `geom` directly, which is simpler and
faster than fighting the ORM over a generated PostGIS column.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, Enum as SAEnum, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.connection import Base


class HazardType(str, enum.Enum):
    POTHOLE = "pothole"
    SPEED_HUMP = "speed_hump"
    CRACK = "crack"
    DEBRIS = "debris"
    OTHER = "other"


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HazardStatus(str, enum.Enum):
    ACTIVE = "active"
    UNCONFIRMED = "unconfirmed"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class RoadDirection(str, enum.Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTHEAST = "northeast"
    NORTHWEST = "northwest"
    SOUTHEAST = "southeast"
    SOUTHWEST = "southwest"
    UNKNOWN = "unknown"


def _enum_values(enum_cls):
    return [item.value for item in enum_cls]


class Hazard(Base):
    __tablename__ = "hazards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What
    hazard_type = Column(
        SAEnum(HazardType, values_callable=_enum_values, name="hazard_type_enum", native_enum=False),
        nullable=False,
    )
    severity = Column(
        SAEnum(SeverityLevel, values_callable=_enum_values, name="severity_enum", native_enum=False),
        nullable=False,
    )
    confidence = Column(Float, nullable=False)
    risk_level = Column(String, nullable=True)
    recommended_speed_kmph = Column(Float, nullable=True)

    # Where
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    road_name = Column(String, nullable=True)
    road_segment_id = Column(String, nullable=True, index=True)
    direction = Column(
        SAEnum(RoadDirection, values_callable=_enum_values, name="road_direction_enum", native_enum=False),
        default=RoadDirection.UNKNOWN,
        nullable=False,
    )

    # Lifecycle
    first_detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    detection_count = Column(Integer, nullable=False, default=1)
    status = Column(
        SAEnum(HazardStatus, values_callable=_enum_values, name="hazard_status_enum", native_enum=False),
        default=HazardStatus.ACTIVE,
        nullable=False,
    )

    # Raw detection metadata: bbox, image ref, model version, etc.
    metadata_ = Column("metadata", JSON, default=dict)
    severity_timeline = Column(JSON, default=list)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Hazard(id={self.id}, type={self.hazard_type}, severity={self.severity}, count={self.detection_count})>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "hazard_type": self.hazard_type.value if self.hazard_type else None,
            "severity": self.severity.value if self.severity else None,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "recommended_speed_kmph": self.recommended_speed_kmph,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "road_name": self.road_name,
            "road_segment_id": self.road_segment_id,
            "direction": self.direction.value if self.direction else None,
            "first_detected_at": self.first_detected_at.isoformat() if self.first_detected_at else None,
            "last_detected_at": self.last_detected_at.isoformat() if self.last_detected_at else None,
            "detection_count": self.detection_count,
            "status": self.status.value if self.status else None,
            "metadata": self.metadata_ or {},
            "severity_timeline": self.severity_timeline or [],
        }
