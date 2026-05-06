"""
PaveX – Decision Engine Module
backend/app/core/decision.py

Converts a detection's severity level into a structured, actionable
driving decision.  Pure Python, no external dependencies, real-time safe.

Pipeline position:
    Frame → Inference → Severity → Decision → Final Output
"""

from __future__ import annotations

import logging
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Decision map  (single source of truth — change here, nowhere else)
# ---------------------------------------------------------------------------
#
# Each entry defines the complete driver instruction for a severity tier.
# Keys mirror the severity values produced by severity.py exactly.
#
# "risk_level" intentionally echoes severity so downstream consumers
# (UI, alerting, telemetry) can work from `decision` alone without
# needing to look back at the parent field.

_DECISION_MAP: dict[str, dict[str, Any]] = {
    "low": {
        "action": "maintain",
        "recommended_speed_kmph": 50,
        "risk_level": "low",
    },
    "medium": {
        "action": "slow_down",
        "recommended_speed_kmph": 30,
        "risk_level": "medium",
    },
    "high": {
        "action": "brake",
        "recommended_speed_kmph": 10,
        "risk_level": "high",
    },
}

# Fallback used whenever an unrecognised severity value arrives.
_DEFAULT_SEVERITY = "low"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_decision(severity: str) -> dict[str, Any]:
    """Map a severity level to a structured driving decision.

    Parameters
    ----------
    severity:
        One of ``"low"``, ``"medium"``, or ``"high"`` as produced by
        ``severity.compute_severity``.

    Returns
    -------
    dict
        A decision dictionary with the following keys:

        .. code-block:: json

            {
                "action":                  "maintain" | "slow_down" | "brake",
                "recommended_speed_kmph":  50 | 30 | 10,
                "risk_level":              "low" | "medium" | "high"
            }

    Notes
    -----
    * Unknown severity values are treated as ``"low"`` and a warning is
      emitted so the caller can triage misconfigured upstream stages.
    * The returned dict is a **shallow copy** of the internal map entry,
      making it safe for callers to mutate without affecting future calls.
    """
    if severity not in _DECISION_MAP:
        logger.warning(
            "compute_decision received unknown severity '%s'. "
            "Expected one of %s. Defaulting to '%s'.",
            severity,
            list(_DECISION_MAP.keys()),
            _DEFAULT_SEVERITY,
        )
        severity = _DEFAULT_SEVERITY

    decision = dict(_DECISION_MAP[severity])  # shallow copy — caller-safe

    logger.debug(
        "severity='%s' → action='%s', speed=%d km/h, risk='%s'",
        severity,
        decision["action"],
        decision["recommended_speed_kmph"],
        decision["risk_level"],
    )

    return decision


def enrich_detections_with_decision(
    detections: list[dict],
) -> list[dict]:
    """Attach a ``"decision"`` block to every detection dict.

    Follows the same additive pattern as ``severity.enrich_detections_with_severity``:
    previous fields are preserved untouched and a new ``"decision"`` key is
    appended.

    Parameters
    ----------
    detections:
        List of detection dicts already enriched with a ``"severity"`` field,
        as produced by ``severity.enrich_detections_with_severity``.

    Returns
    -------
    list[dict]
        New list where each dict contains the original fields **plus**
        a nested ``"decision"`` block::

            {
                "class":      "pothole",
                "confidence": 0.91,
                "bbox":       [x1, y1, x2, y2],
                "severity":   "high",
                "decision": {
                    "action":                 "brake",
                    "recommended_speed_kmph": 10,
                    "risk_level":             "high"
                }
            }

    Notes
    -----
    * Input dicts are **never mutated**; each is shallow-copied via
      ``{**detection, "decision": ...}``.
    * A missing or invalid ``"severity"`` key defaults to ``"low"`` via
      ``compute_decision``'s own validation — no duplicate guard needed here.
    * A per-detection ``try/except`` prevents a single bad entry from
      aborting the entire batch.
    """
    if not detections:
        logger.debug("enrich_detections_with_decision: empty detections list.")
        return []

    enriched: list[dict] = []

    for idx, detection in enumerate(detections):
        severity = detection.get("severity")

        if not isinstance(severity, str):
            logger.warning(
                "Detection #%d has no valid 'severity' field (%r). "
                "compute_decision will fall back to '%s'.",
                idx,
                severity,
                _DEFAULT_SEVERITY,
            )
            # Pass the raw value — compute_decision handles the fallback
            # and logs its own warning so we don't double-report.
            severity = severity  # noqa: PLW0127  (explicit no-op for clarity)

        try:
            decision = compute_decision(severity)
        except Exception as exc:  # pragma: no cover — belt-and-suspenders
            logger.error(
                "Unexpected error computing decision for detection #%d: %s",
                idx,
                exc,
                exc_info=True,
            )
            decision = dict(_DECISION_MAP[_DEFAULT_SEVERITY])

        enriched.append({**detection, "decision": decision})

    logger.debug(
        "enrich_detections_with_decision: enriched %d detection(s).",
        len(enriched),
    )
    return enriched