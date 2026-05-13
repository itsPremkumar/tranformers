# Advanced Software Enhancements (v2.0)

This document details the software-only professional upgrades implemented to enhance the robot's intelligence, safety, and interactivity without requiring additional hardware.

## 1. Connectivity & Wireless Management
### Over-the-Air (OTA) Updates
- **Hostname (Comm):** `Omni-Core-BT`
- **Hostname (Motion):** `Omni-Motion`
- **Implementation:** Integrated `ArduinoOTA` on both ESP32 controllers. Allows wireless firmware deployment over the local network (SSID: `one`).

### Persistent Memory (NVS)
- **Library:** `Preferences.h`
- **Function:** Stores the robot's "Mood" index (Happy, Sad, Angry, Hero) in Non-Volatile Storage.
- **Behavior:** The robot restores its previous facial expression and personality state immediately upon reboot.

---

## 2. Intelligence & Adaptive Sensing
### Terrain Roughness Detection
- **Algorithm:** Real-time variance analysis of Z-axis acceleration (IMU).
- **Output:** A `ROUGHNESS` value transmitted via telemetry.
- **Auto-Logic:** If roughness exceeds `0.05`, the Brain suggests switching to **Crawler Mode** for better stability.

### Voice Activity Detection (VAD)
- **Logic:** Energy-based filtering of I2S microphone data.
- **Function:** Filters out silence and background noise, only triggering AI processing when human speech is detected.

### Smart Battery Management
- **Voltage Thresholds:**
  - **6.8V:** Low Battery Warning (Triggered via OLED Sad Face and Web Status).
  - **6.4V:** Critical Cut-off (Hardware halt to protect LiPo cells).
- **Communication:** Motion controller monitors voltage and sends `CMD:BATTERY_LOW/CRITICAL` to the Comm controller.

---

## 3. Physical Intelligence (Motion)
### Gyro-Assisted Straight Drive
- **Sensor:** MPU6050 Gyroscope (Yaw).
- **Function:** Actively corrects motor speed drift. If the robot veers off-course, the system applies differential PWM correction to maintain a perfectly straight heading.

### Tilt-Compensated Vision
- **Sensor:** MPU6050 Accelerometer (Pitch).
- **Implementation:** Head Tilt servo automatically adjusts in real-time (offset mapping) to keep the ultrasonic sensor level with the ground during inclines or declines.

### Auto-Fall Detection & Recovery
- **Detection:** IMU-based orientation tracking.
- **Recovery:** Specialized servo sequences for `FALL_FORWARD` and `FALL_BACKWARD`. The robot uses its limbs to push off the ground and return to `STATE_STAND`.

---

## 4. Operational Modes
### Crawler Mode (All-Terrain)
- **Configuration:** Low-profile "Spider" stance.
- **Transformation:** Spreads hips to 160° and knees to 160° to lower the center of gravity.
- **Command:** `CMD:CRAWLER`

### Dynamic Lip-Sync
- **Analysis:** Peak amplitude calculation of outgoing I2S audio.
- **Visualization:** OLED mouth height scales dynamically (2px to 24px) based on the audio volume, creating a realistic "speaking" effect.

---

## 5. Technical Specifications
- **Partition Table:** `huge_app` (Comm Controller) to accommodate Bluetooth and OTA stacks.
- **Telemetry Interval:** 500ms
- **Heartbeat Timeout:** 2500ms (Safety auto-stop if Brain disconnects).
