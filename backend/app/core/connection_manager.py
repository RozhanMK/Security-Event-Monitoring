import uuid
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        self.connections.setdefault(user_id, []).append(ws)

    def disconnect(self, user_id: str, ws: WebSocket):
        if user_id in self.connections:
            try:
                self.connections[user_id].remove(ws)
                if not self.connections[user_id]:
                    del self.connections[user_id]
            except ValueError:
                pass 

    async def send_to_user(self, user_id: str, message: dict):
        connections = self.connections.get(user_id, [])
        for ws in connections[:]:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id, ws)

manager = ConnectionManager()
