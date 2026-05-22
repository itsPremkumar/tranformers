import sys
import subprocess
import time

try:
    import websocket
except ImportError:
    print("Installing websocket-client library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
    import websocket

import threading

ROBOT_IP = "192.168.4.1"
WS_URL = f"ws://{ROBOT_IP}:81"

def on_message(ws, message):
    print(f"\n[WS RECV] {message}")

def on_error(ws, error):
    print(f"\n[WS ERROR] {error}")

def on_close(ws, close_status_code, close_msg):
    print("\n[WS CLOSED] Connection shut down")

def on_open(ws):
    print("\n[WS CONNECTED] Connected to Omni-Morph WebSockets!")
    print("Listening to live telemetry. Type a message below and press enter to send...")
    
    def run_input():
        while True:
            try:
                cmd = input()
                if cmd.lower() == 'exit':
                    ws.close()
                    break
                ws.send(cmd)
                print(f"[WS SENT] {cmd}")
            except Exception as e:
                print(f"Send error: {e}")
                break
                
    threading.Thread(target=run_input, daemon=True).start()

def main():
    print(f"Attempting WebSocket connection to: {WS_URL}")
    print("Ensure you are connected to the 'Remote-car' hotspot.")
    
    # Enable trace if you want detail
    # websocket.enableTrace(True)
    
    ws = websocket.WebSocketApp(WS_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("\nExiting WebSocket tester.")

if __name__ == "__main__":
    main()
