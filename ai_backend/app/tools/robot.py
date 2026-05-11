from app.core.manager import manager

async def move_robot(direction: str):
    """Moves the robot (FORWARD, BACKWARD, LEFT, RIGHT, STOP, LEFT_PIVOT, RIGHT_PIVOT, LEFT_PIVOT_BACK, RIGHT_PIVOT_BACK, LEFT_ZERO, RIGHT_ZERO)."""
    print(f"[ACTION] Robot Move: {direction}")
    await manager.send_command(f"CMD:{direction.upper()}")
    return f"Robot is now moving {direction}."

async def set_camera_gimbal(pan: int, tilt: int):
    """Sets camera servos (0-180)."""
    print(f"[ACTION] Camera: Pan={pan}, Tilt={tilt}")
    await manager.send_command(f"PAN:{pan}")
    await manager.send_command(f"TILT:{tilt}")
    return f"Camera positioned at Pan:{pan}, Tilt:{tilt}."

async def transform_robot():
    """Triggers transformation sequence."""
    print(f"[ACTION] Triggering Transformation")
    await manager.send_command("CMD:TRANSFORM")
    return "Initiating transformation sequence."
