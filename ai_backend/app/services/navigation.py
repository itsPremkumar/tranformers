import asyncio
from app.core.manager import manager
from app.tools.reactive_vision import reactive_vision

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
