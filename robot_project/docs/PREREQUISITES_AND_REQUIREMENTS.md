# 📋 Prerequisites & Hardware/Software Requirements
> **Omni-Morph Transformer Humanoid Upgrade - Jetson Deployment Guide**

This document specifies the exact physical components, software libraries, and setup steps required to successfully deploy the Jetson edge computer architecture for the Omni-Morph robot.

---

## 1. Physical Hardware Requirements

To transition the robot to untethered edge autonomy, verify you have the following hardware:

### 🧠 Computing Board (SBC)
*   **NVIDIA Jetson Module:** 
    *   *Recommended:* **Jetson Orin Nano Developer Kit (8GB RAM)** or **Jetson Orin NX (8GB/16GB)**.
    *   *Alternative:* **Jetson Xavier NX Developer Kit** or **Jetson AGX Orin**.
    *   *Note:* The Orin Nano 4GB is not recommended due to local LLM and perception memory constraints.
*   **High-Speed Storage:** **128GB+ M.2 NVMe SSD** (SD cards are prone to corruption and lack the bandwidth required for local LLMs/DeepStream pipelines).

### ⚡ Power Supply & Regulation
*   **QS-1212CCBA-80W Buck Converter:** High-current regulator (Input: 7-40V, Output: 5V @ 6A) to feed the Jetson dev board barrel jack connector.
*   **Isolator Buck Regulator (5V @ 3A):** Feeds the ESP32 logic rail separately to protect the microcontroller from motor/GPU noise.
*   **Jumper Pins:** Required to close the **J48 header** on the dev kit carrier board to enable Barrel Jack high-current power.

### 👁️ Computer Vision & SLAM Sensors
*   **Depth Camera:** **Intel RealSense D435, D435i, or D455** (needed for Isaac ROS Visual Odometry and Nvblox local 3D costmapping).
*   **Wide-Angle Tracking Camera:** **Sony IMX219 CSI V2 Camera** with a 160° wide-angle lens (connected via ribbon cable for low-latency face and hand gesture tracking).
*   **2D Laser Lidar:** **RPLIDAR A1 M8 or A2M8** (USB connection) for secondary safety bubbles and Nav2 grid-map SLAM.

### 🗣️ Voice and Audio Interfaces
*   **Audio Input:** **ReSpeaker 4-Mic Array** (USB connection) or ReSpeaker 2-Mics pHAT (I2S connection) for directional voice recognition.
*   **Audio Amplifier:** **MAX98357A I2S Audio Amp** breakout.
*   **Speaker:** 8 Ohm, 2W or 3W micro speaker.

### 🔌 Communication Bridges
*   **UART Serial Bridge:** **CP2102 USB-to-TTL Adapter** (Standard Setup).
*   **CAN Bus Controller:** **Waveshare SN65HVD230 Transceiver** paired with the Jetson's native `can0` pins (Industrial Setup).

---

## 2. PC Software Requirements

This software is required on your local development computer (Windows, Linux, or macOS) to write and upload code wirelessly:

*   **Python:** Version **3.8 to 3.12** installed (needed to run [auto_sync_jetson.py](file:///c:/one/tranformers/robot_project/tools/auto_sync_jetson.py)).
*   **OpenSSH Client:** Natively installed (enabled by default in Windows 10/11, macOS, and Linux) to execute secure shell commands.
*   **Visual Studio Code:**
    *   **Remote - SSH Extension:** For wireless real-time debugging directly on the Jetson.
*   **Network:** Both the PC and Jetson must be connected to the **same Wi-Fi router** (a standard 5GHz band router is recommended to support high-speed image streaming).

---

## 3. Jetson Software & OS Requirements

The Jetson dev board must be flashed with the official NVIDIA software stack:

*   **Operating System:** **NVIDIA JetPack SDK 6.x** (provides Ubuntu 22.04 LTS, matching ROS 2 Humble).
    *   *Xavier boards:* Use **JetPack 5.x** (Ubuntu 20.04 LTS) and pull ROS 2 Foxy or compile Humble from source.
*   **Acceleration Libraries:**
    *   **CUDA Toolkit (v12.x or v11.x)**
    *   **TensorRT (v8.x+)**
    *   **cuDNN (v8.x+)**
    *   *Note:* These are installed automatically when selecting the "Full Installation" option in the NVIDIA SDK Manager.
*   **Docker Container Engine:**
    *   **Docker CE** (Version 20.10+).
    *   **NVIDIA Container Toolkit** (Allows Docker containers to pass GPU acceleration commands to the hardware).
*   **Ollama Server:** Installed on the Jetson (locally or via container) with the **llama3:8b** or **phi3:medium** GGUF model pre-loaded.

---

## 4. Hardware Wiring & Check Sheet

Before running software scripts, double-check these wiring paths:

```
[ Jetson Pinout ]                 [ Target Device ]
Pin 1 (3.3V) ────────────────────► OLED VCC / CAN Transceiver VCC
Pin 9 (GND)  ────────────────────► OLED GND / CAN Transceiver GND
Pin 3 (SDA)  ────────────────────► OLED SDA
Pin 5 (SCL)  ────────────────────► OLED SCL

Pin 4 (5V)   ────────────────────► MAX98357A VIN
Pin 34 (GND) ────────────────────► MAX98357A GND
Pin 12 (BCLK)────────────────────► MAX98357A BCLK
Pin 35 (LRC) ────────────────────► MAX98357A LRC
Pin 40 (DIN) ────────────────────► MAX98357A DIN

Pin 29 (CAN_TX) ─────────────────► CAN Transceiver TXD
Pin 31 (CAN_RX) ─────────────────► CAN Transceiver RXD
```
