"""
PaveX – Core Inference Module
backend/app/core/inference.py

Loads the YOLOv8 model once at startup and exposes a single
`run_inference` function that the API layer calls per request.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

import numpy as np
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.getenv("PAVEX_MODEL_PATH", BACKEND_DIR / "models" / "pavex_v1.pt"))
CONF_THRESHOLD = 0.5  # filter weak detections

# ---------------------------------------------------------------------------
# Class map
# ---------------------------------------------------------------------------

CLASS_NAMES: dict[int, str] = {
    0: "pothole",
    1: "speed_hump",
}

# ---------------------------------------------------------------------------
# Model – loaded ONCE at module import time
# ---------------------------------------------------------------------------

try:
    model: YOLO = YOLO(str(MODEL_PATH))
    logger.info("PaveX model loaded successfully from %s", MODEL_PATH)
except Exception as exc:
    logger.critical("Failed to load PaveX model: %s", exc, exc_info=True)
    raise RuntimeError(
        f"Could not load YOLOv8 model at '{MODEL_PATH}'. "
        "Ensure the file exists and ultralytics is installed. "
        "Set PAVEX_MODEL_PATH to override the default model location."
    ) from exc


# ---------------------------------------------------------------------------
# Inference function
# ---------------------------------------------------------------------------

def run_inference(frame: np.ndarray) -> List[dict]:
    """
    Run YOLOv8 inference on a single image frame.

    Args:
        frame (np.ndarray): OpenCV image (H, W, C)

    Returns:
        List[dict]: Detection results
    """

    if frame is None or frame.size == 0:
        logger.warning("Empty frame received – returning no detections")
        return []

    # Run model inference
    results = model(frame, verbose=False)

    detections: List[dict] = []

    # Process results
    for result in results:
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            continue

        for box in boxes:
            class_id = int(box.cls[0])
            class_name = CLASS_NAMES.get(class_id)

            # Skip unknown classes
            if class_name is None:
                continue

            confidence = float(box.conf[0])

            # Filter weak detections
            if confidence < CONF_THRESHOLD:
                continue

            x1, y1, x2, y2 = map(float, box.xyxy[0])

            detections.append({
                "class": class_name,
                "confidence": round(confidence, 3),
                "bbox": [x1, y1, x2, y2],
            })

    logger.debug("Detections generated: %d", len(detections))

    return detections
