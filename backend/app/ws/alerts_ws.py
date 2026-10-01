"""
WebSocket endpoint for frontend alert/status connectivity.

Improvements over the original:
- Heartbeat: server sends a ping every HEARTBEAT_INTERVAL seconds.
  If the client doesn't respond within HEARTBEAT_TIMEOUT seconds, the
  socket is considered dead and is forcefully disconnected. This prevents
  ghost connections from accumulating when clients tab-away or crash.
- Uniform disconnect: any exception (not just WebSocketDisconnect) results
  in `alert_manager.disconnect()` so the manager never holds stale refs.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.alerts import alert_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Heartbeat configuration
HEARTBEAT_INTERVAL = 25  # seconds between server pings
HEARTBEAT_TIMEOUT = 10   # seconds to wait for pong before disconnect


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket, driver_id: str = "default-driver"):
    """
    Persistent WebSocket for a single driver. Sends real-time hazard alerts
    produced by the proximity engine.

    Protocol:
      - Server → client: JSON message ``{"type": "ping", ...}`` every 25 s
      - Client → server: any text (e.g. "ping" or "pong") resets the liveness timer
      - On silence > 35 s the server closes the socket and removes the driver
    """
    await alert_manager.connect(driver_id, websocket)

    # Send initial handshake messages
    _now = datetime.now(timezone.utc).isoformat()
    await websocket.send_json({"type": "connection", "data": {"connected": True}, "timestamp": _now})
    await websocket.send_json(
        {
            "type": "system_status",
            "data": {"websocket": "connected", "detection": "active"},
            "timestamp": _now,
        }
    )

    last_pong = asyncio.get_event_loop().time()

    async def _heartbeat():
        """Periodically ping; disconnect if no response within timeout."""
        nonlocal last_pong
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            elapsed = asyncio.get_event_loop().time() - last_pong
            if elapsed > HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT:
                logger.warning(
                    "Driver %s WebSocket heartbeat timeout (%.0fs); disconnecting.",
                    driver_id,
                    elapsed,
                )
                alert_manager.disconnect(driver_id, websocket)
                try:
                    await websocket.close(code=1001)
                except Exception:
                    pass
                return
            # Send ping
            try:
                await websocket.send_json(
                    {
                        "type": "ping",
                        "data": {"ts": asyncio.get_event_loop().time()},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception:
                # Socket already dead — stop the heartbeat task
                return

    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        while True:
            message = await websocket.receive_text()
            # Any message from the client counts as liveness proof
            last_pong = asyncio.get_event_loop().time()
            if message in ("ping", "pong"):
                await websocket.send_json(
                    {
                        "type": "pong",
                        "data": {"connected": True},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
    except WebSocketDisconnect:
        logger.info("Driver %s WebSocket disconnected cleanly.", driver_id)
    except Exception as exc:
        logger.warning("Driver %s WebSocket error: %s", driver_id, exc)
    finally:
        heartbeat_task.cancel()
        alert_manager.disconnect(driver_id, websocket)
