"""
PaveX – Detection API Router
backend/app/api/detect.py

Exposes a POST /detect endpoint that accepts an uploaded image,
runs full pipeline, and returns structured detection results.
"""

from __future__ import annotations

import logging
import time

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, status

# ✅ FIX 1: Correct import
from app.core.pipeline import run_pipeline

# ✅ ADD: import location enrichment
from app.services.location import enrich_detections_with_location

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/detect", tags=["Detection"])

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "",
    summary="Detect road hazards in an uploaded image",
    response_description="Detection results with metadata",
    status_code=status.HTTP_200_OK,
)
async def detect(
    file: UploadFile = File(..., description="Image file (JPEG, PNG, BMP, etc.)"),
    latitude: float | None = None,   # ✅ ADD
    longitude: float | None = None,  # ✅ ADD
):
    """
    Accepts an image upload, runs full PaveX pipeline, and returns results.

    Response format:
    {
        "num_detections": int,
        "detections": [...],
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

        result = run_pipeline(frame)  # ✅ FIX 2: use result, not detections

        # ✅ ADD: attach location to detections
        if "detections" in result:
            result["detections"] = enrich_detections_with_location(
                result["detections"],
                latitude=latitude,
                longitude=longitude
            )

        processing_time_ms = (time.perf_counter() - start_time) * 1000

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during pipeline processing.",
        ) from exc

    # ------------------------------------------------------------------
    # 5. Attach processing time and return
    # ------------------------------------------------------------------
    result["processing_time_ms"] = round(processing_time_ms, 2)

    return result