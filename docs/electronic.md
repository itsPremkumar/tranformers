# ⚡ Transformer Robot - Electronics & Wiring Guide

This document defines the master wiring specification for the Transformer Robot. Proper power distribution is critical for the stability of this multi-controller system.

---

## 🔋 1. Power Distribution System

The robot requires three distinct power rails to handle varying current demands:

| Rail | Voltage | Target Components | Recommended Source |
| :--- | :--- | :--- | :--- |
| **Logic Rail** | 5.0V | ESP32s, Sensors, OLED | Dedicated 3A Buck Converter |
| **Servo Rail** | 6.0V - 7.4V | PCA9685, 14-18 Servos | High-Current (10A+) Buck or LiPo |
| **Motor Rail** | 12V | L298N Driver, DC Motors | Direct 3S LiPo Connection |

> [!CAUTION]
> **Common Ground**: All GND pins from all power supplies and controllers **MUST** be connected to a single common ground bus. Failure to do so will cause serial communication errors and potential hardware damage.

---

## 🧠 2. Motion Controller (ESP32)

| Component | Pin Type | GPIO | Notes |
| :--- | :--- | :--- | :--- |
| **Motor IN1/2** | Output | 27 / 26 | L298N Channel A |
| **Motor IN3/4** | Output | 25 / 33 | L298N Channel B |
| **Motor ENA/B** | PWM | 14 / 12 | Speed Control |
| **Ultrasonic TRIG**| Output | 5 | Trigger Pulse |
| **Ultrasonic ECHO**| Input | 18 | Pulse Timing |
| **Pan Servo** | PWM | 13 | Head Horizontal |
| **Tilt Servo** | PWM | 16 | Head Vertical |
| **I2C SDA/SCL** | Data/Clock| 21 / 22 | To MPU6050 & PCA9685 |
| **Link RX/TX** | UART | **4 / 15** | To Comm Controller |

---

## 📡 3. Communication Controller (ESP32)

| Component | Pin Type | GPIO | Notes |
| :--- | :--- | :--- | :--- |
| **SIM7600 RX/TX** | UART | 16 / 17 | 4G Communication |
| **I2S BCK** | Clock | 26 | Audio Bit Clock |
| **I2S WS** | Select | 25 | Audio Word Select |
| **I2S DATA IN** | Input | 33 | From INMP441 Mic |
| **I2S DATA OUT** | Output | 22 | To MAX98357A Amp |
| **OLED SDA** | Data | 21 | I2C Data |
| **OLED SCL** | Clock | **23** | **Remapped** to avoid I2S conflict |
| **Link RX/TX** | UART | **15 / 4** | To Motion Controller |

---

## 👁️ 4. Vision Controller (ESP32-CAM)

*   **Model**: AI-Thinker ESP32-CAM
*   **Default Pinout**: AI-Thinker standard (GPIO 4 for Flash).
*   **Power**: Requires stable 5V (At least 500mA during streaming).

---

## ⚠️ Wiring Checklist

1.  **Cross Serial Links**: Comm TX (4) ➡️ Motion RX (4) AND Motion TX (15) ➡️ Comm RX (15).
2.  **I2C Pull-ups**: Ensure the I2C bus has appropriate pull-up resistors (usually built into the modules).
3.  **Capacitors**: Add a large electrolytic capacitor (1000uF+) across the Servo power rail to handle sudden current spikes during transformation.
