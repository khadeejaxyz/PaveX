"""
PaveX – Pipeline Integration Module
backend/app/core/pipeline.py

Orchestrates the full detection pipeline in strict stage order:

    Frame → Inference → Severity → Decision → Final Output

This module owns no logic of its own — it delegates exclusively to the
three core modules and returns a single, fully-enriched response dict.
"""

from __future__ import annotations

import logging

import numpy as np

from app.core.decision import enrich_detections_with_decision
from app.core.inference import run_inference
from app.core.severity import enrich_detections_with_severity

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Empty-response sentinel  (returned on invalid input or total failure)
# ---------------------------------------------------------------------------

_EMPTY_RESPONSE: dict = {"num_detections": 0, "detections": []}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_pipeline(frame: np.ndarray) -> dict:
    """Execute the full PaveX detection pipeline on a single image frame.

    Stages (executed in strict order):
        1. **Inference**  – ``run_inference``               → raw detections
        2. **Severity**   – ``enrich_detections_with_severity`` → + severity field
        3. **Decision**   – ``enrich_detections_with_decision``  → + decision block

    Parameters
    ----------
    frame:
        BGR image decoded by OpenCV (``numpy.ndarray``, shape ``(H, W, C)``).

    Returns
    -------
    dict
        Fully enriched response::

            {
                "num_detections": 2,
                "detections": [
                    {
                        "class":      "pothole",
                        "confidence": 0.921,
                        "bbox":       [120.0, 340.5, 280.3, 460.1],
                        "severity":   "high",
                        "decision": {
                            "action":                 "brake",
                            "recommended_speed_kmph": 10,
                            "risk_level":             "high"
                        }
                    },
                    ...
                ]
            }

        Returns ``{"num_detections": 0, "detections": []}`` when the frame
        is invalid or an unrecoverable error occurs in any stage.

    Notes
    -----
    * Each stage is individually guarded by a ``try/except`` block so that
      a failure in one stage degrades gracefully instead of crashing the
      pipeline entirely.
    * No file I/O, no model loading, no external dependencies — real-time safe.
    """
    # ── Frame validation ───────────────────────────────────────────────────
    if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
        logger.warning(
            "run_pipeline received an invalid frame (%s). "
            "Returning empty response.",
            type(frame).__name__,
        )
        return dict(_EMPTY_RESPONSE)

    if frame.ndim < 2:
        logger.warning(
            "run_pipeline received a frame with unexpected ndim=%d. "
            "Returning empty response.",
            frame.ndim,
        )
        return dict(_EMPTY_RESPONSE)

    logger.debug(
        "Pipeline started — frame shape: %s, dtype: %s",
        frame.shape,
        frame.dtype,
    )

    # ── Stage 1 · Inference ────────────────────────────────────────────────
    try:
        detections = run_inference(frame)
        logger.debug(
            "Stage 1 (inference) complete — %d raw detection(s).",
            len(detections),
        )
    except Exception as exc:
        logger.error(
            "Stage 1 (inference) failed: %s. Returning empty response.",
            exc,
            exc_info=True,
        )
        return dict(_EMPTY_RESPONSE)

    if not detections:
        logger.debug("No detections — skipping severity and decision stages.")
        return {"num_detections": 0, "detections": []}

    # ── Stage 2 · Severity enrichment ─────────────────────────────────────
    try:
        detections = enrich_detections_with_severity(detections, frame.shape)
        logger.debug(
            "Stage 2 (severity) complete — %d detection(s) enriched.",
            len(detections),
        )
    except Exception as exc:
        logger.error(
            "Stage 2 (severity) failed: %s. Returning detections without severity/decision.",
            exc,
            exc_info=True,
        )
        return {"num_detections": len(detections), "detections": detections}

    # ── Stage 3 · Decision enrichment ─────────────────────────────────────
    try:
        detections = enrich_detections_with_decision(detections)
        logger.debug(
            "Stage 3 (decision) complete — %d detection(s) fully enriched.",
            len(detections),
        )
    except Exception as exc:
        logger.error(
            "Stage 3 (decision) failed: %s. Returning detections without decision.",
            exc,
            exc_info=True,
        )
        return {"num_detections": len(detections), "detections": detections}

    # ── Final response ─────────────────────────────────────────────────────
    response = {
        "num_detections": len(detections),
        "detections": detections,
    }

    logger.debug(
        "Pipeline complete — %d fully enriched detection(s) returned.",
        response["num_detections"],
    )

    return response