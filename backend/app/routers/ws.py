from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.ws_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{torno_id}")
async def websocket_endpoint(ws: WebSocket, torno_id: int):
    await manager.connect(torno_id, ws)
    try:
        while True:
            data = await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(torno_id, ws)
    except Exception:
        manager.disconnect(torno_id, ws)
