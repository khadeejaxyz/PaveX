"""
backend/app/core/video_stream.py

Real-time video stream processing using OpenCV.
Captures frames, runs detection pipeline, overlays results, and displays output.
"""

import sys
import os
import time
import logging
from typing import Union

import cv2

# Add backend directory to Python path to resolve 'app' module imports
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.pipeline import run_pipeline  # 

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

# Visual style constants
_BOX_COLOR      = (0, 255, 0)       # green bounding box
_BOX_THICKNESS  = 2
_TEXT_COLOR     = (255, 255, 255)   # white label text
_TEXT_BG_COLOR  = (0, 180, 0)       # dark-green label background
_FPS_COLOR      = (0, 220, 255)     # yellow-ish FPS counter
_FONT           = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE     = 0.55
_FONT_THICKNESS = 1
_LABEL_PAD      = 4                 # pixels of padding around label text


def _draw_detection(frame, detection: dict) -> None:
    """
    Draw one detection's bounding box and label onto *frame* in-place.

    Expected detection keys:
        class, confidence, bbox, severity, action, recommended_speed
    """
    try:
        x1, y1, x2, y2 = (int(v) for v in detection["bbox"])
        cls       = detection.get("class", "unknown")
        severity  = detection.get("severity", "N/A")

        # ✅ FIX APPLIED HERE
        decision = detection.get("decision", {})
        rec_speed = decision.get("recommended_speed_kmph", "N/A")

        label     = f"{cls} | {severity} | {rec_speed} km/h"

        # --- bounding box ---
        cv2.rectangle(frame, (x1, y1), (x2, y2), _BOX_COLOR, _BOX_THICKNESS)

        # --- label background ---
        (txt_w, txt_h), baseline = cv2.getTextSize(
            label, _FONT, _FONT_SCALE, _FONT_THICKNESS
        )
        bg_y1 = max(y1 - txt_h - 2 * _LABEL_PAD, 0)
        bg_y2 = max(y1, txt_h + 2 * _LABEL_PAD)
        cv2.rectangle(
            frame,
            (x1, bg_y1),
            (x1 + txt_w + 2 * _LABEL_PAD, bg_y2),
            _TEXT_BG_COLOR,
            cv2.FILLED,
        )

        # --- label text ---
        cv2.putText(
            frame,
            label,
            (x1 + _LABEL_PAD, bg_y2 - _LABEL_PAD - baseline // 2),
            _FONT,
            _FONT_SCALE,
            _TEXT_COLOR,
            _FONT_THICKNESS,
            cv2.LINE_AA,
        )
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("Skipping malformed detection %s – %s", detection, exc)


def _draw_fps(frame, fps: float) -> None:
    """Overlay the current FPS in the top-right corner."""
    text = f"FPS: {fps:.1f}"
    (txt_w, txt_h), _ = cv2.getTextSize(text, _FONT, _FONT_SCALE, _FONT_THICKNESS)
    h, w = frame.shape[:2]
    x = w - txt_w - 10
    y = txt_h + 10
    cv2.putText(
        frame, text, (x, y), _FONT, _FONT_SCALE, _FPS_COLOR, _FONT_THICKNESS, cv2.LINE_AA
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_video_stream(source: Union[int, str] = 0) -> None:
    """
    Capture video from *source*, run the detection pipeline on every frame,
    overlay results, and display the output in real time.

    Parameters
    ----------
    source : int | str
        ``0`` (or any integer) selects the corresponding webcam.
        A string is treated as a file path to a video file.

    Controls
    --------
    Press **q** to quit.

    Raises
    ------
    RuntimeError
        If the video source cannot be opened.
    """
    # ------------------------------------------------------------------
    # Open video source
    # ------------------------------------------------------------------
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(
            f"Unable to open video source: {source!r}. "
            "Check that the device is connected or the file path is correct."
        )

    logger.info("Video stream started – source=%r. Press 'q' to quit.", source)

    # ------------------------------------------------------------------
    # FPS tracking
    # ------------------------------------------------------------------
    fps          = 0.0
    frame_count  = 0
    fps_interval = 0.5          # recalculate FPS every 0.5 s
    t_last       = time.perf_counter()

    try:
        while True:
            # --------------------------------------------------------------
            # 1. Read frame
            # --------------------------------------------------------------
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                # End of file → stop; transient camera hiccup → keep going
                if isinstance(source, str):
                    logger.info("End of video file reached.")
                    break
                logger.warning("Empty frame received – skipping.")
                continue

            # --------------------------------------------------------------
            # 2. Run detection pipeline
            # --------------------------------------------------------------
            detections = []
            try:
                result = run_pipeline(frame)  # ✅ FIXED
                detections = result.get("detections", [])
            except Exception as exc:          # noqa: BLE001
                logger.error("Pipeline error on frame %d: %s", frame_count, exc)

            # --------------------------------------------------------------
            # 3. Overlay detections
            # --------------------------------------------------------------
            for detection in detections:
                _draw_detection(frame, detection)

            # --------------------------------------------------------------
            # 4. Overlay FPS
            # --------------------------------------------------------------
            frame_count += 1
            t_now = time.perf_counter()
            elapsed = t_now - t_last
            if elapsed >= fps_interval:
                fps     = frame_count / elapsed
                frame_count = 0
                t_last  = t_now

            _draw_fps(frame, fps)

            # --------------------------------------------------------------
            # 5. Display
            # --------------------------------------------------------------
            cv2.imshow("Video Stream – press 'q' to quit", frame)

            # --------------------------------------------------------------
            # 6. Exit on 'q'
            # --------------------------------------------------------------
            if cv2.waitKey(30) & 0xFF == ord("q"):
                logger.info("Quit signal received.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Video stream stopped.")