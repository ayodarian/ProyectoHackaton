from fastapi import WebSocket
from collections import defaultdict


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)
        self._ultimo_estado: dict[int, dict] = {}

    async def connect(self, torno_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[torno_id].append(ws)

    def disconnect(self, torno_id: int, ws: WebSocket) -> None:
        self._connections[torno_id] = [
            c for c in self._connections[torno_id] if c != ws
        ]
        if not self._connections[torno_id]:
            del self._connections[torno_id]

    async def broadcast(self, torno_id: int, data: dict) -> None:
        stale = []
        for ws in self._connections.get(torno_id, []):
            try:
                await ws.send_json(data)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(torno_id, ws)

    async def broadcast_estado(
        self, torno_id: int, estado: dict
    ) -> None:
        self._ultimo_estado[torno_id] = estado
        await self.broadcast(torno_id, {"type": "estado", "data": estado})

    async def broadcast_alerta(
        self, torno_id: int, alerta: dict
    ) -> None:
        await self.broadcast(torno_id, {"type": "alerta", "data": alerta})

    def set_ultimo_estado(self, torno_id: int, estado: dict) -> None:
        self._ultimo_estado[torno_id] = estado

    def get_ultimo_estado(self, torno_id: int) -> dict | None:
        return self._ultimo_estado.get(torno_id)

    def get_todos_estados(self) -> list[dict]:
        return list(self._ultimo_estado.values())


manager = ConnectionManager()
