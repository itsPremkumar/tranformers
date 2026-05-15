# 🔌 Master Wiring Guide: Transformers Motion Controller

This guide provides the exact physical pin mappings for connecting your sensors, motors, and controllers to the ESP32 (Motion Controller).

## 📊 Pin Mapping Table

| Component | Pin Function | GPIO (Software) | ESP32 Physical Label |
| :--- | :--- | :--- | :--- |
| **Motors (L298N)** | Left Motor IN1 | 27 | **D27** |
| | Left Motor IN2 | 26 | **D26** |
| | Right Motor IN1 | 25 | **D25** |
| | Right Motor IN2 | 33 | **D33** |
| | Left Speed (ENA) | 14 | **D14** |
| | Right Speed (ENB) | 12 | **D12** |
| **Sensors (I2C)** | SDA (Data) | 21 | **D21** |
| | SCL (Clock) | 22 | **D22** |
| **Ultrasonic** | Trigger | 5 | **D5** |
| | Echo | 18 | **D18** |
| **Head Servos** | Pan Servo | 13 | **D13** |
| | Tilt Servo | 16 | **D16** |
| **Comms Link** | RX (To Comm TX) | 4 | **D4** |
| | TX (To Comm RX) | 15 | **D15** |
| **Health Monitor**| Battery Voltage | 34 | **D34** |
| | Current Sensor | 35 | **D35** |

---

## 🛠️ Step-by-Step Connection Instructions

### 1. The Motor Drive (L298N)
Connect the 6 control wires from your L298N driver to the ESP32. Ensure the L298N **GND** is connected to the ESP32 **GND**.

### 2. The I2C Bus (Gyro & Servo Driver)
The MPU6050 and the PCA9685 share the same two wires (**D21** and **D22**). 
> [!TIP]
> Use a small breadboard or a custom PCB to "split" these wires so both sensors can plug in at once.

### 3. The Ultrasonic "Eyes"
The HC-SR04 requires **5V** to operate reliably. Connect its VCC to the **VIN** pin of the ESP32 if you are powering the ESP32 via a 5V source.

### 4. Comm-to-Comm Link
This is a "Cross-Over" connection:
- Motion **TX (D15)** -> Comm **RX**
- Motion **RX (D4)** -> Comm **TX**

---

## ✅ Post-Wiring Test
Once you have finished wiring, upload the code and open the Serial Monitor. Type the following command:
`CMD:TEST`

The robot will perform a self-diagnostic and report the status of every sensor in this list.
