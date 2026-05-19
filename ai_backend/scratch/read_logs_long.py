import serial
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_long():
    print("Opening COM15 at 115200...")
    try:
        ser = serial.Serial("COM15", 115200, timeout=1.0)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    print("Sending reset pulse...")
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(0.1)
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setRTS(False)
    ser.setDTR(False)
    time.sleep(0.5)
    ser.reset_input_buffer()

    print("Capturing logs for 20 seconds...")
    start = time.time()
    buffer = ""
    while time.time() - start < 20.0:
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
    test_long()
