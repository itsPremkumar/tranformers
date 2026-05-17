import os
import cv2
import asyncio
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from app.core.config import settings
from app.core.manager import manager
from app.tools.vision import capture_frame
from app.tools.reactive_vision import reactive_vision
from app.tools.odometry import visual_odometry
from app.schemas.prompt import UserPrompt
from app.services.brain import process_ask_robot

router = APIRouter()

# Global camera object for the local USB camera
global_cap = None

@router.post("/ask")
async def ask_robot(user_input: UserPrompt):
    """The main AI endpoint. Handles vision and physical voice."""
    return await process_ask_robot(user_input.prompt)

@router.post("/manual_cmd")
async def manual_cmd(cmd: str):
    """Direct manual override from dashboard buttons."""
    await manager.send_command(cmd)
    return {"status": "sent"}

@router.get("/dashboard", response_class=HTMLResponse)
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

@router.get("/video_feed")
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return StreamingResponse(gen_frames(), media_type='multipart/x-mixed-replace; boundary=frame')

@router.get("/status")
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
