import uuid
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        self.connections.setdefault(user_id, []).append(ws)

    def disconnect(self, user_id: str, ws: WebSocket):
        self.connections[user_id].remove(ws)

    async def send_to_user(self, user_id: str, message: dict):
        for ws in self.connections.get(user_id, []):
            await ws.send_json(message)

manager = ConnectionManager()