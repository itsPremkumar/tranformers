# PlatformIO CLI Guide & Tutorial

This guide provides instructions and examples for building, uploading, and debugging the firmware for both the **Communication Controller** and **Motion Controller** using the PlatformIO Command Line Interface (CLI).

---

## 📂 Project Structure

This workspace contains two distinct PlatformIO projects:
1. `comm_controller/` — Handles the Wi-Fi AP/STA mode, Web Dashboard, and WebSockets.
2. `motion_controller/` — Handles motor controls, servos, balance (IMU), and safety telemetry.

Always run these commands from the directory of the project you want to build or upload.

---

## ⚡ Core CLI Commands

### 1. Build / Compile Code
Compiles the source code and checks for syntax/build errors without uploading to the board.
* **Command**:
  ```powershell
  pio run
  ```
* **Specific Environment**: (If multiple environments are defined in `platformio.ini`)
  ```powershell
  pio run -e esp32dev
  ```

### 2. Upload Firmware (USB Serial)
Compiles and uploads the compiled binary to the connected ESP32 board over a USB cable.
* **Auto-detect Port**:
  ```powershell
  pio run -t upload
  ```
* **Force Specific COM Port** (e.g., `COM15`):
  ```powershell
  pio run -t upload --upload-port COM15
  ```

### 3. Serial Monitor
Opens a terminal to read log outputs (`Serial.print()`) from the ESP32.
* **Auto-detect Port & Baud Rate**:
  ```powershell
  pio device monitor -b 115200
  ```
* **Force Specific Port**:
  ```powershell
  pio device monitor -p COM15 -b 115200
  ```
* **To Exit the Monitor**: Press `Ctrl + C` or `Ctrl + A` then `Ctrl + Q`.

### 4. Upload & Monitor (Combined)
Compiles, uploads, and immediately opens the serial monitor. Highly recommended for daily development.
* **Command**:
  ```powershell
  pio run -t upload -t monitor
  ```

### 5. Clean Build Files
Deletes compiled temporary binaries and caches. Use this if you run into strange compile conflicts or linker errors.
* **Command**:
  ```powershell
  pio run -t clean
  ```

---

## 📡 Wireless OTA (Over-The-Air) Uploads
Once the ESP32 is running and connected to Wi-Fi, you can flash updates wirelessly.

1. Connect your computer to the same Wi-Fi network as the ESP32.
2. Run the upload command targeting the ESP32's IP address:
   ```powershell
   pio run -t upload --upload-port 10.179.30.67
   ```
*(Replace `10.179.30.67` with the active IP printed on boot).*

---

## 🔍 Diagnostics and Utilities

* **List Connected Serial Devices**:
  ```powershell
  pio device list
  ```
* **Locate PlatformIO Executable Path**:
  If the `pio` command is not recognized globally in your command prompt/terminal, use the full PlatformIO virtual environment path:
  ```powershell
  & "C:\Users\PREM KUMAR\.platformio\penv\Scripts\pio.exe" <command>
  ```

---

## 🛠️ Troubleshooting Common Errors

### ❌ `Could not open port: PermissionError(13, 'Access is denied.')`
* **Cause**: Another program (usually an active serial monitor, terminal, or another IDE) has the COM port open.
* **Fix**: Close all active serial terminals/monitors (press `Ctrl + C` in open CLI monitoring terminals) and retry the upload.

### ❌ `Error: Please specify upload_port...`
* **Cause**: PlatformIO cannot detect any active USB-to-UART serial bridge device plugged into the computer.
* **Fix**: 
  1. Ensure the micro-USB/USB-C cable is firmly plugged in.
  2. Make sure you are using a **data sync** cable, not a power-only charging cable.
  3. Check Device Manager to verify the driver (e.g., *Silicon Labs CP210x USB to UART Bridge*) is active.
  4. If the board was put into deep sleep, press the physical **EN/RST button** on the ESP32 board to wake up the USB serial bridge.
