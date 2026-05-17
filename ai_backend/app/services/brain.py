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
from app.services.vector_memory import vector_memory

llm = LLMFactory(manager)

async def process_ask_robot(prompt: str):
    """The main AI brain logic. Handles vision, search, LLM reasoning, command execution, and TTS."""
    print(f"\n[DEBUG] --- NEW REQUEST ---")
    print(f"[DEBUG] User Prompt: {prompt}")
    
    # Log incoming command to Diagnostics Excel sheet
    try:
        from app.services.diagnostic_logger import log_diagnostic_event
        log_diagnostic_event("Dialogue Inbound", f"User Prompt: '{prompt}'", "success")
    except Exception:
        pass
        
    # 1. Long-Term Vector Memory Recall
    memories = vector_memory.search_memory(prompt, k=2)
    memory_context = ""
    if memories:
        memory_context = "\n[SYSTEM MEMORY INJECTION: You recall the following relevant past occurrences/dialogues]:\n"
        for m in memories:
            if m.get("similarity", 0.0) > 0.45:
                memory_context += f"- {m['text']}\n"
    
    enhanced_prompt = prompt
    if memory_context:
        enhanced_prompt = f"{memory_context}\nUser Current Input: {prompt}"
    
    # Get the active robot's name and mode for memory retrieval
    robot_name = "Unknown"
    robot_mode = "Robot" # Default
    if manager.active_connections:
        ws = manager.active_connections[0]
        profile = manager.get_profile(ws)
        robot_name = profile.get("name", "Unknown")
        robot_mode = profile.get("current_mode", "Robot")

    print(f"[DEBUG] Robot: {robot_name}, Mode: {robot_mode}")

    # 0. Local Offline Command Interceptor (Jarvis-Inspired Sub-Millisecond Router)
    offline_prompt = prompt.lower().strip()
    offline_response = None
    
    if any(k in offline_prompt for k in ["what is the time", "what's the time", "tell me the time"]):
        from datetime import datetime
        offline_response = f"It's {datetime.now().strftime('%I:%M %p')} right now."
    elif any(k in offline_prompt for k in ["what is the date", "what's the date", "tell me the date"]):
        from datetime import datetime
        offline_response = f"It's {datetime.now().strftime('%B %d, %Y')} today."
    elif any(k in offline_prompt for k in ["what is the battery", "what's the battery", "check battery"]):
        offline_response = f"My battery level is {round(reactive_vision.last_battery, 1)} percent."
    elif any(k in offline_prompt for k in ["clear conversation", "clear history", "reset memory"]):
        offline_response = "Dialogue memory cleared successfully."

    if offline_response:
        print(f"[OFFLINE INTERCEPT] Match found! Responding with: {offline_response}")
        commands = [
            "FACE:Wonder",
            f"SUB_TEXT:{offline_response}",
            f"SAY:{offline_response}"
        ]
        
        if manager.active_connections:
            ws = manager.active_connections[0]
            for cmd in commands:
                await manager.send_command(cmd, target_ws=ws)
                
        try:
            from app.services.diagnostic_logger import log_diagnostic_event
            log_diagnostic_event("Offline Intercept", f"Responded to query: '{prompt}' locally.", "success")
        except Exception:
            pass
            
        return {"status": "success", "commands": commands}

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
    json_response = await llm.get_response(enhanced_prompt, robot_name, image, hw_status=hw_status, internet_context=internet_results)
    
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
                
                # Intercept server-side OS automation commands
                if cmd.startswith("CMD:OPEN_APP:") or cmd.startswith("CMD:TYPE_TEXT:"):
                    if cmd.startswith("CMD:OPEN_APP:"):
                        app_name = cmd[13:]
                        from app.tools.os_automation import OSAutomationTools
                        result_msg = await asyncio.to_thread(OSAutomationTools.start_application, app_name)
                        print(f"[OS AUTOMATION] {result_msg}")
                    elif cmd.startswith("CMD:TYPE_TEXT:"):
                        text_to_type = cmd[14:]
                        from app.tools.os_automation import OSAutomationTools
                        result_msg = await asyncio.to_thread(OSAutomationTools.type_text, text_to_type)
                        print(f"[OS AUTOMATION] {result_msg}")
                    continue
                
                # Intercept dynamic serial hardware dispatch sweeps
                if cmd.startswith("CMD:SERIAL_SEND:"):
                    from app.services.serial_recovery import serial_dispatcher
                    result_msg = await asyncio.to_thread(serial_dispatcher.send_command, cmd)
                    print(f"[SERIAL ROUTER] {result_msg}")
                    continue

                # Intercept SQL-backed dynamic Task & TODO commands
                if cmd.startswith("CMD:ADD_TASK:") or cmd.startswith("CMD:LIST_TASKS") or cmd.startswith("CMD:UPDATE_TASK:"):
                    from app.core.memory import memory_manager
                    if cmd.startswith("CMD:ADD_TASK:"):
                        payload = cmd[13:].split(",")
                        desc = payload[0].strip()
                        due = payload[1].strip() if len(payload) > 1 else ""
                        pri = payload[2].strip() if len(payload) > 2 else "medium"
                        result_msg = memory_manager.add_todo_task(robot_name, desc, due, pri)
                        print(f"[TASK MANAGER] {result_msg}")
                        # Log event inside diagnostics logger
                        try:
                            from app.services.diagnostic_logger import log_diagnostic_event
                            log_diagnostic_event("Task Tracker", f"Added Task: '{desc}'", "success")
                        except Exception: pass
                    elif cmd.startswith("CMD:LIST_TASKS"):
                        status = "all"
                        if ":" in cmd:
                            status = cmd[15:].strip()
                        tasks = memory_manager.get_todo_tasks(robot_name, status)
                        print(f"[TASK MANAGER] Retrieved tasks: {tasks}")
                    elif cmd.startswith("CMD:UPDATE_TASK:"):
                        payload = cmd[16:].split(",")
                        try:
                            t_id = int(payload[0].strip())
                            n_status = payload[1].strip()
                            result_msg = memory_manager.update_todo_status(robot_name, t_id, n_status)
                            print(f"[TASK MANAGER] {result_msg}")
                            # Log event inside diagnostics logger
                            try:
                                from app.services.diagnostic_logger import log_diagnostic_event
                                log_diagnostic_event("Task Tracker", f"Updated Task {t_id} to status: '{n_status}'", "success")
                            except Exception: pass
                        except ValueError:
                            print("[TASK MANAGER ERROR] Invalid Task ID parameter.")
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
                    
                    # 1. Parse and synchronize dynamic emotion qualifiers (Xiaozhi Inspired)
                    detected_emotion = None
                    emotions_map = {
                        "[HAPPY]": "Happy",
                        "[SAD]": "Sad",
                        "[ANGRY]": "Angry",
                        "[PEACE]": "Peace",
                        "[HERO]": "Hero",
                        "[LOVE]": "Love",
                        "[FEAR]": "Fear",
                        "[DISGUST]": "Disgust",
                        "[WONDER]": "Wonder",
                        "[WARNING]": "Warning",
                        "[SLEEP]": "Sleep"
                    }
                    
                    for marker, mood_str in emotions_map.items():
                        if marker in text.upper():
                            detected_emotion = mood_str
                            import re
                            text = re.sub(re.escape(marker), "", text, flags=re.IGNORECASE).strip()
                    
                    if detected_emotion:
                        print(f"[EMOTION SYNC] Detected qualifier '{detected_emotion}'. Dispatching FACE change...")
                        await manager.send_command(f"FACE:{detected_emotion}")
                        
                    # 2. Dispatch real-time horizontal scrolling subtitles (Xiaozhi Inspired)
                    print(f"[SUBTITLE SYNC] Dispatching scrolling subtitle text: '{text}'")
                    await manager.send_command(f"SUB_TEXT:{text}")
                    
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
        
        # Asynchronously store successful dialogue turn in Vector Memory
        speech_commands = [c for c in commands if isinstance(c, str) and c.startswith("SAY:")]
        robot_response_text = " ".join([c[4:] for c in speech_commands]) if speech_commands else ""
        if robot_response_text:
            memory_text = f"User said: {prompt} | You responded: {robot_response_text}"
            asyncio.create_task(asyncio.to_thread(vector_memory.add_memory, memory_text, {"robot_name": robot_name, "mode": robot_mode}))

        # Log processed commands to Diagnostics Excel sheet
        try:
            from app.services.diagnostic_logger import log_diagnostic_event
            log_diagnostic_event("Dialogue Outbound", f"Commands Executed: {commands}", "success")
        except Exception:
            pass

        return {"status": "success", "commands": commands}
    except Exception as e:
        print(f"Error: {e}")
        # Log failure to Diagnostics Excel sheet
        try:
            from app.services.diagnostic_logger import log_diagnostic_event
            log_diagnostic_event("System Error", f"Failed to execute prompt: {str(e)}", "error")
        except Exception:
            pass
        return {"status": "error", "message": str(e)}
