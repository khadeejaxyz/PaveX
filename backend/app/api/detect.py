"""
PaveX – Detection API Router
backend/app/api/detect.py

Exposes a POST /detect endpoint that accepts an uploaded image,
runs the full pipeline, persists each detection as a hazard
(creating or confirming via radius-based dedup), and returns
structured detection results.
"""

from __future__ import annotations

import logging
import time

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from sqlalchemy.orm import Session

from app.core.pipeline import run_pipeline
from app.services.location import enrich_detections_with_location
from app.db.connection import get_db
from app.db.models import HazardType
from app.db import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detect", tags=["Detection"])

# Classes the pipeline can emit that don't map 1:1 to HazardType get bucketed here
_KNOWN_HAZARD_TYPES = {t.value for t in HazardType}


def _safe_hazard_type(raw_class: str) -> str:
    normalized = (raw_class or "").strip().lower().replace(" ", "_")
    return normalized if normalized in _KNOWN_HAZARD_TYPES else "other"


@router.post(
    "",
    summary="Detect road hazards in an uploaded image",
    response_description="Detection results with metadata",
    status_code=status.HTTP_200_OK,
)
async def detect(
    file: UploadFile = File(..., description="Image file (JPEG, PNG, BMP, etc.)"),
    latitude: float | None = None,
    longitude: float | None = None,
    heading_degrees: float | None = None,
    db: Session = Depends(get_db),
):
    """
    Accepts an image upload, runs the full PaveX pipeline, persists any
    detections that carry GPS coordinates, and returns results.

    Response format:
    {
        "num_detections": int,
        "detections": [
            { ..., "hazard_id": str | None, "detection_count": int | None, "persisted": bool }
        ],
        "processing_time_ms": float
    }
    """

    # ------------------------------------------------------------------
    # 1. Validate file type
    # ------------------------------------------------------------------
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an image.",
        )

    # ------------------------------------------------------------------
    # 2. Read file bytes
    # ------------------------------------------------------------------
    try:
        raw_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read uploaded file.",
        ) from exc

    # ------------------------------------------------------------------
    # 3. Decode image
    # ------------------------------------------------------------------
    try:
        np_buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    except Exception as exc:
        logger.warning("Image decoding error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode the uploaded file as an image.",
        ) from exc

    if frame is None:
        logger.warning("Invalid image content: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unsupported image format.",
        )

    # ------------------------------------------------------------------
    # 4. Run full pipeline with timing
    # ------------------------------------------------------------------
    try:
        start_time = time.perf_counter()

        result = run_pipeline(frame)

        if "detections" in result:
            result["detections"] = enrich_detections_with_location(
                result["detections"],
                latitude=latitude,
                longitude=longitude,
            )

        processing_time_ms = (time.perf_counter() - start_time) * 1000

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during pipeline processing.",
        ) from exc

    # ------------------------------------------------------------------
    # 5. Persist each detection (create or confirm existing hazard)
    # ------------------------------------------------------------------
    for det in result.get("detections", []):
        det_lat = det.get("latitude", latitude)
        det_lon = det.get("longitude", longitude)

        if det_lat is None or det_lon is None:
            # No GPS = nothing to persist geographically. Still return the
            # detection so the live feed can render it, just flag it.
            det["persisted"] = False
            det["hazard_id"] = None
            det["detection_count"] = None
            logger.warning(
                "Detection of %s skipped persistence: missing GPS coordinates",
                det.get("class"),
            )
            continue

        decision = det.get("decision", {}) or {}

        try:
            hazard = crud.create_or_confirm_hazard(
                db=db,
                hazard_type=_safe_hazard_type(det.get("class")),
                severity=det.get("severity", "low"),
                confidence=float(det.get("confidence", 0.0)),
                latitude=float(det_lat),
                longitude=float(det_lon),
                heading_degrees=heading_degrees,
                recommended_speed_kmph=decision.get("recommended_speed_kmph"),
                risk_level=decision.get("risk_level"),
                metadata={
                    "bbox": det.get("bbox"),
                    "action": decision.get("action"),
                    "source_filename": file.filename,
                },
            )
            det["persisted"] = True
            det["hazard_id"] = str(hazard.id)
            det["detection_count"] = hazard.detection_count
        except Exception as exc:
            # A DB hiccup shouldn't take down the whole detection response —
            # log it, surface it on the detection, keep going.
            logger.error("Failed to persist detection: %s", exc, exc_info=True)
            det["persisted"] = False
            det["hazard_id"] = None
            det["detection_count"] = None
            det["persistence_error"] = str(exc)

    # ------------------------------------------------------------------
    # 6. Attach processing time and return
    # ------------------------------------------------------------------
    result["processing_time_ms"] = round(processing_time_ms, 2)

    return result
