import os
import cv2
import json
import asyncio
import sys
import io

# Force UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from app.core.config import settings
from app.core.manager import manager
from app.core.llm_factory import LLMFactory
from app.tools.vision import capture_frame
from app.tools.audio import generate_tts_pcm
from app.tools.reactive_vision import reactive_vision
from app.tools.odometry import visual_odometry
from app.tools.solar import analyze_brightness
import subprocess
from pydantic import BaseModel

try:
    from app.tools.voice_assistant import voice_assistant
    VOICE_ENABLED = True
except Exception as e:
    print(f"[VOICE] Voice Assistant disabled (Missing dependencies or model): {e}")
    VOICE_ENABLED = False

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
    
    # Get the active robot's name and mode for memory retrieval
    robot_name = "Unknown"
    robot_mode = "Robot" # Default
    if manager.active_connections:
        ws = manager.active_connections[0]
        profile = manager.get_profile(ws)
        robot_name = profile.get("name", "Unknown")
        robot_mode = profile.get("current_mode", "Robot")

    print(f"[DEBUG] Robot: {robot_name}, Mode: {robot_mode}")

    # 1. Swarm Reasoning Interceptor (Runs the multi-minute deep thinking loop)
    swarm_keywords = ["think deeply", "thinking mode", "swarm reasoning", "analyze deeply", "contemplate"]
    if any(k in user_input.prompt.lower() for k in swarm_keywords):
        print(f"[DEBUG] SWARM REASONING ACTIVATED for: {user_input.prompt}")
        from app.tools.deep_thinking import run_swarm_reasoning
        # Run the full swarm logic and return directly, skipping the standard short-loop
        commands = await run_swarm_reasoning(user_input.prompt, manager, llm, robot_name, None)
        return {"status": "success", "commands": commands}

    image = None
    # Smart Vision Trigger: Capture frame if the prompt implies looking at something
    visual_keywords = ["see", "look", "watch", "camera", "describe", "identify", "detect", "in front of"]
    if any(k in user_input.prompt.lower() for k in visual_keywords):
        print(f"[DEBUG] Vision Triggered. Capturing frame...")
        image = capture_frame()
        print(f"[DEBUG] Image Captured: {'Success' if image else 'Failed'}")
    
    # Smart Internet Trigger: Search the web if the prompt implies needing current info
    internet_results = None
    deep_keywords = ["deep research", "browser research", "research deeply", "deep search", "learn about"]
    search_keywords = ["search", "google", "weather", "news", "who is", "what is the price", "latest"]
    
    if any(k in user_input.prompt.lower() for k in deep_keywords):
        from app.tools.deep_research import run_research_subprocess
        print(f"[DEBUG] Playwright Deep Research Triggered. Scrapping: {user_input.prompt}")
        internet_results = await run_research_subprocess(user_input.prompt)
        print(f"[DEBUG] Deep Research Results Length: {len(internet_results) if internet_results else 0}")
    elif any(k in user_input.prompt.lower() for k in search_keywords):
        from app.tools.internet import web_search
        print(f"[DEBUG] Internet Search Triggered. Searching for: {user_input.prompt}")
        internet_results = web_search(user_input.prompt)
        print(f"[DEBUG] Internet Results Length: {len(internet_results) if internet_results else 0}")

    # Collect Hardware Status
    hw_status = {
        "battery": round(reactive_vision.last_battery, 1),
        "distance": reactive_vision.last_distance,
        "mode": robot_mode
    }

    # Hybrid Command Dispatcher (Ensures reliability for critical hardware tasks)
    hybrid_commands = []
    if any(k in user_input.prompt.lower() for k in ["waste", "trash", "garbage"]):
        hybrid_commands.append("CMD:COLLECT_WASTE")
    if any(k in user_input.prompt.lower() for k in ["follow", "track me", "look at me"]):
        hybrid_commands.append("CMD:FOLLOW")
    if "play" in user_input.prompt.lower():
        # Extrapolate song name for the playback tool
        query = user_input.prompt.lower().split("play")[-1].replace("on youtube", "").replace("song", "").strip()
        hybrid_commands.append(f"SAY:Playing '{query}' on YouTube.")

    print(f"[DEBUG] Requesting LLM Response...")
    json_response = await llm.get_response(user_input.prompt, robot_name, image, hw_status=hw_status, internet_context=internet_results)
    
    try:
        commands = json.loads(json_response)
        # Merge hybrid commands (avoid duplicates)
        for h_cmd in hybrid_commands:
            if h_cmd not in commands:
                commands.insert(0, h_cmd)
        
        if manager.active_connections:
            ws = manager.active_connections[0] # Assume first robot for now
            for cmd in commands:
                if not isinstance(cmd, str):
                    continue
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
                
                if "SAY:Playing" in cmd and "on YouTube" in cmd:
                    from app.tools.internet import play_youtube
                    song_name = cmd.replace("SAY:Playing '", "").replace("' on YouTube.", "").strip()
                    await asyncio.to_thread(play_youtube, song_name)
                    asyncio.create_task(approach_target(action_at_end="PUSH"))
                
                if "CMD:STOP_FOLLOW" in cmd:
                    manager.update_profile(ws, {"current_task": "Idle"})
                    reactive_vision.is_tracking = False
                
                # --- EVENT HANDLERS ---
                if "EVENT:LOUD_NOISE" in cmd:
                    print("[EVENT] Brain heard a loud noise!")
                    async def curiosity_sequence():
                        await manager.send_command("CMD:STOP", target_ws=ws)
                        await manager.send_command("PAN:45", target_ws=ws)
                        await asyncio.sleep(0.5)
                        await manager.send_command("PAN:135", target_ws=ws)
                        await asyncio.sleep(0.5)
                        await manager.send_command("PAN:90", target_ws=ws)
                        await manager.send_command("SAY:I heard something. Is someone there?", target_ws=ws)
                    asyncio.create_task(curiosity_sequence())

                if "CMD:RESET_ODO" in cmd:
                    visual_odometry.reset()

                if "CMD:SUN_SEEK" in cmd:
                    print("[SOLAR] Sun-seeking initiated...")
                    manager.update_profile(ws, {"current_task": "Sun-Seeking"})
                    # Start a loop to steer toward light
                    async def solar_loop():
                        while manager.get_profile(ws).get("current_task") == "Sun-Seeking":
                            img = capture_frame()
                            if img:
                                data = analyze_brightness(img)
                                if data and data["intensity"] > 0.4:
                                    if data["x"] > 0.2: await manager.send_command("CMD:RIGHT", target_ws=ws)
                                    elif data["x"] < -0.2: await manager.send_command("CMD:LEFT", target_ws=ws)
                                    else: await manager.send_command("CMD:FORWARD", target_ws=ws)
                                else:
                                    await manager.send_command("CMD:LEFT", target_ws=ws) # Scan for light
                            await asyncio.sleep(1)
                    asyncio.create_task(solar_loop())

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
            
            # --- Visual Odometry Update ---
            # Run in a separate thread to avoid blocking the stream
            await asyncio.to_thread(visual_odometry.process_frame, frame)
            
            # Sync position back to robot
            pos = visual_odometry.get_position()
            for ws in list(manager.active_connections):
                try:
                    await manager.send_command(f"POS:{pos['x']},{pos['y']}", target_ws=ws)
                except: pass
            
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            await asyncio.sleep(0.01) # Faster 60+ FPS potential
    except Exception as e:
        print(f"[VIDEO] Exception: {e}")
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
            "task": profile.get("current_task"),
            "pos": visual_odometry.get_position()
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

async def proactive_loop():
    """Background task to engage humans every 60 seconds across all robots."""
    while True:
        await asyncio.sleep(60)
        # Iterate over a copy of connections to be thread-safe
        for ws in list(manager.active_connections):
            try:
                profile = manager.get_profile(ws)
                robot_name = profile.get("name", "Unknown")
                
                # Only engage if the robot is idle
                if profile.get("current_task", "Idle") != "Idle":
                    continue

                print(f"[PROACTIVE] Engaging {robot_name}...")
                image = capture_frame()
                json_response = await llm.get_response(
                    "Make a short, curious observation about what you see in the camera or how you feel. Keep it under 20 words.", 
                    robot_name,
                    image
                )
                commands = json.loads(json_response)
                for cmd in commands:
                    await manager.send_command(cmd, target_ws=ws)
            except Exception as e:
                print(f"Proactive Loop Error: {e}")

async def proactive_voice_loop():
    """Background task to listen for the wake-word and process voice commands locally."""
    if not VOICE_ENABLED:
        return
        
    print("[VOICE] Proactive Voice Loop started (using local microphone).")
    while True:
        try:
            # This will block until wake-word is detected, then record and transcribe
            text, language = await voice_assistant.process_speech()
            
            if not text:
                continue
                
            print(f"[VOICE] Submitting to brain: '{text}' (Lang: {language})")
            
            # Update the robot profile with the detected language so TTS responds correctly
            if manager.active_connections:
                ws = manager.active_connections[0]
                manager.update_profile(ws, {"language": language})
            
            # Trigger the standard brain flow
            await ask_robot(UserPrompt(prompt=text))
            
        except Exception as e:
            print(f"[VOICE] Loop Error: {e}")
            await asyncio.sleep(1)

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
    if VOICE_ENABLED:
        asyncio.create_task(proactive_voice_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
