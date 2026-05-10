# 🤖 Omni-Morph Robot - Theoretical Real-Life Blueprint (Open Source)

This project is a **theoretical version** and technical blueprint for creating **real-life transformation robots**. It combines modular robotics, distributed multi-core processing, and advanced AI "Super-Brain" logic to bridge the gap between science fiction and physical reality. 

[![Python Lint & Test](https://github.com/itsPremkumar/tranformers/actions/workflows/python-app.yml/badge.svg)](https://github.com/itsPremkumar/tranformers/actions/workflows/python-app.yml)
[![Security Policy](https://img.shields.io/badge/Security-Policy-blue.svg)](./SECURITY.md)

**This is an open-source project** dedicated to the advancement of modular autonomous agents.

## 🌟 Key Features

*   **Dynamic Transformation**: Seamless mechanical transition between **Humanoid** (Walking/Interaction) and **4WD Car** (High-speed Mobility) modes.
*   **AI Super-Brain (Cognitive Layer)**: High-level reasoning powered by Gemini 1.5 Pro/Flash and local Ollama (Llama 3), enabling complex conversation and physical decision-making.
*   **Advanced Vision Intelligence**: 
    *   **Reactive Vision**: Face, ball, and waste tracking using OpenCV.
    *   **Gesture Recognition**: MediaPipe-based hand signal control (Silent interaction).
    *   **Visual SLAM**: Basic odometry using Optical Flow for movement estimation.
*   **distributed Tri-Core Architecture**: 
    *   **Motion Controller**: Real-time gait, servo orchestration (PCA9685), and IMU-based balance.
    *   **Communication Controller**: Web-based remote control, 4G LTE fallback (SIM7600), and OLED facial expressions.
    *   **Vision Controller**: Low-latency FPV MJPEG streaming.
*   **Physical Voice & Audio**: Real-time I2S Audio streaming for AI text-to-speech, allowing the robot to speak through its physical body.
*   **Safety & Health**: Integrated battery monitoring, over-current protection, and fall detection.

## 📁 Project Structure

*   **[`ai_backend/`](./ai_backend/)**: The Python-based "Super-Brain". Handles LLM integration, vision processing, and coordinates the hardware via WebSockets.
*   **[`motion_controller/`](./motion_controller/)**: ESP32 firmware for physical actuation, PCA9685 driving, and IMU stabilization.
*   **[`comm_controller/`](./comm_controller/)**: ESP32 gateway for networking (Wi-Fi/4G), I2S audio, and OLED UI.
*   **[`vision_controller/`](./vision_controller/)**: ESP32-CAM MJPEG server for remote visual feedback.

## 🧠 AI Super-Brain (Cognitive Layer)

The robot is powered by a FastAPI-based backend that provides "consciousness":
- **Multi-Model Support**: Dynamically switches between Gemini (Cloud) and Ollama (Local).
- **Persistent Memory**: SQLite-backed memory "vaults" for unique robot personalities (e.g., Omni-Core, Yellow-Stinger).
- **Proactive Engagement**: The robot can initiate conversations based on visual observations.
- **Autonomous Navigation**: Logic to approach targets (like a ball or waste) for physical interaction.

## 🛠️ Hardware Stack

*   **Processors**: 2x ESP32 DevKit V1, 1x ESP32-CAM.
*   **Actuators**: MG996R/DS3218 High-Torque Servos, 12V Geared DC Motors.
*   **Drivers**: PCA9685 (16-Ch PWM), L298N (H-Bridge).
*   **Sensors**: MPU6050 (IMU), HC-SR04 (Ultrasonic), INMP441 (I2S Mic).
*   **Audio/Display**: MAX98357A (I2S Amp), SSD1306 OLED.
*   **Network**: SIM7600G-H 4G Module.

## 🚀 Getting Started

1.  **AI Backend**: Navigate to `ai_backend/`, install dependencies from `requirements.txt`, and run `python app/main.py`.
2.  **Hardware Configuration**: Update Wi-Fi and API keys in `Config.h` and `.env` files.
3.  **Deployment**: Flash the ESP32 modules using PlatformIO.
4.  **Wiring**: Refer to [**electronic.md**](./docs/electronic.md) for master wiring schematics.

## 📖 Documentation

### 🚀 Core Guides
*   📋 [**Project Summary**](./docs/COMPLETE_PROJECT_SUMMARY.md): Master overview of the entire build.
*   📐 [**3D Model Quick Start**](./docs/COMPLETE_3D_MODEL_QUICK_START.md): Immediate steps for CAD design.
*   📘 [**Technical Documentation**](./docs/docs.md): Deep dive into protocols and architecture.
*   🦾 [**Omni-Morph Build Guide**](./docs/README.md): Step-by-step instructions for hardware.
*   ⚡ [**Electronics Guide**](./docs/electronic.md): Master wiring and power.
*   📋 [**Components List**](./docs/list.md): Detailed BOM for fabrication.

### 🧠 Advanced AI & Interaction
*   🧠 [**AI Super-Brain**](./docs/ai_super_brain.md): LLM logic, memory, and internet tools.
*   🛡️ [**Diagnostics & Safety**](./docs/diagnostics_and_safety.md): Test suites and emergency protocols.
*   👋 [**Multimodal Interaction**](./docs/multimodal_interaction.md): Vision, voice, and gesture control.


## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please see [**CONTRIBUTING.md**](./CONTRIBUTING.md) for guidelines.

## ⚠️ Safety Disclaimer

This project involves high-torque motors, high-current power systems, and moving mechanical parts. 
- **Use at your own risk.** The authors are not responsible for any damage to hardware or personal injury.
- Always test servos without mechanical load first.
- Ensure proper cable management to avoid shorts.
- Use a dedicated power supply for motors to avoid frying the logic controllers.

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---
*Built for the next generation of modular robotics. This project is a contribution to the open-source community to make real-life transformation robots a reality.*


