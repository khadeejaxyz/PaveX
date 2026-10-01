"""
PaveX – Pipeline Integration Module
backend/app/core/pipeline.py

Orchestrates the full detection pipeline in strict stage order:

    Frame → Inference → Depth → Severity → Decision → Final Output

This module owns no logic of its own — it delegates exclusively to the
core modules and returns a single, fully-enriched response dict.

Depth estimation is IDENTICAL for live feed and uploaded video/photo
frames — there is no separate code path per input source. If depth
estimation is disabled or fails, the pipeline degrades gracefully to
bbox-size-only severity, same as before this stage existed.
"""

from __future__ import annotations

import logging

import numpy as np

from app.core.decision import enrich_detections_with_decision
from app.core.depth import estimate_depth
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
        1. **Inference**  – ``run_inference``                    → raw detections
        2. **Depth**      – ``estimate_depth``                   → relative depth map (or None)
        3. **Severity**   – ``enrich_detections_with_severity``  → + severity field
        4. **Decision**   – ``enrich_detections_with_decision``  → + decision block

    Parameters
    ----------
    frame:
        BGR image decoded by OpenCV (``numpy.ndarray``, shape ``(H, W, C)``).
        Same code path regardless of whether this frame came from a live
        feed or was extracted from an uploaded video/photo.

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
                        "severity":   "critical",
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
        is invalid or an unrecoverable error occurs in the inference stage.

    Notes
    -----
    * Each stage is individually guarded by a ``try/except`` block so that
      a failure in one stage degrades gracefully instead of crashing the
      pipeline entirely.
    * A depth-estimation failure specifically degrades to ``depth_map=None``
      rather than aborting the pipeline — severity still runs, just without
      the depth-based escalation signal.
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
        logger.debug("No detections — skipping depth, severity and decision stages.")
        return {"num_detections": 0, "detections": []}

    # ── Stage 2 · Depth estimation ─────────────────────────────────────────
    depth_map = None
    try:
        depth_map = estimate_depth(frame)
        logger.debug(
            "Stage 2 (depth) complete — depth_map=%s",
            "available" if depth_map is not None else "unavailable",
        )
    except Exception as exc:
        logger.error(
            "Stage 2 (depth) failed: %s. Continuing without depth signal.",
            exc,
            exc_info=True,
        )
        depth_map = None

    # ── Stage 3 · Severity enrichment ──────────────────────────────────────
    try:
        detections = enrich_detections_with_severity(detections, frame.shape, depth_map)
        logger.debug(
            "Stage 3 (severity) complete — %d detection(s) enriched.",
            len(detections),
        )
    except Exception as exc:
        logger.error(
            "Stage 3 (severity) failed: %s. Returning detections without severity/decision.",
            exc,
            exc_info=True,
        )
        return {"num_detections": len(detections), "detections": detections}

    # ── Stage 4 · Decision enrichment ──────────────────────────────────────
    try:
        detections = enrich_detections_with_decision(detections)
        logger.debug(
            "Stage 4 (decision) complete — %d detection(s) fully enriched.",
            len(detections),
        )
    except Exception as exc:
        logger.error(
            "Stage 4 (decision) failed: %s. Returning detections without decision.",
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