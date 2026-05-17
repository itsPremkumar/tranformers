import json
import asyncio
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
