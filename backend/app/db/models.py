from sqlalchemy import Column, String, Float, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import uuid
import enum
from datetime import datetime

from app.db.connection import Base


class HazardType(str, enum.Enum):
    POTHOLE = "pothole"
    SPEED_HUMP = "speed_hump"


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HazardEvent(Base):
    __tablename__ = "hazard_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hazard_type = Column(
        Enum(
            HazardType,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            native_enum=False,
        ),
        nullable=False,
    )
    severity = Column(
        Enum(
            SeverityLevel,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            native_enum=False,
        ),
        nullable=False,
    )
    confidence = Column(Float, nullable=False)
    bbox_area_pct = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    speed_recommendation = Column(Integer, nullable=True)
    video_source = Column(String, nullable=False)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<HazardEvent(id={self.id}, type={self.hazard_type}, severity={self.severity})>"
