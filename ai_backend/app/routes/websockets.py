import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.manager import manager
from app.core.llm_factory import LLMFactory
from app.tools.vision import capture_frame
from app.tools.reactive_vision import reactive_vision

router = APIRouter()
llm = LLMFactory(manager)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles real-time communication with the robot hardware."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("IDENTITY:"):
                try:
                    payload = json.loads(data[9:])
                    manager.update_profile(websocket, payload)
                    profile = manager.get_profile(websocket)
                    print(f"--- ROBOT IDENTIFIED: {profile['name']} ---")
                except: pass
            elif data.startswith("DISTANCE:"):
                try:
                    dist = int(data[9:])
                    reactive_vision.last_distance = dist
                    manager.update_profile(websocket, {"distance": dist})
                except: pass
            elif data.startswith("BATTERY:"):
                try:
                    bat = float(data[8:])
                    reactive_vision.last_battery = bat
                    manager.update_profile(websocket, {"battery": round(bat, 1)})
                except: pass
            elif data.startswith("CURRENT:"):
                try:
                    curr = float(data[8:])
                    if curr > 2.5: # 2.5 Amps limit
                        await manager.send_command("CMD:STOP")
                        print("[SAFETY] Emergency Stop: High Current Detected!")
                except: pass
            elif data == "CMD:IDLE_OBSERVE":
                profile = manager.get_profile(websocket)
                robot_name = profile.get("name", "Unknown")
                print(f"[CURIOSITY] {robot_name} is bored. Triggering investigation...")
                image = capture_frame()
                json_response = await llm.get_response(
                    "You have been idle. Look at the camera feed, find something interesting (an object, person, or color), and announce that you are going to investigate it. Be curious and scientific.",
                    robot_name,
                    image
                )
                try:
                    commands = json.loads(json_response)
                    for cmd in commands:
                        await manager.send_command(cmd, target_ws=websocket)
                except: pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Feature 6: Active Swarm Knowledge Sharing via WebSockets
swarm_connections = []

@router.websocket("/ws/swarm_knowledge")
async def swarm_knowledge_endpoint(websocket: WebSocket):
    """
    Broadcasts discovered scientific facts and telemetry diagnoses to all connected swarm nodes.
    """
    await websocket.accept()
    swarm_connections.append(websocket)
    try:
        while True:
            # When a node shares knowledge, broadcast it to the rest of the swarm
            knowledge_payload = await websocket.receive_text()
            print(f"[SWARM] Broadcasting new knowledge: {knowledge_payload[:50]}...")
            for connection in swarm_connections:
                if connection != websocket:
                    try:
                        await connection.send_text(knowledge_payload)
                    except: pass
    except WebSocketDisconnect:
        swarm_connections.remove(websocket)
