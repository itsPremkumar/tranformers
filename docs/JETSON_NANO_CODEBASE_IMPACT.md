# 🛠️ Jetson Nano Upgrade: Codebase Impact & Migration Checklist

This document details the modifications required across the four primary subsystems of the Omni-Morph framework to support the Nvidia Jetson Nano edge architecture.

---

## 📊 Subsystem Impact Overview

| Subsystem | Impact Level | Action Required |
| :--- | :--- | :--- |
| **`motion_controller`** | **🟡 Minor Changes** | Retain for real-time actuation. Route UART serial pins to the Jetson Nano USB or GPIO UART pins. |
| **`ai_backend`** | **🟠 Major Refactoring** | Migrate backend to run locally on Jetson. Implement PySerial instead of WebSockets. Enable GPU CUDA acceleration. |
| **`comm_controller`** | **🔴 Completely Removed** | Bypassed. OLED display and Max98357A I2S audio are wired directly to Jetson GPIO pins. |
| **`vision_controller`** | **🔴 Completely Removed** | Bypassed. Captured frame inputs are fetched from the local CSI/USB camera path (`/dev/video0`). |

---

## 🔍 Subsystem Details & Refactoring Specifications

### 1. `motion_controller` (ESP32 Firmware) — Minor Changes
* **Role**: High-speed DC motor PWM, S-Curve kinematics, and 100Hz Core 1 FreeRTOS IMU balance loops.
* **Why it is kept**: Linux (Jetson Nano) cannot handle hard real-time motor and servo PWM cycles reliably.
* **Checklist**:
  - [x] Maintain the FreeRTOS IMU task and PID loop structures.
  - [x] Maintain safety-critical immediate bypass pathways (`EMERGENCY_STOP`, `STOP`, `FALL_RECOVERY`).
  - [ ] Connect the Hardware Serial TX2/RX2 pins (GPIO 17/16) to the CP2102 USB-to-TTL UART bridge plugged into the Jetson Nano.

### 2. `ai_backend` (Python / FastAPI Backend) — Major Refactoring
* **Role**: High-level FSM mission orchestrator, RAG memory vault (ChromaDB), computer vision, and local AI interface.
* **Checklist**:
  - [ ] **GStreamer camera integration**: Update the frame reader inside `app/tools/vision.py` to capture frames via local CSI camera hardware pipeline.
  - [ ] **PySerial link**: Implement the `SerialLinkManager` to replace WebSockets. Start a background loop on application boot to monitor serial lines.
  - [ ] **Local AI model execution**: Set up local Ollama models on the Jetson Nano Ubuntu OS.
  - [ ] **CUDA optimization**: Build OpenCV and MediaPipe with CUDA support to accelerate vision processing on the 128-core GPU.

### 3. `comm_controller` (ESP32 Gateway) — Completely Removed
* **Role**: Wi-Fi/4G client, network healing, OLED face animations, and I2S text-to-speech.
* **Why it is removed**: The Jetson Nano is a full single-board computer that manages Wi-Fi, cellular, I2C displays, and audio natively.
* **Checklist**:
  - [ ] Wire the SSD1306 OLED display directly to Jetson Nano I2C pins. Drive it via the Python `luma.oled` library.
  - [ ] Wire the Max98357A Audio Amp directly to the Jetson Nano I2S GPIO pins. Play local audio clips and run TTS models on the Nano.

### 4. `vision_controller` (ESP32-CAM) — Completely Removed
* **Role**: Low-resolution, high-latency MJPEG Wi-Fi stream.
* **Why it is removed**: Low frame rate and Wi-Fi streaming latency make real-time target navigation unsafe.
* **Checklist**:
  - [ ] Discard the ESP32-CAM module.
  - [ ] Connect a Sony IMX219 CSI camera or USB Web Camera directly to the Jetson Nano.
