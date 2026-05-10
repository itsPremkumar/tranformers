# 🦾 Sentinel-Class Transformer: Full Master Architecture

This document provides the complete technical blueprint for the **Autonomous 11.1V Transformer Robot**, covering mechanical, electronic, and software systems.

---

## 🏗️ 1. Physical & Kinematic Structure (18-DOF)

The robot utilizes a **Four-Legged Hybrid Chassis** that enables high-speed rolling and complex humanoid-style walking.

### 🦵 1.1 The Articulated Legs (x4)
Each leg is a "Smart Limb" with 4 degrees of freedom (DOF):
1.  **Hip Pan**: Lateral steering (Servo: MG996R).
2.  **Hip Tilt**: Body lift/squat (Servo: MG996R).
3.  **Knee Flex**: Primary transformation joint (Servo: MG996R).
4.  **Ankle Stabilizer**: Leveling the drive-foot (Servo: MG90S).

### 🏎️ 1.2 The Drive System
*   **Actuators**: 4x **Yellow Geared Motors (1:48 Ratio)**.
*   **Placement**: Integrated into the "Foot" of each leg using a 3D-printed sandwich mount.
*   **Function**: Provides 4WD high-speed mobility in Car Mode and stable standing platforms in Robot Mode.

---

## 🔋 2. 3S-Pro Power System (11.1V)

The robot is powered by an **11.1V (3S) Li-Ion Battery Pack**. To protect the electronics, the power is distributed via three dedicated "Highways":

*   **Highway A (11.1V Direct)**: Powers the **L298N Motor Driver**. This provides maximum torque for the DC motors.
*   **Highway B (High-Power Buck Converter 5V/10A)**: Steps down 11V to **5.0V - 6.0V**. This is dedicated exclusively to the **18 Servos**.
*   **Highway C (Clean 3.3V Logic Rail)**: Isolated power for the **ESP32s**, **IMU**, and **Sensors** to ensure stability during high-current motor movements.

---

## 🧠 3. Electronic Architecture (The Nervous System)

### 3.1 Distributed Control
*   **Primary Brain (AI Backend)**: Hosted on PC/Docker. Handles Vision, LLM, and Long-Term Memory.
*   **Comm Controller (ESP32-S3)**: Gateway for WebSocket bridge, OLED face, and I2S Physical Voice.
*   **Motion Controller (ESP32)**: Handles real-time PWM for 18 servos and 4 DC motors.

### 🔌 3.2 Drivers & Expansion
*   **PCA9685**: I2C PWM expansion for precise control of all 18 servos.
*   **L298N**: Dual H-Bridge for the 4 DC motors.
*   **INA219**: Current/Voltage sensing for hardware health monitoring.

---

## 📡 4. Sensor & Component Placement

| Component | Physical Location | Function |
| :--- | :--- | :--- |
| **MPU6050 (IMU)** | **Geometric Center of Torso** | **Balance Hub**. Detects tilt/fall events and provides orientation data. |
| **Ultrasonic** | **Front of Head Gimbal** | Obstacle avoidance and "Personal Space" safety buffer. |
| **SSD1306 OLED** | **Head Front (Face)** | Displays AI eyes, moods, and system status. |
| **ESP32-CAM** | **Head Center** | AI Vision for face tracking and gesture recognition. |
| **MAX98357A** | **Base of Torso** | I2S Audio amplifier for the physical AI voice. |

---

## 💻 5. Software & Intelligence

### 🤖 5.1 Robot States (Modes)
1.  **STATE_CAR**: Low center of gravity. Optimized for speed and manual racing.
2.  **STATE_ROBOT**: High vantage point. Optimized for AI interaction, face tracking, and walking.
3.  **STATE_TRANSFORM**: A non-blocking sequence that moves all 18 servos in sync to change modes.

### 👁️ 5.2 Sensing Suite
*   **AI Vision**: MJPEG stream for high-level reasoning and local gesture tracking.
*   **Safety**: Local ultrasonic pings trigger emergency stops in autonomous modes.
*   **Health Telemetry**: Real-time Battery Voltage and Current sensing sent to the AI Brain.

---

## 🔄 6. Transformation Logic (The Sequence)

| Step | Component | Action | Purpose |
| :--- | :--- | :--- | :--- |
| **1** | Motors | Stop All Wheels | Safety |
| **2** | Head | TILT: 0 (Look Forward) | Balance |
| **3** | Knees | Move to 135° | Extension |
| **4** | Hips | Tilt to 90° | Raising Body |
| **5** | Ankles | Level Wheels | Stability |
| **6** | OLED | Display "Happy Face" | Success |

---

## 🏁 7. Hardware Manifest (Bill of Materials)
*   **Battery**: 11.1V 3S Li-Ion (3000mAh+ recommended).
*   **Primary Servos**: 12x MG996R (Metal Gear, High Torque).
*   **Secondary Servos**: 6x MG90S (Metal Gear, Mini).
*   **Motors**: 4x Yellow DC Geared Motors.
*   **Buck Converter**: 1x 10A DC-DC Step-Down.
*   **Controllers**: 2x ESP32 + 1x ESP32-CAM.
*   **Display**: 1x SSD1306 0.96" OLED.
*   **Audio**: 1x I2S DAC + 3W Speaker.
