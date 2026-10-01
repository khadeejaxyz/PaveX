"""
PaveX – Depth Estimation Module
backend/app/core/depth.py

Provides a single, per-frame relative depth map used by severity.py to
gauge how close a detected hazard is to the camera. This is monocular
(single-camera) depth — it produces RELATIVE closeness within a frame,
not calibrated real-world distance. That's sufficient for ranking
hazard urgency; it is not a substitute for a physical distance sensor.

Model: MiDaS_small (via torch.hub) — chosen for speed over accuracy,
since this runs inline with the detection pipeline. If depth inference
becomes a bottleneck once tested on real hardware, set
PAVEX_DEPTH_ENABLED=false to disable this stage entirely; severity.py
falls back to bbox-size-only scoring automatically.

When moving to edge hardware later, swap this module's model-loading
block for an ONNX/TensorRT-exported MiDaS — `estimate_depth()`'s
signature and return shape stay the same, so nothing above this module
needs to change.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEPTH_ENABLED: bool = os.getenv("PAVEX_DEPTH_ENABLED", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Optional torch import — depth gracefully disabled if torch not installed
# ---------------------------------------------------------------------------

_torch = None
_torch_available = False

if DEPTH_ENABLED:
    try:
        import torch as _torch  # type: ignore[assignment]
        _torch_available = True
    except ImportError:
        _torch_available = False
        DEPTH_ENABLED = False
        logger.warning(
            "torch is not installed. Depth estimation disabled for this session; "
            "severity falls back to bbox-size scoring only."
        )

_DEVICE = None
if _torch_available and _torch is not None:
    _DEVICE = _torch.device("cuda" if _torch.cuda.is_available() else "cpu")

# ---------------------------------------------------------------------------
# Model – loaded ONCE at module import time (same pattern as inference.py)
# ---------------------------------------------------------------------------

_model = None
_transform = None


def _trust_torch_hub_repo(owner: str, repo: str) -> None:
    """Avoid torch.hub input prompts for known model dependencies."""
    try:
        hub_dir = Path(_torch.hub.get_dir())
        hub_dir.mkdir(parents=True, exist_ok=True)
        trusted_list = hub_dir / "trusted_list"
        trusted_list.touch(exist_ok=True)

        repo_id = f"{owner}_{repo}"
        trusted = {line.strip() for line in trusted_list.read_text().splitlines()}
        if repo_id not in trusted:
            with trusted_list.open("a", encoding="utf-8") as fh:
                fh.write(f"{repo_id}\n")
    except OSError as exc:
        logger.warning("Could not update torch.hub trusted repo list: %s", exc)


if DEPTH_ENABLED and _torch_available:
    try:
        _trust_torch_hub_repo("rwightman", "gen-efficientnet-pytorch")

        _model = _torch.hub.load("intel-isl/MiDaS", "MiDaS_small", trust_repo=True)
        _model.to(_DEVICE)
        _model.eval()

        _midas_transforms = _torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
        _transform = _midas_transforms.small_transform

        logger.info("Depth model (MiDaS_small) loaded successfully on %s", _DEVICE)
    except Exception as exc:
        logger.error(
            "Failed to load depth model: %s. Depth estimation will be disabled "
            "for this session; severity falls back to bbox-size scoring only.",
            exc,
            exc_info=True,
        )
        DEPTH_ENABLED = False
else:
    if not _torch_available:
        pass  # warning already emitted above
    else:
        logger.info("Depth estimation disabled via PAVEX_DEPTH_ENABLED=false")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def estimate_depth(frame: np.ndarray) -> np.ndarray | None:
    """
    Returns a relative depth map, same (H, W) as the input frame, where
    HIGHER values = CLOSER to the camera (MiDaS convention: inverse depth).

    Returns None if depth is disabled or estimation fails — callers must
    handle None gracefully (severity.py treats it as "no depth signal").
    """
    if not DEPTH_ENABLED or _model is None:
        return None

    if frame is None or frame.size == 0:
        logger.warning("estimate_depth received an empty frame.")
        return None

    try:
        # MiDaS expects RGB; OpenCV frames are BGR
        img_rgb = frame[:, :, ::-1]

        input_batch = _transform(img_rgb).to(_DEVICE)

        with _torch.no_grad():
            prediction = _model(input_batch)
            prediction = _torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=frame.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        depth_map = prediction.cpu().numpy()
        return depth_map

    except Exception as exc:
        logger.error("Depth estimation failed: %s", exc, exc_info=True)
        return None


def closeness_score(depth_map: np.ndarray, bbox: list) -> float | None:
    """
    Returns a 0-1 score for how close the region inside `bbox` is,
    RELATIVE to the depth range of this specific frame (1 = closest
    object in the frame, 0 = farthest). Returns None if it can't be
    computed (missing depth map, degenerate bbox, flat depth range).
    """
    if depth_map is None:
        return None

    try:
        x1, y1, x2, y2 = (int(v) for v in bbox)
        h, w = depth_map.shape[:2]
        x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
        y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))

        if x2 <= x1 or y2 <= y1:
            return None

        region = depth_map[y1:y2, x1:x2]
        if region.size == 0:
            return None

        region_mean = float(np.mean(region))
        frame_min = float(np.min(depth_map))
        frame_max = float(np.max(depth_map))

        if frame_max - frame_min < 1e-6:
            return None  # flat depth map, no usable signal

        score = (region_mean - frame_min) / (frame_max - frame_min)
        return max(0.0, min(1.0, score))

    except Exception as exc:
        logger.error("closeness_score computation failed: %s", exc, exc_info=True)
        return None
