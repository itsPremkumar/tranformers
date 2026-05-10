# 🤖 Transformer Robot – Technical Documentation

This document provides a deep dive into the system architecture, software logic, and communication protocols of the Transformer Robot.

---

## 🧠 1. System Architecture

The robot utilizes a **Distributed Controller Pattern**. This separates high-current motor tasks from sensitive communication and vision processing.

### 🎛️ Motion Controller (ESP32)
*   **Purpose**: Physical actuation and real-time sensor processing.
*   **Key Responsibilities**:
    *   Servo orchestration via PCA9685 (14-18 servos).
    *   DC motor control via L298N (Car mode).
    *   IMU processing (MPU6050) for fall detection and pitch stabilization.
    *   Autonomous avoidance using Ultrasonic scanning.

### 📡 Communication Controller (ESP32)
*   **Purpose**: Gateway for user interaction and sensory feedback.
*   **Key Responsibilities**:
    *   Hosting the **WebSocket & HTTP Web Server**.
    *   Managing connectivity fallback (Wi-Fi ↔ 4G LTE).
    *   Rendering facial expressions on the SSD1306 OLED.
    *   Handling I2S Audio input/output.

### 👁️ Vision Controller (ESP32-CAM)
*   **Purpose**: Low-latency video streaming.
*   **Key Responsibilities**:
    *   Serving an MJPEG stream on Port 80.
    *   Direct FPV access via browser.

---

## 📡 2. Communication Protocol (Inter-ESP32)

The Comm and Motion controllers communicate via a dedicated **UART Serial Link** (115,200 Baud).

### Control Commands (Comm ➡️ Motion)
Commands are text-based strings terminated by a newline (`\n`).

| Command | Action |
| :--- | :--- |
| `CMD:FORWARD` | Move forward (Car/Walk based on state) |
| `CMD:BACKWARD`| Move backward |
| `CMD:LEFT`    | Turn left |
| `CMD:RIGHT`   | Turn right |
| `CMD:STOP`    | Halt all movement |
| `CMD:TRANSFORM`| Trigger mechanical transformation sequence |
| `CMD:AUTO`    | Enable autonomous obstacle avoidance mode |
| `PAN:X`       | Set head pan angle to X degrees |
| `TILT:X`      | Set head tilt angle to X degrees |
| `CMD:TEST`    | Trigger hardware self-test diagnostic |
| `BEAT`        | System heartbeat (sent every 1 second) |

### Status Feedback (Motion ➡️ Comm)
The Motion controller occasionally sends status updates or diagnostic results (e.g., `[PASS] MPU6050 Found`).

---

## 🛡️ 3. Safety & Diagnostic Logic

### 💓 Heartbeat Mechanism
To prevent "runaway" robot scenarios if communication fails:
1.  Comm Controller sends `BEAT` every 1000ms.
2.  Motion Controller monitors the link.
3.  If no command (including `BEAT`) is received for **2500ms**, the robot automatically enters `STATE_STAND` and stops all motors.

### 🚨 Fall Detection
The `Balance` module continuously monitors the MPU6050. If a pitch or roll angle exceeds a critical threshold, it triggers an emergency stop to protect the servo gears from impact.

### 🔍 Hardware Self-Test (`CMD:TEST`)
Initiates a comprehensive check:
*   I2C Bus scan for PCA9685 and MPU6050.
*   Ultrasonic range validation.
*   Head servo sweep.
*   Short motor burst with IMU verification (checks if robot actually moved).

---

## 💻 4. Core Software Modules

### Motion Controller
*   **`ServoControl`**: Uses a non-blocking sequence generator for smooth transformation.
*   **`MotorControl`**: Implements PWM speed ramping for the L298N.
*   **`ObstacleAvoidance`**: A state machine that handles scanning, hole detection (ground distance > 45cm), and pathfinding.

### Communication Controller
*   **`NetworkManager`**: Implements a priority-based connection logic (Wi-Fi preferred, LTE fallback).
*   **`WebInterface`**: Served from SPIFFS/Flash. Uses WebSockets for low-latency directional control.
*   **`DisplayController`**: An animation engine for the OLED, handling blinking and mood transitions.

---

## 🌐 5. Web Interface (Remote Control)

Access the control dashboard by navigating to the Comm Controller's IP address.
*   **Default Port**: 80
*   **Control Method**: Virtual Joystick and Action Buttons.
*   **Visual Feedback**: Real-time RSSI signal strength and battery status (if hardware supported).

---

## 🏁 6. Deployment Workflow

1.  **Configure**: Set credentials in `Config.h`.
2.  **Compile**: Use PlatformIO.
3.  **Calibrate**: Use the `standPosition()` command during first boot to verify servo offsets.
4.  **Monitor**: Use the Serial Monitor to observe diagnostic output during the `CMD:TEST` sequence.

---

## 🧠 7. AI Super-Brain (Cognitive Layer)

The robot is powered by a high-level Python backend that provides "consciousness" to the hardware.

### 🧩 Modular Architecture
The brain is organized into specialized modules:
*   **`app/core/llm_factory.py`**: A multi-provider engine that switches between **Gemini**, **GPT-4**, **Claude**, and local **Ollama**.
*   **`app/core/memory.py`**: A SQLite-backed persistent memory system that stores unique "souls" for different robots.
*   **`app/core/manager.py`**: Handles real-time WebSocket communication and robot identity handshakes.

### 🔄 Hybrid Processing
The brain uses **Hybrid AI logic**:
1.  **Cloud Primary**: Uses Gemini 1.5 Flash for complex vision and reasoning.
2.  **Local Fallback**: Automatically switches to **Ollama (Llama 3)** if internet connectivity is lost.

---

## 👁️ 8. Reactive Vision & Tracking

The robot features a real-time vision system that bridges the camera feed with the gimbal servos.

### 🎯 Local Face Tracking
*   **Engine**: OpenCV running in the Python backend.
*   **Logic**: Detects faces locally and calculates the center-offset.
*   **Actuation**: Sends high-frequency `PAN` and `TILT` commands to the robot to keep the target centered.

### 🛡️ Ultrasonic Fusion
*   **Safety**: The live distance from the ultrasonic sensor is streamed back to the brain.
*   **Collision Avoidance**: If the robot is in "Follow Mode" and the distance drops below **20cm**, an emergency `CMD:STOP` is triggered.

---

## 🗣️ 9. Physical Voice (Local TTS)

The robot speaks through its physical body using **I2S Audio Streaming**.

### 🎤 Process Flow
1.  **Text Generation**: AI generates a response string.
2.  **Audio Synthesis**: Backend converts text to **16kHz Raw PCM** using `gTTS` and `pydub`.
3.  **Streaming**: Binary packets are sent over WebSocket.
4.  **Playback**: The ESP32 receives bytes and pipes them to the `i2s_write` buffer for the speaker.
5.  **Sync**: The OLED face plays a talking animation specifically during audio transmission.

---

## 💾 10. Multi-Robot Memory Vaults

To support different robot models (Sentinel Prime, Bumblebee, etc.), the system uses **Isolated Persistence**:
*   **Key**: Memories are indexed by the `ROBOT_NAME` sent during handshake.
*   **Recall**: The AI retrieves the last 5 conversation exchanges for that specific robot.
*   **Identity**: Each robot remembers its own persona, history, and user-specific facts across reboots.

---

## 🛡️ 12. Advanced Autonomous Intelligence (Pro-Grade)

The robot ecosystem has been upgraded with "High-End" autonomous capabilities that simulate professional robotic behavior.

### 👋 12.1 Gesture Recognition
*   **Engine**: Google MediaPipe Hand Tracking.
*   **Function**: The robot understands physical hand signals.
    *   **Open Palm (5 Fingers)**: Triggers an immediate `CMD:STOP`.
    *   **Point (Index Finger)**: Triggers `CMD:FORWARD`.
*   **Benefit**: Allows for silent, non-verbal interaction with the robot.

### 🔋 12.2 Energy & Hardware Health
*   **Battery Management**: Real-time voltage monitoring with automated verbal alerts when power drops below 15%.
*   **Over-Current Protection**: The backend monitors Amperage spikes. If a motor jams or a leg hits an obstacle, the system triggers an emergency stop to protect the servo gears and electronics.

### 🗺️ 12.3 Visual SLAM (Optical Flow)
*   **Mechanism**: Uses Farneback Optical Flow to track pixel displacement between camera frames.
*   **Function**: Estimates how many "robot-steps" have been taken and in which direction.
*   **Benefit**: Provides a subconscious sense of movement even without high-end LIDAR sensors.

---

## 🏁 13. Project Status: V1.0 COMPLETE
The Transformer Robot is now a fully autonomous physical agent with vision, voice, memory, and reactive intelligence.

