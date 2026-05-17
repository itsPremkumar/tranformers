# Omni-Morph Robot - Quick Run Guide 🚀

This cheat-sheet contains the exact commands configured for your system's specific Python paths (using Thonny's Python environment) to run the AI backend, execute the automated hardware-in-the-loop (HIL) tests, and flash the ESP32 firmware.

---

## 💻 1. Start the FastAPI AI Backend Server
To boot up the main swarm AI backend, open your PowerShell terminal and run:

```powershell
& "C:\Program Files (x86)\Thonny\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

*   **Interactive Robot Web Dashboard:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
*   **FastAPI Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔬 2. Run the Automated Hardware (HIL) Test Suite
To scan your COM ports, test Wi-Fi/WebSocket command routing, and check the serial bridge between your two physical ESP32 boards, run:

```powershell
& "C:\Program Files (x86)\Thonny\python.exe" c:\one\tranformers\ai_backend\test_esp32_hardware.py
```

> **💡 Desk-wiring check before testing:**
> *   Connect **GND** of Board 1 to **GND** of Board 2.
> *   Connect **GPIO 17 (TX2)** of Board 1 $\leftrightarrow$ **GPIO 16 (RX2)** of Board 2.
> *   Connect **GPIO 16 (RX2)** of Board 1 $\leftrightarrow$ **GPIO 17 (TX2)** of Board 2.

---

## 🛠️ 3. Flash Firmware to ESP32 Controllers
To upload the compile-verified firmware files directly using your system's absolute PlatformIO CLI path, run:

```powershell
# 📶 Upload Communication Gateway Firmware (ESP32 Board 1)
& "C:\Users\PREM KUMAR\.platformio\penv\Scripts\pio.exe" run -d comm_controller -t upload

# ⚙️ Upload Motion Controller Firmware (ESP32 Board 2)
& "C:\Users\PREM KUMAR\.platformio\penv\Scripts\pio.exe" run -d motion_controller -t upload
```
