# 🦾 Sentinel-Class Autonomous Transformer: MASTER BUILD GUIDE

This is the final, comprehensive guide for the **Sentinel-Class Autonomous Transformer**. It combines all technical requirements, the Bill of Materials (BOM), and assembly blueprints.

---

## 🛒 1. Master Bill of Materials (Shopping List)

### ⚡ Power & Drivers
- [ ] **Battery**: 1x 11.1V (3S) Li-Ion or Li-Po Battery Pack (3000mAh+ / 30C discharge).
- [ ] **Buck Converter**: 1x 10A DC-DC Step-Down (12V to 5V/6V) for the 18 servos.
- [ ] **Servo Driver**: 2x PCA9685 16-Channel I2C PWM Drivers.
- [ ] **Motor Driver**: 1x L298N Dual H-Bridge Driver (or TB6612FNG for better efficiency).
- [ ] **Wiring**: 18AWG or 20AWG Silicone Wire (Red/Black) for the main power rail.

### 🦴 Actuators
- [ ] **Hip & Knee Servos**: 12x MG996R Metal Gear High-Torque Servos.
- [ ] **Ankle & Head Servos**: 6x MG90S Metal Gear Micro Servos.
- [ ] **Drive Motors**: 4x Yellow DC Geared Motors (1:48 Ratio) + 65mm Wheels.

### 🧠 Controllers & Sensors
- [ ] **Comm Controller**: 1x ESP32-S3 (for high-speed WebSockets/Audio).
- [ ] **Motion Controller**: 1x ESP32 (30-pin or 38-pin).
- [ ] **Vision**: 1x ESP32-CAM (with external antenna recommended).
- [ ] **IMU**: 1x MPU6050 (Gyroscopic balance).
- [ ] **Distance**: 1x HC-SR04 Ultrasonic Sensor.
- [ ] **Display**: 1x SSD1306 0.96" I2C OLED Display.
- [ ] **Audio**: 1x MAX98357A I2S Amplifier + 1x 3W 4-Ohm Speaker.

---

## 🔌 2. Wiring Architecture (The Nervous System)

### 2.1 Power Distribution (The "3-Highway" Split)
1.  **Direct 11.1V**: Battery ➡️ L298N Motor Driver.
2.  **5V Servo Rail**: Battery ➡️ 10A Buck Converter ➡️ PCA9685 V+ Rails.
3.  **3.3V Logic Rail**: Battery ➡️ LDO/Buck (or ESP32 5V Pin) ➡️ ESP32s, Sensors, and OLED.
*   **CRITICAL**: All Ground (GND) wires must be connected together (Common Ground).

### 2.2 Communication (I2C Bus)
*   **SDA (Pin 21)** & **SCL (Pin 22)** on the ESP32.
*   Connect the following in parallel: PCA9685 #1, PCA9685 #2, MPU6050, and SSD1306 OLED.
*   *Note: Use short wires (<15cm) to prevent signal noise.*

---

## 🏗️ 3. Physical Construction Guide

### 3D Printing Recommendations
*   **Material**: PETG or high-quality PLA+.
*   **Infill**: 
    *   Torso: 20%.
    *   Legs/Hips: **50% (Grid/Gyroid)** to handle MG996R torque.
*   **Mounting**:
    *   **MPU6050**: Must be bolted flat to the center of the torso.
    *   **OLED/Camera**: Mounted on the head gimbal for 180° awareness.

---

## 💻 4. Software Ecosystem

### 4.1 AI Backend (PC/Server)
*   **Docker**: Run `docker-compose up --build`.
*   **AI Engine**: Primary: Gemini 2.0 / Fallback: DeepSeek R1 (via Ollama).
*   **Vision**: Real-time Gesture Recognition and Face Tracking active via `reactive_vision.py`.

### 4.2 Firmware (ESP32s)
*   **Comm Controller**: Bridges robot to AI Brain via WebSockets. Handles Physical Voice (I2S).
*   **Motion Controller**: Receives JSON commands and executes the 18-servo transformation sequence.

---

## ✅ 5. Final Build Checklist
1.  [ ] **Calibrate Servos**: Test every servo individually at 90° before installing.
2.  [ ] **Test 11V Rail**: Ensure the L298N is receiving 11V but the Servos are ONLY receiving 5-6V.
3.  [ ] **IMU Calibration**: Run the balance-test script to ensure the MPU6050 is reading level.
4.  [ ] **Identity Check**: Ensure `ROBOT_NAME` in the firmware matches your AI Backend database.

**Mission Ready.** Your Transformers robot project is now fully documented for purchase and assembly.
