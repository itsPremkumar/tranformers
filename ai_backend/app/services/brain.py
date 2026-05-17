import json
import asyncio
from app.core.manager import manager
from app.core.llm_factory import LLMFactory
from app.tools.vision import capture_frame
from app.tools.audio import generate_tts_pcm
from app.tools.reactive_vision import reactive_vision
from app.tools.odometry import visual_odometry
from app.tools.solar import analyze_brightness
from app.services.navigation import approach_target

llm = LLMFactory(manager)

async def process_ask_robot(prompt: str):
    """The main AI brain logic. Handles vision, search, LLM reasoning, command execution, and TTS."""
    print(f"\n[DEBUG] --- NEW REQUEST ---")
    print(f"[DEBUG] User Prompt: {prompt}")
    
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
    if any(k in prompt.lower() for k in swarm_keywords):
        print(f"[DEBUG] SWARM REASONING ACTIVATED for: {prompt}")
        from app.tools.deep_thinking import run_swarm_reasoning
        # Run the full swarm logic and return directly, skipping the standard short-loop
        commands = await run_swarm_reasoning(prompt, manager, llm, robot_name, None)
        return {"status": "success", "commands": commands}

    image = None
    # Smart Vision Trigger: Capture frame if the prompt implies looking at something
    visual_keywords = ["see", "look", "watch", "camera", "describe", "identify", "detect", "in front of"]
    if any(k in prompt.lower() for k in visual_keywords):
        print(f"[DEBUG] Vision Triggered. Capturing frame...")
        image = capture_frame()
        print(f"[DEBUG] Image Captured: {'Success' if image else 'Failed'}")
    
    # Smart Internet Trigger: Search the web if the prompt implies needing current info
    internet_results = None
    deep_keywords = ["deep research", "browser research", "research deeply", "deep search", "learn about"]
    search_keywords = ["search", "google", "weather", "news", "who is", "what is the price", "latest"]
    
    if any(k in prompt.lower() for k in deep_keywords):
        from app.tools.deep_research import run_research_subprocess
        print(f"[DEBUG] Playwright Deep Research Triggered. Scrapping: {prompt}")
        internet_results = await run_research_subprocess(prompt)
        print(f"[DEBUG] Deep Research Results Length: {len(internet_results) if internet_results else 0}")
    elif any(k in prompt.lower() for k in search_keywords):
        from app.tools.internet import web_search
        print(f"[DEBUG] Internet Search Triggered. Searching for: {prompt}")
        internet_results = web_search(prompt)
        print(f"[DEBUG] Internet Results Length: {len(internet_results) if internet_results else 0}")

    # Collect Hardware Status
    hw_status = {
        "battery": round(reactive_vision.last_battery, 1),
        "distance": reactive_vision.last_distance,
        "mode": robot_mode
    }

    # Hybrid Command Dispatcher (Ensures reliability for critical hardware tasks)
    hybrid_commands = []
    if any(k in prompt.lower() for k in ["waste", "trash", "garbage"]):
        hybrid_commands.append("CMD:COLLECT_WASTE")
    if any(k in prompt.lower() for k in ["follow", "track me", "look at me"]):
        hybrid_commands.append("CMD:FOLLOW")
    if "play" in prompt.lower():
        # Extrapolate song name for the playback tool
        query = prompt.lower().split("play")[-1].replace("on youtube", "").replace("song", "").strip()
        hybrid_commands.append(f"SAY:Playing '{query}' on YouTube.")

    print(f"[DEBUG] Requesting LLM Response...")
    json_response = await llm.get_response(prompt, robot_name, image, hw_status=hw_status, internet_context=internet_results)
    
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
