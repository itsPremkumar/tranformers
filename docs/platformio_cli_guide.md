# PlatformIO CLI Compliance & Verification Guide

This document outlines the professional method for verifying, compiling, and checking your Transformer Robot microcontroller code using the **PlatformIO Core (CLI)**. 

## 1. Prerequisites
Ensure you have the PlatformIO Core installed. If you use VS Code, it is already located in your user profile.

**Path to CLI (Windows Example):**
`C:\Users\<YourUser>\.platformio\penv\Scripts\pio.exe`

---

## 2. Basic Compilation (The "Compliance Check")
Before uploading to the robot, always run a build to ensure there are no syntax or library errors.

**Command:**
```bash
pio run
```
*   **What it does:** Downloads required libraries, compiles all `.cpp` files, and links the final firmware.
*   **Success Indicator:** `[SUCCESS]` in green at the bottom.

---

## 3. Advanced Compliance Verification (`pio check`)
To find deeper bugs like **memory leaks**, **uninitialized variables**, or **potential crashes** that a standard compile might miss:

**Command:**
```bash
pio check
```
*   **Why use it:** It performs "Static Analysis." It reads your code without running it to find dangerous patterns.
*   **Recommended for:** Critical systems like the Motion Controller.

---

## 4. Multi-Environment Selection
If your `platformio.ini` has multiple environments (e.g., `esp32dev`, `esp32cam`), you can target a specific one:

**Command:**
```bash
pio run -e esp32dev
```

---

## 5. Deployment (Uploading to Hardware)
Once the compliance check passes, use the CLI to flash the code to your ESP32 via USB.

**Command:**
```bash
pio run -t upload
```
*   **Tip:** If you have multiple robots connected, specify the port:
    ```bash
    pio run -t upload --upload-port COM3
    ```

---

## 6. Real-time Monitoring
To see the debug logs from the robot after flashing:

**Command:**
```bash
pio device monitor
```
*   **Exit Monitor:** Press `Ctrl + C` or `Ctrl + ]`.

---

## 7. Troubleshooting Common CLI Issues

| Error | Solution |
| :--- | :--- |
| `'pio' is not recognized` | Add the PIO Scripts folder to your Windows `PATH` or use the absolute path. |
| `UnknownPackageError` | Check your `platformio.ini` library names. Ensure you have an internet connection. |
| `Failed to connect to ESP32` | Hold the **BOOT** button on the ESP32 when you see the "Connecting..." message. |
| `ModuleNotFoundError` | Run `python -m pip install <module_name>` inside the PIO virtual environment. |

---

*Last Updated: 2026-05-11*
