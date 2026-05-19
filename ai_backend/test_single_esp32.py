import sys
import os
import time
import io

# Force console to output UTF-8 safely to bypass CP1252/Windows encoding constraints
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- 1. Import or Install Serial ---
try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[BOOTSTRAP] 'pyserial' is missing. Installing automatically...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
        import serial
        import serial.tools.list_ports
        print("[BOOTSTRAP] 'pyserial' installed successfully!")
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] Failed to auto-install 'pyserial': {e}")
        sys.exit(1)

def main():
    print("==================================================")
    print("🔍 OMNI-MORPH SINGLE ESP32 DIAGNOSTIC TOOL 🔍")
    print("==================================================")

    # 1. Scan Ports
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ NO ACTIVE COM PORTS DETECTED!")
        print("Please ensure your ESP32 board is plugged in via USB.")
        sys.exit(1)

    print(f"Found {len(ports)} serial port(s):")
    target_port = None
    for p in ports:
        print(f" - {p.device}: {p.description}")
        if "COM15" in p.device:
            target_port = p.device

    if not target_port:
        # Default to the first available port
        target_port = ports[0].device

    print(f"\nTargeting Port: {target_port}")

    # 2. Establish Connection
    BAUD_RATE = 115200
    try:
        ser = serial.Serial(target_port, BAUD_RATE, timeout=2.0)
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not open port {target_port}: {e}")
        sys.exit(1)

    # 3. Hardware Pulse Reset (Robust RTS/DTR release pattern)
    print("\n♻️ Resetting ESP32 board via serial pulse...")
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(0.1)
    
    # Send EN low pulse
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    
    # Release EN and GPIO0
    ser.setRTS(False)
    ser.setDTR(False)
    time.sleep(0.5)
    ser.reset_input_buffer()

    # 4. Listen to Boot & Application Output
    print("📥 Capturing boot logs for 6 seconds (Please wait)...")
    boot_logs = []
    start_time = time.time()
    
    # Read non-blockingly
    buffer = ""
    while time.time() - start_time < 6.0:
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        print(f"  [ESP32] {line}")
                        boot_logs.append(line)
            else:
                time.sleep(0.05)
        except Exception as e:
            print(f"[ERROR] Reading serial failed: {e}")
            break

    # 5. Classify Firmware Role
    print("\n==================================================")
    print("📊 DIAGNOSTIC RESULTS & FIRMWARE ANALYSIS 📊")
    print("==================================================")

    is_comm = False
    is_motion = False
    has_ota = False
    has_ble = False
    has_i2c_error = False

    for log in boot_logs:
        if any(keyword in log for keyword in ["Comm Controller", "Action Received:", "[AUDIO]", "[WIFI]", "Long Range Mode", "[BT-SOURCE]"]):
            is_comm = True
        if any(keyword in log for keyword in ["Exec:", "omni-motion", "Safety:", "MPU6050", "[FAILSAFE]"]):
            is_motion = True
        if "[OTA]" in log or "ArduinoOTA" in log:
            has_ota = True
        if "BLE" in log or "Bluetooth" in log or "BT-SOURCE" in log:
            has_ble = True
        if "MPU6050 connection failed" in log or "I2C" in log:
            has_i2c_error = True

    if is_comm:
        print("Detected Role: 📟 COMMUNICATION CONTROLLER (Network / UI)")
        print("  - Boot Status: Booted successfully.")
        print(f"  - Bluetooth Enabled: {'Yes' if has_ble else 'No / Unreported'}")
        print(f"  - OTA Enabled: {'Yes' if has_ota else 'No / Unreported'}")
        print("\n🧪 Running Comm-Specific Checks...")
        # Write some commands to test input buffer
        print("Writing test command 'CMD:SCAN' over Serial...")
        ser.write(b"CMD:SCAN\n")
        time.sleep(1.0)
        # Check output
        if ser.in_waiting > 0:
            resp = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"Response: {resp.strip()}")
        else:
            print("No serial reply to SCAN (Comm Controller parses commands primarily via WebSocket).")

    elif is_motion:
        print("Detected Role: ⚙️ MOTION CONTROLLER (Motor / Safety)")
        print("  - Boot Status: Booted successfully.")
        print(f"  - MPU6050/I2C State: {'⚠️ MPU6050 Missing/Failed' if has_i2c_error else 'OK'}")
        print(f"  - OTA Enabled: {'Yes' if has_ota else 'No / Unreported'}")
        print("\n🧪 Running Motion-Specific Checks...")
        # Write test command
        print("Sending safety heartbeat 'BEAT' and 'CMD:STOP'...")
        ser.write(b"BEAT\n")
        time.sleep(0.2)
        ser.write(b"CMD:STOP\n")
        time.sleep(1.0)
        # Check response
        response_lines = []
        if ser.in_waiting > 0:
            resp = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            for line in resp.split("\n"):
                line = line.strip()
                if line:
                    print(f"Response: {line}")
                    response_lines.append(line)
        
        has_ack = any("ACK" in r for r in response_lines)
        if has_ack:
            print("✔️ Serial Command Parser: OK (Responded with ACK)")
        else:
            print("⚠️ Command Parser did not reply with ACK (Wait for connections or check baud config).")

    else:
        print("Detected Role: ❓ UNCLASSIFIED / OTHERS")
        print("  - The ESP32 is online but did not output known startup signatures.")
        print("  - Boot logs show raw setup routines or standard bootloader data.")
        print("\n💡 Suggestions:")
        print("  1. If this is a new board, you should compile and upload one of the firmwares:")
        print("     - Compile & Upload Comm Controller:   pio run -d comm_controller -t upload")
        print("     - Compile & Upload Motion Controller: pio run -d motion_controller -t upload")
        print("  2. Ensure the baud rate matches 115200 in the code.")

    ser.close()
    print("==================================================")

if __name__ == "__main__":
    main()
