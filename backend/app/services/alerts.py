"""
WebSocket connection manager for driver alerts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class AlertConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, driver_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(driver_id, set()).add(websocket)
        logger.info("Driver %s WebSocket connected (%s active)", driver_id, self.active_count)

    def disconnect(self, driver_id: str, websocket: WebSocket) -> None:
        sockets = self._connections.get(driver_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(driver_id, None)
        logger.info("Driver %s WebSocket disconnected (%s active)", driver_id, self.active_count)

    @property
    def active_count(self) -> int:
        return sum(len(sockets) for sockets in self._connections.values())

    async def send_to_driver(self, driver_id: str, message_type: str, data: dict[str, Any]) -> None:
        sockets = list(self._connections.get(driver_id, set()))
        if not sockets:
            return

        payload = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                logger.warning("Removing dead WebSocket for driver %s", driver_id, exc_info=True)
                self.disconnect(driver_id, websocket)

    async def broadcast_system_status(self) -> None:
        for driver_id in list(self._connections.keys()):
            await self.send_to_driver(
                driver_id,
                "system_status",
                {"websocket": "connected", "detection": "active"},
            )


alert_manager = AlertConnectionManager()

