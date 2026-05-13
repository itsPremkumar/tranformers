# 🛡️ Diagnostics, Calibration & Safety

The Transformer Robot is a high-power machine. To protect the electronics, mechanical joints, and the environment, it implements a multi-layer safety and diagnostic architecture.

## 🔍 1. Hardware Self-Test (`CMD:TEST`)
Before deployment, it is highly recommended to run the **Full Diagnostic Suite**. This can be triggered via the Serial Monitor or the Web Dashboard.

### Test Sequence:
1.  **I2C Bus Scan**: Verifies connectivity to the PCA9685 (Servos) and MPU6050 (IMU).
2.  **Ultrasonic Validation**: Checks if the HC-SR04 is returning valid distances (0-400cm).
3.  **Head Servo Sweep**: Moves the head gimbal through its full range of motion.
4.  **Kinetic Validation**: Briefly engages the drive motors and uses the IMU to verify that physical movement actually occurred.

## 🚨 2. Multi-Layer Safety Protocols

### 🔋 2.1 Battery Intelligence
The system monitors the 11.1V 3S battery in real-time with hardware-level protection:
- **Voltage Warning (6.8V)**: The robot broadcasts a "Battery Low" status, shows a **Sad Face** on the OLED, and provides a verbal warning.
- **Critical Cut-off (6.4V)**: To prevent cell damage, the Motion Controller performs an **Emergency Hardware Halt**, locking all motors and stopping logic.
- **NVS Memory**: Current mood and power states are saved to Non-Volatile Storage to ensure safety across reboots.

### ⚡ 2.2 Over-Current Protection
The backend monitors the Amperage from the `CURRENT_PIN`:
- **Threshold**: **2.5 Amps**.
- **Action**: If current exceeds this limit (indicating a jammed motor or short circuit), an emergency `CMD:STOP` is triggered immediately.

### 🕳️ 2.3 Hole & Cliff Detection
The ultrasonic sensor is mounted at an angle to detect the ground:
- **Threshold**: **45cm**.
- **Action**: If the distance to the ground suddenly increases (indicating a stair or table edge), the robot halts and reverses automatically.

### 💓 2.4 Communication Heartbeat
To prevent "runaway" scenarios if the Wi-Fi or Controller link fails:
- **Interval**: Comm controller sends `BEAT` every 1000ms.
- **Timeout**: If Motion controller receives nothing for **2500ms**, it enters `STATE_STAND` and locks all motors.

### 🚨 2.5 Fall Detection & Auto-Recovery
The MPU6050 IMU monitors the robot's pitch and roll in real-time:
- **Detection**: Instant stop if an extreme tilt is detected (Forward, Backward, or Side fall).
- **Auto-Recovery**: After a fall, the robot executes a **Self-Righting Sequence**. It identifies its orientation and uses its servos to push itself back up to a standing position.

## 🛠️ 3. Calibration
- **Servo Offsets**: Use the `standPosition()` command to verify that all limbs are aligned.
- **IMU Zeroing**: Ensure the robot is on a level surface during boot-up to calibrate the gyroscope.
