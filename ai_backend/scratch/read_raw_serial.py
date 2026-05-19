import serial
import time

def read_raw():
    print("Opening COM15 at 115200...")
    try:
        ser = serial.Serial("COM15", 115200, timeout=1.0)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    print("Rebooting board...")
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.2)
    ser.setDTR(True)
    ser.setRTS(False)
    time.sleep(0.5)

    print("Reading for 5 seconds...")
    start = time.time()
    raw_data = b""
    while time.time() - start < 5.0:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting)
            raw_data += chunk
            print(f"Read {len(chunk)} bytes: {chunk}")
        time.sleep(0.1)

    print(f"\nTotal bytes received: {len(raw_data)}")
    print(f"Raw hex: {raw_data.hex()}")
    print(f"Text representation: {raw_data.decode('utf-8', errors='replace')}")
    ser.close()

if __name__ == "__main__":
    read_raw()
