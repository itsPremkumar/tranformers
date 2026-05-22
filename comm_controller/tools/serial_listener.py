import serial
import time
import sys

port = 'COM15'
baud = 115200
timeout = 5 # seconds

print(f"Opening port {port} at {baud} baud...", flush=True)
try:
    ser = serial.Serial(port, baud, timeout=1)
    # Toggle DTR/RTS to reset the board so we see the boot message
    print("Resetting ESP32 board...", flush=True)
    ser.dtr = False
    ser.rts = False
    time.sleep(0.1)
    ser.dtr = True
    ser.rts = True
    time.sleep(0.5)
    
    start_time = time.time()
    print("Listening for 20 seconds...", flush=True)
    while time.time() - start_time < 20:
        line = ser.readline()
        if line:
            # Decode ignoring non-ascii bytes
            decoded = line.decode('ascii', errors='ignore').strip()
            # Remove any control characters or keep it simple
            printable = "".join(c for c in decoded if 32 <= ord(c) < 127 or c in '\r\n\t')
            if printable:
                print(f"[SERIAL OUT] {printable}", flush=True)
    ser.close()
    print("Listening complete.", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
    sys.exit(1)
