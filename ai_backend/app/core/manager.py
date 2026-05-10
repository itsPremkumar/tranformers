import json
import asyncio
from typing import List, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Map each connection to its specific robot identity
        self.robot_profiles = {} 

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.robot_profiles[websocket] = {
            "name": "Unknown",
            "persona": "A mysterious robot.",
            "version": "unknown",
            "language": "en",
            "battery": 0,
            "distance": 0,
            "current_mode": "Robot",
            "current_task": "Idle"
        }
        print(f"Robot Connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.robot_profiles.pop(websocket, None)
            print(f"Robot Disconnected: {websocket.client}")

    async def send_command(self, cmd, target_ws: Optional[WebSocket] = None):
        """Sends a command to a specific robot or all robots."""
        targets = [target_ws] if target_ws else self.active_connections
        for connection in targets:
            try:
                if isinstance(cmd, bytes):
                    await connection.send_bytes(cmd)
                else:
                    await connection.send_text(cmd)
            except:
                pass

    def update_profile(self, websocket: WebSocket, profile: dict):
        if websocket in self.robot_profiles:
            self.robot_profiles[websocket].update(profile)

    def get_profile(self, websocket: WebSocket):
        return self.robot_profiles.get(websocket)

manager = ConnectionManager()
