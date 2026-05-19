import serial
import time
import sys
import io

# Safe console encoding wrapper for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_release():
    print("Opening COM15 at 115200...")
    try:
        # Open without initializing DTR/RTS
        ser = serial.Serial()
        ser.port = "COM15"
        ser.baudrate = 115200
        ser.timeout = 1.0
        ser.open()
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    # To run ESP32 normally: release DTR and RTS (set to False)
    print("Releasing DTR and RTS control lines to allow normal boot...")
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(0.5)

    # Let's perform a reset pulse that leaves them in the released state:
    # 1. Pull EN low (RTS=True, DTR=False)
    print("Sending reset pulse...")
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    
    # 2. Release EN and GPIO0 (RTS=False, DTR=False)
    ser.setRTS(False)
    ser.setDTR(False)
    time.sleep(0.5)

    print("Listening to output for 6 seconds...")
    start = time.time()
    buffer = ""
    while time.time() - start < 6.0:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    print(f" [ESP32] {line}")
        time.sleep(0.1)

    ser.close()

if __name__ == "__main__":
    test_release()
