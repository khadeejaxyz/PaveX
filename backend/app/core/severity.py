"""
PaveX – Severity Estimation Module
backend/app/core/severity.py

Adds a rule-based "severity" field (low / medium / high) to each detection
produced by inference.py.  No ML is used; all thresholds are loaded once
from backend/app/config/severity_config.yaml.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SEVERITY_LEVELS = ("low", "medium", "high")

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_CONFIG_PATH = Path(
    os.environ.get(
        "PAVEX_SEVERITY_CONFIG",
        _BACKEND_DIR / "app" / "config" / "severity_config.yaml",
    )
)

# ---------------------------------------------------------------------------
# Config loader – executed once at module import
# ---------------------------------------------------------------------------


def _load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Severity config not found at '{path}'. "
            "Set the PAVEX_SEVERITY_CONFIG env-var to override the path."
        )

    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    for key in ("low_threshold", "medium_threshold"):
        if key not in cfg:
            raise ValueError(f"Missing required config key: '{key}'")
        if not isinstance(cfg[key], (int, float)) or cfg[key] < 0:
            raise ValueError(f"'{key}' must be a non-negative number.")

    if cfg["low_threshold"] >= cfg["medium_threshold"]:
        raise ValueError(
            "'low_threshold' must be strictly less than 'medium_threshold'."
        )

    pw = cfg.get("position_weighting", {})
    ratio = pw.get("lower_frame_ratio", 0.7)
    if not (0.0 < ratio < 1.0):
        raise ValueError("'lower_frame_ratio' must be in the open interval (0, 1).")

    logger.info(
        "Severity config loaded from '%s' — low=%.1f%%, medium=%.1f%%, "
        "pos_weighting=%s, lower_frame_ratio=%.2f",
        path,
        cfg["low_threshold"],
        cfg["medium_threshold"],
        pw.get("enabled", False),
        ratio,
    )
    return cfg


try:
    _cfg = _load_config(_CONFIG_PATH)
except Exception as exc:
    logger.critical("Failed to load severity config: %s", exc, exc_info=True)
    raise

_LOW_THRESHOLD: float = float(_cfg["low_threshold"])
_MEDIUM_THRESHOLD: float = float(_cfg["medium_threshold"])

_PW_ENABLED: bool = bool(_cfg.get("position_weighting", {}).get("enabled", False))
_LOWER_FRAME_RATIO: float = float(
    _cfg.get("position_weighting", {}).get("lower_frame_ratio", 0.7)
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _upgrade_severity(level: str) -> str:
    idx = _SEVERITY_LEVELS.index(level)
    return _SEVERITY_LEVELS[min(idx + 1, len(_SEVERITY_LEVELS) - 1)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_severity(bbox: list, frame_shape: tuple) -> str:
    if len(bbox) != 4:
        logger.warning("Invalid bbox length %d; expected 4. Defaulting to 'low'.", len(bbox))
        return "low"

    x1, y1, x2, y2 = (float(v) for v in bbox)

    if len(frame_shape) < 2:
        logger.warning("frame_shape has fewer than 2 dimensions. Defaulting to 'low'.")
        return "low"

    frame_height, frame_width = float(frame_shape[0]), float(frame_shape[1])

    if frame_height <= 0 or frame_width <= 0:
        logger.warning(
            "Non-positive frame dimensions (%.1f × %.1f). Defaulting to 'low'.",
            frame_height, frame_width,
        )
        return "low"

    # 🔥 Clamp bbox to frame boundaries
    x1 = max(0.0, min(x1, frame_width))
    x2 = max(0.0, min(x2, frame_width))
    y1 = max(0.0, min(y1, frame_height))
    y2 = max(0.0, min(y2, frame_height))

    # Re-check after clamping
    if x2 <= x1 or y2 <= y1:
        logger.warning(
            "Degenerate bbox after clamping [%.1f, %.1f, %.1f, %.1f]. Defaulting to 'low'.",
            x1, y1, x2, y2,
        )
        return "low"

    area = (x2 - x1) * (y2 - y1)
    frame_area = frame_height * frame_width
    bbox_pct = (area / frame_area) * 100.0

    if bbox_pct < _LOW_THRESHOLD:
        severity = "low"
    elif bbox_pct < _MEDIUM_THRESHOLD:
        severity = "medium"
    else:
        severity = "high"

    logger.debug(
        "bbox_pct=%.3f%% → base severity='%s'", bbox_pct, severity
    )

    if _PW_ENABLED:
        lower_boundary = _LOWER_FRAME_RATIO * frame_height
        if y2 > lower_boundary:
            upgraded = _upgrade_severity(severity)
            logger.debug(
                "y2=%.1f > lower_boundary=%.1f → upgrading '%s' → '%s'",
                y2, lower_boundary, severity, upgraded,
            )
            severity = upgraded

    return severity


def enrich_detections_with_severity(
    detections: list[dict],
    frame_shape: tuple,
) -> list[dict]:

    if not detections:
        logger.debug("enrich_detections_with_severity: empty detections list.")
        return []

    enriched: list[dict] = []

    for idx, detection in enumerate(detections):
        bbox = detection.get("bbox")

        if not isinstance(bbox, (list, tuple)):
            logger.warning(
                "Detection #%d has no valid 'bbox' key (%r). Defaulting severity to 'low'.",
                idx, bbox,
            )
            bbox = [0, 0, 0, 0]

        try:
            severity = compute_severity(bbox, frame_shape)
        except Exception as exc:
            logger.error(
                "Unexpected error computing severity for detection #%d: %s",
                idx, exc, exc_info=True,
            )
            severity = "low"

        enriched.append({**detection, "severity": severity})

    logger.debug(
        "Enriched %d detection(s) with severity levels.", len(enriched)
    )
    return enriched
