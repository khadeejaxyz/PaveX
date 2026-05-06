"""
WebSocket endpoint for frontend alert/status connectivity.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(
        {
            "type": "connection",
            "data": {"connected": True},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    await websocket.send_json(
        {
            "type": "system_status",
            "data": {
                "websocket": "connected",
                "detection": "active",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
