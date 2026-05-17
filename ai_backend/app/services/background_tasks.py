import json
import asyncio
import os
import datetime
import schedule
from app.core.manager import manager
from app.core.llm_factory import LLMFactory
from app.tools.vision import capture_frame
from app.services.brain import process_ask_robot

try:
    from app.tools.voice_assistant import voice_assistant
    VOICE_ENABLED = True
except Exception as e:
    print(f"[VOICE] Voice Assistant disabled (Missing dependencies or model): {e}")
    VOICE_ENABLED = False

llm = LLMFactory(manager)

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
            await process_ask_robot(text)
            
        except Exception as e:
            print(f"[VOICE] Loop Error: {e}")
            await asyncio.sleep(1)

# --- Threaded Swarm Scheduler Engine ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULER_FILE = os.path.join(BASE_DIR, "data", "scheduler.json")

def get_scheduler_tasks():
    """Retrieve schedule items or generate template defaults."""
    if not os.path.exists(SCHEDULER_FILE):
        os.makedirs(os.path.dirname(SCHEDULER_FILE), exist_ok=True)
        default_schedule = [
            {"id": 1, "time": "09:00", "prompt": "SAY:Good morning. Commencing daily hardware diagnostics.", "status": "active"},
            {"id": 2, "time": "14:00", "prompt": "CMD:SUN_SEEK", "status": "active"},
            {"id": 3, "time": "22:00", "prompt": "SAY:Night cycle active. Entering low-power sleep mode.", "status": "active"}
        ]
        try:
            with open(SCHEDULER_FILE, 'w') as f:
                json.dump(default_schedule, f, indent=4)
        except Exception as e:
            print(f"[SCHEDULER ERROR] Failed to save default schedule: {e}")
        return default_schedule
    try:
        with open(SCHEDULER_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[SCHEDULER ERROR] Failed to read schedule: {e}")
        return []

async def trigger_scheduled_item(prompt: str):
    """Execute scheduled tasks through the cognitive brain flow."""
    print(f"\n[SCHEDULER EVENT] Triggering timed execution: '{prompt}'")
    
    # Log event inside Diagnostics Excel sheet
    try:
        from app.services.diagnostic_logger import log_diagnostic_event
        log_diagnostic_event("Scheduler", f"Executed scheduled prompt: '{prompt}'", "success")
    except Exception:
        pass
        
    await process_ask_robot(prompt)

async def swarm_scheduler_loop():
    """Background loop that schedules and executes daily routines."""
    print("[SCHEDULER] Swarm Scheduler Loop started.")
    
    # Initialize daily tasks
    tasks = get_scheduler_tasks()
    for task in tasks:
        if task.get("status") == "active" and "time" in task:
            t_time = task["time"]
            prompt = task["prompt"]
            # Register using thread-safe executor callbacks
            schedule.every().day.at(t_time).do(
                lambda p=prompt: asyncio.create_task(trigger_scheduled_item(p))
            )
            print(f"[SCHEDULER] Registered daily task at {t_time}: '{prompt}'")

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)
