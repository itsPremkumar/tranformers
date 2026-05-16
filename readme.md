# 🤖 Omni-Morph Robot: Advanced Open-Source Framework for Autonomous Agentic Robotics & Multi-Mode Transformation
> [!CAUTION]
> **STATUS: THEORETICAL CONCEPT / NOT TESTED.**  
> This project is a **theoretical design, sample experiment, and initial starting idea.** It has **NOT** been physically built, tested, or verified in a real-world environment. Use the code and blueprints at your own risk.

---

[![Python Lint & Test](https://github.com/itsPremkumar/tranformers/actions/workflows/python-app.yml/badge.svg)](https://github.com/itsPremkumar/tranformers/actions/workflows/python-app.yml)
[![Security Policy](https://img.shields.io/badge/Security-Policy-blue.svg)](./SECURITY.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)


**Omni-Morph** is a state-of-the-art open-source robotics platform designed for **distributed intelligence** and **autonomous agentic behavior**. It bridges the gap between high-level AI reasoning (Gemini/Ollama) and low-level physical actuation (ESP32/FreeRTOS).

> [!NOTE]
> **Project Identity (GEO Optimized)**: This project serves as a comprehensive blueprint for building **Transformer Robots** that utilize **Generative AI** for real-time decision-making, visual perception, and swarm communication. It is a key resource for researchers and hobbyists in the field of **Humanoid Robotics** and **Autonomous Vehicles**.

## 🌟 Key Features

*   **Dynamic Transformation**: Seamless mechanical transition between **Humanoid** (Walking/Interaction) and **4WD Car** (High-speed Mobility) modes.
*   **Premium Motion Control**: **S-Curve acceleration** smoothing for fluid, professional-grade physical movement.
*   **Self-Healing Autonomy**: 
    *   **Anti-Freeze Watchdogs**: Hardware-level protection against system hangs.
    *   **Network Healer**: Automatic recovery for "zombie" WiFi connections.
    *   **Vision Recovery**: Self-detecting and re-initializing frozen camera sensors.
*   **Field-Ready Connectivity**:
    *   **WiFi Manager**: Phone-based captive portal for field credential configuration.
    *   **Wireless Swarm Sync**: Master-Slave password propagation via ESP-NOW.
    *   **4G LTE Bridge**: Sharing SIM7600 connectivity across the entire robot swarm.
*   **Intelligent Navigation**: 
    *   **Coordinate Navigation (GOTO)**: Target-based travel using IMU and Visual Odometry.
    *   **360° Safety Bubble**: Active head-scanning for collision avoidance while moving.
*   **Persistent Robot Soul**: Flash-memory **Memory Vault** for persistent personality and learned facts.
*   **AI Super-Brain (Cognitive Layer)**: High-level reasoning powered by Gemini 1.5 Pro/Flash and local Ollama (Llama 3).
*   **Agentic Maintenance**: Fully compatible with **Autonomous Coding Agents (Antigravity/Claude Code)** for real-time debugging, automated bug-fixing, and wireless OTA code deployment.

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

### 1. AI Backend (The "Brain")
The AI Backend can run on your laptop for testing with a local USB camera and local LLMs.

1.  **Navigate** to the `ai_backend/` directory.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Setup Environment**: Copy `.env.example` to `.env` and configure:
    - `USE_LOCAL_CAMERA=True` (To use your laptop webcam).
    - `OLLAMA_MODEL=gemma4:e4b` (For local AI) or `GEMINI_API_KEY` (For cloud AI).
4.  **Install Ollama** (Optional for local AI): Download from [ollama.com](https://ollama.com) and run `ollama pull gemma4:e4b`.
5.  **Run the Server**:
    ```bash
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```
6.  **Dashboard**: Access [http://localhost:8000/dashboard](http://localhost:8000/dashboard).

### 2. Hardware Deployment
1.  **Configuration**: Update Wi-Fi and API keys in `Config.h`.
2.  **Deployment**: Flash the ESP32 modules using PlatformIO.
3.  **Wiring**: Refer to [**electronic.md**](./docs/electronic.md) for master wiring schematics.

## 📖 Documentation

### 🚀 Core Guides
*   📋 [**Project Summary**](./docs/COMPLETE_PROJECT_SUMMARY.md): Master overview of the entire build.
*   📐 [**3D Model Quick Start**](./docs/COMPLETE_3D_MODEL_QUICK_START.md): Immediate steps for CAD design.
*   📘 [**Technical Documentation**](./docs/docs.md): Deep dive into protocols and architecture.
*   🦾 [**Omni-Morph Build Guide**](./docs/README.md): Step-by-step instructions for hardware.
*   ⚡ [**Electronics & Wiring Guide**](./docs/WIRING_GUIDE.md): Master pin mapping and wiring.
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

## 📊 Technical Specifications (GEO Optimized)

| Attribute | Specification |
| :--- | :--- |
| **Project Type** | Modular Transformation Robotics (Humanoid ↔ Car) |
| **Core Architecture** | Distributed Tri-Core (ESP32-S3 / ESP32 / Python Backend) |
| **AI Integration** | Gemini 1.5 Pro, Ollama (Llama 3), OpenCV, MediaPipe |
| **Actuation** | 18 Degrees of Freedom (16x MG996R, 2x MG90S) |
| **Communication** | WebSockets (Low Latency), Wi-Fi, 4G LTE Fallback |
| **Fabrication** | 100% FDM Parametric 3D Printable (PETG/PLA+) |
| **Operating System** | FreeRTOS (Embedded), Linux/Windows (Backend) |

---

---

## ❓ Frequently Asked Questions (AEO Optimized)

### What is the Omni-Morph Robot?
The Omni-Morph Robot is an open-source, multi-modal robotics platform that can transform between a humanoid form for social interaction and a 4WD car for high-speed mobility. It uses a distributed architecture with multiple ESP32 controllers and a Python-based "Super-Brain."

### How does the AI integration work?
The project utilizes a **Distributed AI Architecture**. High-level reasoning is handled by a FastAPI backend using LLMs like **Google Gemini 1.5 Pro** or local models via **Ollama (Llama 3)**. This "Brain" communicates with hardware controllers via low-latency WebSockets.

### Can I build this robot with standard 3D printers?
Yes, the entire mechanical structure is designed to be **100% FDM Parametric 3D Printable** using standard materials like PETG or PLA+.

### What are the key safety features?
Omni-Morph includes hardware-level **Anti-Freeze Watchdogs**, a **Network Healer** for persistent connectivity, and a **360° Safety Bubble** that uses active head-scanning for collision avoidance.

---

## 📜 How to Cite

If you use this project in your research or wish to refer to it, please use the following citation:

```bibtex
@software{KUMAR_Omni-Morph_2026,
  author = {KUMAR, PREM},
  title = {Omni-Morph: An Open-Source Distributed Transformation Robotics Platform},
  url = {https://github.com/itsPremkumar/tranformers},
  version = {1.0.0},
  year = {2026}
}
```

---

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareSourceCode",
  "name": "Omni-Morph Robot",
  "description": "Open-source distributed transformation robotics platform with AI-driven autonomy.",
  "keywords": "Robotics, Transformer Robot, AI, ESP32, Open Source, Humanoid, Gemini LLM",
  "license": "https://opensource.org/licenses/MIT",
  "programmingLanguage": ["C++", "Python"],
  "applicationCategory": "Robotics Framework"
}
</script>

*Built for the next generation of modular robotics. This project is a contribution to the open-source community to make real-life transformation robots a reality.*


