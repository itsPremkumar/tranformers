import os
import cv2
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from app.core.config import settings
from app.core.manager import manager
from app.core.llm_factory import LLMFactory
from app.tools.vision import capture_frame
from app.tools.audio import generate_tts_pcm
from app.tools.reactive_vision import reactive_vision
import subprocess
from pydantic import BaseModel

app = FastAPI(title=settings.PROJECT_NAME)
llm = LLMFactory(manager)

# Global camera object for the local USB camera
global_cap = None

class UserPrompt(BaseModel):
    prompt: str

async def approach_target(action_at_end=None):
    """Autonomous navigation loop towards a vision target."""
    print(f"[AUTO] Approaching target for action: {action_at_end}")
    
    # Ensure robot is in correct mode (Robot Mode for interaction)
    if action_at_end in ["KICK", "PUSH"]:
        await manager.send_command("CMD:TRANSFORM") # Ensure Robot Mode
        await asyncio.sleep(2)

    while reactive_vision.is_tracking:
        off_x = reactive_vision.target_offset_x
        area = reactive_vision.target_area
        
        # 1. Alignment (Turn towards target)
        if off_x > 0.2:
            await manager.send_command("CMD:RIGHT")
        elif off_x < -0.2:
            await manager.send_command("CMD:LEFT")
        else:
            # 2. Distance Control (Move forward until close)
            if area < 0.15: # Target is small (far away)
                await manager.send_command("CMD:FORWARD")
            else:
                # 3. Target Reached! Perform Action
                await manager.send_command("CMD:STOP")
                if action_at_end == "KICK":
                    await manager.send_command("CMD:KICK")
                elif action_at_end == "PUSH":
                    await manager.send_command("CMD:PUSH")
                
                print(f"[AUTO] Task {action_at_end} Complete.")
                reactive_vision.is_tracking = False # Stop tracking once done
                break
        
        await asyncio.sleep(0.5)

@app.post("/ask")
async def ask_robot(user_input: UserPrompt):
    """The main AI endpoint. Handles vision and physical voice."""
    print(f"\n[DEBUG] --- NEW REQUEST ---")
    print(f"[DEBUG] User Prompt: {user_input.prompt}")
    
    image = None
    # Smart Vision Trigger: Capture frame if the prompt implies looking at something
    visual_keywords = ["see", "look", "watch", "camera", "what is", "who is", "describe", "identify", "where", "detect"]
    if any(k in user_input.prompt.lower() for k in visual_keywords):
        print(f"[DEBUG] Vision Triggered. Capturing frame...")
        image = capture_frame()
        print(f"[DEBUG] Image Captured: {'Success' if image else 'Failed'}")
    
    # Smart Internet Trigger: Search the web if the prompt implies needing current info
    internet_results = None
    search_keywords = ["search", "google", "weather", "news", "who is", "what is the price", "latest"]
    if any(k in user_input.prompt.lower() for k in search_keywords):
        from app.tools.internet import web_search
        print(f"[DEBUG] Internet Search Triggered. Searching for: {user_input.prompt}")
        internet_results = web_search(user_input.prompt)
        print(f"[DEBUG] Internet Results Length: {len(internet_results) if internet_results else 0}")
    
    # Get the active robot's name and mode for memory retrieval
    robot_name = "Unknown"
    robot_mode = "Robot" # Default
    if manager.active_connections:
        ws = manager.active_connections[0]
        profile = manager.get_profile(ws)
        robot_name = profile.get("name", "Unknown")
        robot_mode = profile.get("current_mode", "Robot")

    print(f"[DEBUG] Robot: {robot_name}, Mode: {robot_mode}")

    # Collect Hardware Status
    hw_status = {
        "battery": round(reactive_vision.last_battery, 1),
        "distance": reactive_vision.last_distance,
        "mode": robot_mode
    }

    print(f"[DEBUG] Requesting LLM Response...")
    json_response = await llm.get_response(user_input.prompt, robot_name, image, hw_status=hw_status, internet_context=internet_results)
    print(f"[DEBUG] LLM Response: {json_response[:100]}...")
    
    try:
        commands = json.loads(json_response)
        if manager.active_connections:
            ws = manager.active_connections[0] # Assume first robot for now
            for cmd in commands:
                await manager.send_command(cmd)
                
                # Update mode tracking
                if "CMD:TRANSFORM" in cmd:
                    manager.update_profile(ws, {"current_mode": "Car"})
                elif "CMD:WALK" in cmd:
                    manager.update_profile(ws, {"current_mode": "Robot"})
                
                # --- Advanced Task Handling ---
                if "CMD:FOLLOW" in cmd:
                    manager.update_profile(ws, {"current_task": "Following Face"})
                    asyncio.create_task(reactive_vision.start_tracking("face"))
                
                if "CMD:PLAY_BALL" in cmd:
                    manager.update_profile(ws, {"current_task": "Playing Ball"})
                    asyncio.create_task(reactive_vision.start_tracking("ball"))
                    asyncio.create_task(approach_target(action_at_end="KICK"))
                
                if "CMD:COLLECT_WASTE" in cmd:
                    manager.update_profile(ws, {"current_task": "Collecting Waste"})
                    asyncio.create_task(reactive_vision.start_tracking("waste"))
                    asyncio.create_task(approach_target(action_at_end="PUSH"))
                
                if "CMD:STOP_FOLLOW" in cmd:
                    manager.update_profile(ws, {"current_task": "Idle"})
                    reactive_vision.is_tracking = False
                
                # Check for speech command to send physical audio
                if cmd.startswith("SAY:"):
                    text = cmd[4:]
                    # Get language from robot profile
                    robot_lang = "en"
                    if manager.active_connections:
                        ws = manager.active_connections[0]
                        profile = manager.get_profile(ws)
                        robot_lang = profile.get("language", "en")
                    
                    # Use thread to avoid blocking the event loop
                    pcm_data = await asyncio.to_thread(generate_tts_pcm, text, lang=robot_lang)
                    if pcm_data:
                        print(f"[AUDIO] Streaming {len(pcm_data)} bytes to robot body...")
                        # Send binary audio data
                        await manager.send_command(pcm_data)
        
        return {"status": "success", "commands": commands}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/manual_cmd")
async def manual_cmd(cmd: str):
    """Direct manual override from dashboard buttons."""
    await manager.send_command(cmd)
    return {"status": "sent"}

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serves the Unified AI Dashboard."""
    try:
        with open("app/templates/dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Dashboard template not found in app/templates/"

async def gen_frames():
    """Video streaming generator function using a shared camera instance."""
    global global_cap
    source = settings.LOCAL_CAMERA_INDEX if settings.USE_LOCAL_CAMERA else settings.ESP32_CAM_URL
    
    if settings.USE_LOCAL_CAMERA:
        if global_cap is None or not global_cap.isOpened():
            print(f"[VIDEO] Initializing shared camera source: {source}")
            global_cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        cap = global_cap
    else:
        # For ESP32-CAM (URL), we can open new ones or proxy, but let's stick to simple capture for now
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"[VIDEO] ERROR: Could not open source {source}")
        return

    try:
        while True:
            if reactive_vision.is_tracking and reactive_vision.latest_frame is not None:
                frame = reactive_vision.latest_frame
            else:
                success, frame = cap.read()
                if not success:
                    print(f"[VIDEO] ERROR: Failed to read frame from source {source}")
                    # If it's a local camera, try to re-initialize next time
                    if settings.USE_LOCAL_CAMERA:
                        cap.release()
                    break
            
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            await asyncio.sleep(0.03) # ~30 FPS
    except Exception as e:
        print(f"[VIDEO] Exception in gen_frames: {e}")
    # Note: We don't release global_cap here so other clients can use it

@app.get("/video_feed")
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return StreamingResponse(gen_frames(), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get("/status")
async def get_status():
    """Returns the current hardware status for all connected robots."""
    robots = []
    for ws, profile in manager.robot_profiles.items():
        robots.append({
            "id": id(ws),
            "name": profile.get("name"),
            "battery": profile.get("battery"),
            "distance": profile.get("distance"),
            "mode": profile.get("current_mode"),
            "task": profile.get("current_task")
        })
    return {"robots": robots}

@app.websocket("/ws")
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
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def proactive_loop():
    """Background task to engage humans every 60 seconds across all robots."""
    while True:
        await asyncio.sleep(60)
        # Iterate over a copy of connections to be thread-safe
        for ws in list(manager.active_connections):
            try:
                profile = manager.get_profile(ws)
                robot_name = profile.get("name", "Unknown")
                
                print(f"[PROACTIVE] Engaging {robot_name}...")
                json_response = await llm.get_response("Look around and make a curious observation.", robot_name)
                commands = json.loads(json_response)
                for cmd in commands:
                    await manager.send_command(cmd, target_ws=ws)
            except Exception as e:
                print(f"Proactive Loop Error for {robot_name if 'robot_name' in locals() else 'Unknown'}: {e}")

def check_ollama():
    """Ensures Ollama is running before the backend starts."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', 11434)) != 0:
            print("[OLLAMA] Server not detected. Starting Ollama automatically...")
            # Try to start Ollama in the background
            try:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("[OLLAMA] Started successfully.")
            except Exception as e:
                print(f"[OLLAMA] Error starting: {e}")

@app.on_event("startup")
async def startup():
    check_ollama()
    asyncio.create_task(proactive_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
