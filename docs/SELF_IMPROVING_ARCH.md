
# 🧬 THE SELF-IMPROVING ROBOT ARCHITECTURE

This document explains the "Autonomous Evolution" system of the Omni-Morph robot. It allows the robot to analyze its own performance and receive wireless code upgrades automatically.

## 1. The Autonomous Evolution Loop
The system follows a 4-step cycle that never stops:

1.  **DATA COLLECTION**: The robot sends high-speed telemetry (Gyro, Battery, Stall Current, Vision frames) to the AI Backend.
2.  **BEHAVIOR ANALYSIS**: The AI reviews the logs. It looks for patterns like: *"The robot keeps falling when turning left at 40% speed."*
3.  **CODE OPTIMIZATION**: An **Autonomous Coding Agent (Antigravity/Claude Code)** analyzes the diagnosis and generates a physical code fix (e.g., adjusting the servo center of gravity or slowing down the pivot).
4.  **WIRELESS DEPLOYMENT**: The Agent uses the **OTA (Over-The-Air)** system or PlatformIO CLI to flash the new, improved code while the robot is still standing.

---

## 2. Intelligence Modules

### A. The "Log-to-Code" Bridge
*   **How it works**: Every error message seen in the **Wireless Serial Monitor** is parsed by the AI. 
*   **Example**: If the log shows `[I2C] Error: Bus Busy`, the AI automatically modifies the `systemMgr.i2cRecovery()` logic to be more aggressive and pushes the update wirelessly.

### B. Heuristic Terrain Adaptation
*   **How it works**: The Motion Controller records the "Roughness" of the terrain using the MPU6050.
*   **Self-Improvement**: If the robot detects it is on grass (high vibration), the AI Backend sends a command to permanentely update the **Config.h** walking gait to be wider and more stable.

### C. Vision-Latency Optimization
*   **How it works**: The AI Backend measures the delay between a frame being captured and a command being executed.
*   **Self-Improvement**: If latency is high, the AI tells the **Vision Controller** to lower the resolution or increase the clock speed wirelessly via an OTA update.

---

## 3. Automated Bug-Fixing Pipeline
When a bug is found, the system performs an **Automated Surgery**:

1.  **Isolation**: The AI finds the exact file (e.g., `ServoControl.cpp`) and the exact line causing the issue.
2.  **Refactoring**: The AI rewrites the function using modern C++ standards to save memory or increase speed.
3.  **Validation**: A virtual "PlatformIO Build" is triggered. If it compiles, it moves to the next step.
4.  **Silent Flash**: The robot receives the update. If the new code crashes, the **Hardware Watchdog** triggers a "Rollback" to the previous stable version.

---

## 4. Autonomous Agent Integration (The "Engineer in the Machine")
An **Autonomous Coding Agent (Antigravity/Claude Code)** is integrated into this architecture as the **Firmware Engineer**:
*   **Real-time Debugging**: The Agent monitors the wireless serial output to catch bugs the moment they happen.
*   **Repo-Wide Intelligence**: The Agent can read the entire repository at once to ensure a change in the "Brain" doesn't break the "Legs."
*   **Tool-Chain Mastery**: It uses **PlatformIO** to manage dependencies and flash hardware automatically.
*   **Documentation Sync**: It maintains the **Master System Guide** so the documentation is always as "smart" as the code.

---

**This architecture ensures that your robot gets smarter and more stable the more you use it.**

**Would you like me to set up a "Deep Learning" task in the backend that specifically tries to optimize the robot's battery life?**

---

## 5. Technical Implementation Details (Advanced)
These details represent the active implementation in the current firmware stack as of May 2026.

### A. Hardware Self-Healing (Active)
*   **I2C Bus Recovery**: The `systemMgr.i2cRecovery()` logic actively monitors for SCL/SDA hang-ups. If the MPU6050 or OLED becomes unresponsive, the robot performs an automated bus-clear sequence to restore communication without a full system reboot.
*   **Vision Watchdog**: The Vision Controller monitors frame capture success. If the sensor freezes (detected via `capture_failures > 5`), the controller triggers a hardware `ESP.restart()` specifically for the camera module while the Communication module maintains the link.

### B. Network-Aware Vision Intelligence
*   **SSID Auto-Detection**: The Vision Controller detects the `Omni-Gateway` (4G LTE Hotspot) vs. standard Home WiFi.
*   **Adaptive Quality**: When on 4G, it automatically throttles to `CIF` resolution and reduces JPEG quality to 15 to minimize latency. It restores `SVGA` and quality 10 when a high-bandwidth WiFi link is restored.

### C. Safety-First Wireless Deployment
*   **OTA State Interlocks**: The Motion Controller implements a safety check during OTA updates. It will **reject** or delay an incoming flash if the robot is in a `WALK` or `AVOID` state, ensuring it is only updated when in a stable `STAND` or `CAR` position.
*   **ESP-NOW Credentials Sync**: To prevent "Wireless Brick" scenarios, the Communication Controller uses **ESP-NOW** to broadcast WiFi credentials to the sub-controllers (Vision & Motion). This ensures that if the robot is moved to a new network, all modules update their connections simultaneously.

### D. Hardware Watchdog & Rollback
*   **ESP-Task-WDT**: All microcontrollers are protected by a 5-10 second hardware watchdog. 
*   **Rollback Mechanism**: If a new firmware update contains a logic loop that blocks the main task, the watchdog triggers a hardware reset, effectively "rolling back" the system to a clean boot state.
