import asyncio
import time
from enum import Enum
from app.core.manager import manager
from app.tools.reactive_vision import reactive_vision
from app.tools.vision import capture_frame
from app.services.brain import process_ask_robot

class MissionState(Enum):
    IDLE = "IDLE"
    EXPLORING = "EXPLORING"
    LOW_BATTERY = "LOW_BATTERY"
    OBSTACLE_DETECTED = "OBSTACLE_DETECTED"
    WORKING = "WORKING"
    CHARGING = "CHARGING"

class AutonomousMissionOrchestrator:
    def __init__(self, manager):
        self.manager = manager
        self.state = MissionState.IDLE
        self.task_queue = []
        self.exploration_interval = 120  # seconds between curiosity scans
        self.battery_threshold = 15.0    # percentage
        self.obstacle_threshold = 20     # cm
        self.last_state_change = time.time()
        self.last_exploration_time = time.time()

    def add_task(self, task_command: str):
        print(f"[AUTONOMY] Task added to queue: {task_command}")
        self.task_queue.append(task_command)

    def get_status(self) -> dict:
        return {
            "state": self.state.value,
            "queue_length": len(self.task_queue)
        }

    def _get_battery_percentage(self) -> float:
        bat = reactive_vision.last_battery
        # If it's a raw voltage (e.g. less than 9.0V), convert to percentage
        if bat < 9.0:
            pct = ((bat - 6.4) / (8.4 - 6.4)) * 100
            return max(0.0, min(100.0, pct))
        return bat

    async def run(self):
        print("[AUTONOMY] Autonomous Mission Orchestrator FSM started.")
        while True:
            try:
                # 1. State Transitions & Safety Priority
                battery_pct = self._get_battery_percentage()
                distance = reactive_vision.last_distance

                # High Priority: Low Battery Check
                if battery_pct < self.battery_threshold and self.state not in (MissionState.LOW_BATTERY, MissionState.CHARGING):
                    print(f"[AUTONOMY] Battery low ({battery_pct:.1f}%). Transitioning to LOW_BATTERY.")
                    self.state = MissionState.LOW_BATTERY
                    self.last_state_change = time.time()

                # High Priority: Obstacle Check (only if moving or working)
                elif distance < self.obstacle_threshold and self.state not in (MissionState.OBSTACLE_DETECTED, MissionState.LOW_BATTERY, MissionState.CHARGING):
                    print(f"[AUTONOMY] Obstacle detected at {distance} cm. Transitioning to OBSTACLE_DETECTED.")
                    self.state = MissionState.OBSTACLE_DETECTED
                    self.last_state_change = time.time()

                # If no urgent states, process tasks or explore
                elif self.state == MissionState.IDLE:
                    if self.task_queue:
                        print("[AUTONOMY] Tasks found in queue. Transitioning to WORKING.")
                        self.state = MissionState.WORKING
                        self.last_state_change = time.time()
                    elif time.time() - self.last_exploration_time > self.exploration_interval:
                        print("[AUTONOMY] Idle interval exceeded. Transitioning to EXPLORING.")
                        self.state = MissionState.EXPLORING
                        self.last_state_change = time.time()

                # 2. Execute State Handler
                if self.state == MissionState.IDLE:
                    await self._handle_idle()
                elif self.state == MissionState.EXPLORING:
                    await self._handle_exploring()
                elif self.state == MissionState.LOW_BATTERY:
                    await self._handle_low_battery()
                elif self.state == MissionState.CHARGING:
                    await self._handle_charging()
                elif self.state == MissionState.OBSTACLE_DETECTED:
                    await self._handle_obstacle()
                elif self.state == MissionState.WORKING:
                    await self._handle_working()

            except Exception as e:
                print(f"[AUTONOMY] Error in state machine loop: {e}")

            await asyncio.sleep(2)

    async def _handle_idle(self):
        # Do nothing, just wait for transition
        pass

    async def _handle_exploring(self):
        print("[AUTONOMY] Exploring state handler active. Capturing frame...")
        try:
            frame = capture_frame()
            if frame is not None:
                print("[AUTONOMY] Frame captured. Querying AI brain for visual observation...")
                await process_ask_robot("Make a visual observation of your surroundings.")
            else:
                print("[AUTONOMY] Frame capture failed.")
        except Exception as e:
            print(f"[AUTONOMY] Error during exploration: {e}")
        finally:
            self.state = MissionState.IDLE
            self.last_exploration_time = time.time()
            self.last_state_change = time.time()

    async def _handle_low_battery(self):
        print("[AUTONOMY] Battery low. Command SUN_SEEK, audio announcement, and sad face.")
        try:
            await self.manager.send_command("CMD:SUN_SEEK")
            await self.manager.send_command("FACE:Sad")
            await self.manager.send_command("SAY:My battery is low, seeking energy source")
        except Exception as e:
            print(f"[AUTONOMY] Error in low battery handler: {e}")
        self.state = MissionState.CHARGING
        self.last_state_change = time.time()

    async def _handle_charging(self):
        # Monitor battery. If it rises above 30%, transition to IDLE
        battery_pct = self._get_battery_percentage()
        print(f"[AUTONOMY] Charging... Current battery: {battery_pct:.1f}%")
        if battery_pct > 30.0:
            print("[AUTONOMY] Battery recovered above 30%. Transitioning to IDLE.")
            try:
                await self.manager.send_command("SAY:Battery recovered")
                await self.manager.send_command("FACE:Happy")
            except Exception as e:
                print(f"[AUTONOMY] Error in charging recovery: {e}")
            self.state = MissionState.IDLE
            self.last_exploration_time = time.time()
            self.last_state_change = time.time()

    async def _handle_obstacle(self):
        print("[AUTONOMY] Handling obstacle: backing away safely.")
        try:
            await self.manager.send_command("CMD:STOP")
            await asyncio.sleep(0.5)
            await self.manager.send_command("CMD:BACKWARD")
            await asyncio.sleep(0.5)
            await self.manager.send_command("CMD:STOP")
        except Exception as e:
            print(f"[AUTONOMY] Error in obstacle handler: {e}")
        self.state = MissionState.IDLE
        self.last_state_change = time.time()

    async def _handle_working(self):
        if not self.task_queue:
            self.state = MissionState.IDLE
            self.last_state_change = time.time()
            return
        
        task = self.task_queue.pop(0)
        print(f"[AUTONOMY] Executing working task: {task}")
        try:
            await self.manager.send_command(task)
        except Exception as e:
            print(f"[AUTONOMY] Error executing working task: {e}")
        
        if not self.task_queue:
            self.state = MissionState.IDLE
            self.last_state_change = time.time()

mission_orchestrator = None

async def autonomous_mission_loop(manager):
    global mission_orchestrator
    mission_orchestrator = AutonomousMissionOrchestrator(manager)
    await mission_orchestrator.run()
